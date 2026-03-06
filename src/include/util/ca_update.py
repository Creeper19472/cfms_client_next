"""Utilities for checking and updating the local CA certificate store.

The certificate store is fetched from the GitHub repository referenced by
:data:`include.constants.CA_CERT_REPO`.  Only files whose extension is
``.pem`` or ``.crt`` are downloaded.  A per-file manifest
(:file:`.manifest.json`) is stored in the CA directory so that unchanged
certificates are never re-downloaded.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from include.constants import CA_CERT_API_URL

__all__ = [
    "CACertUpdateResult",
    "check_and_update_ca_certs",
]

logger = logging.getLogger(__name__)

# Only download files with these extensions from the remote repository.
_ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".pem", ".crt"})

# Name of the local manifest file that stores per-file git-blob SHAs.
_MANIFEST_FILENAME = ".manifest.json"


@dataclass
class CACertUpdateResult:
    """Summary of a CA certificate store update run."""

    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        """Return ``True`` if any certificate was added, updated, or removed."""
        return bool(self.added or self.updated or self.removed)

    def __str__(self) -> str:
        parts = []
        if self.added:
            parts.append(f"added {len(self.added)}")
        if self.updated:
            parts.append(f"updated {len(self.updated)}")
        if self.removed:
            parts.append(f"removed {len(self.removed)}")
        if self.unchanged:
            parts.append(f"unchanged {len(self.unchanged)}")
        if self.errors:
            parts.append(f"errors {len(self.errors)}")
        return ", ".join(parts) if parts else "no changes"


def _git_blob_sha(content: bytes) -> str:
    """Compute the git blob SHA-1 for *content*.

    Git stores file content as a blob object whose SHA-1 is computed over
    the header ``"blob {len}\\0"`` concatenated with the raw bytes.  This
    matches the ``sha`` field returned by the GitHub Contents API.
    """
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content).hexdigest()  # noqa: S324 – git protocol uses SHA-1


def _load_manifest(ca_dir: Path) -> dict[str, str]:
    """Load the stored git-blob SHA manifest from *ca_dir*.

    Returns an empty dict if the manifest does not exist or is corrupt.
    """
    manifest_path = ca_dir / _MANIFEST_FILENAME
    if not manifest_path.exists():
        return {}
    try:
        with manifest_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {}
        return {str(k): str(v) for k, v in data.items()}
    except Exception as exc:
        logger.warning("Could not read CA manifest: %s", exc)
        return {}


def _save_manifest(ca_dir: Path, manifest: dict[str, str]) -> None:
    """Persist *manifest* to *ca_dir*."""
    manifest_path = ca_dir / _MANIFEST_FILENAME
    try:
        with manifest_path.open("w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
    except Exception as exc:
        logger.warning("Could not write CA manifest: %s", exc)


def _fetch_remote_entries(timeout: int = 10) -> list[dict[str, Any]]:
    """Fetch the list of files in the remote CA repository via the GitHub API.

    Returns a list of GitHub Contents API file objects (dicts).

    Raises:
        requests.exceptions.RequestException: on network / HTTP errors.
    """
    resp = requests.get(CA_CERT_API_URL, timeout=timeout)
    resp.raise_for_status()
    entries: list[dict[str, Any]] = resp.json()
    if not isinstance(entries, list):
        raise ValueError(f"Unexpected GitHub API response format: {type(entries)}")
    return entries


def check_and_update_ca_certs(
    ca_dir: Path,
    *,
    timeout: int = 10,
) -> CACertUpdateResult:
    """Check the remote CA certificate repository and sync the local store.

    Algorithm
    ---------
    1. Fetch the directory listing from the GitHub Contents API.
    2. Load the local manifest (git-blob SHA per filename).
    3. For each remote file whose extension is in :data:`_ALLOWED_EXTENSIONS`:

       * If the filename is not in the manifest **or** the SHA has changed,
         download the file, verify its integrity against the expected git-blob
         SHA, write it to disk, and record the new SHA.
       * Otherwise mark it as unchanged.

    4. For each local certificate file *not* present in the remote listing,
       delete the file and remove it from the manifest.
    5. Persist the updated manifest.

    Parameters
    ----------
    ca_dir:
        Path to the local CA certificate directory.
    timeout:
        HTTP request timeout in seconds.

    Returns
    -------
    CACertUpdateResult
        Summary of the changes made.
    """
    result = CACertUpdateResult()

    ca_dir.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest(ca_dir)

    # --- fetch remote state ---------------------------------------------------
    try:
        remote_entries = _fetch_remote_entries(timeout=timeout)
    except Exception as exc:
        logger.error("Failed to fetch CA cert listing from GitHub: %s", exc)
        result.errors.append(f"Failed to fetch remote listing: {exc}")
        return result

    # Build a map of filename -> entry for easy lookup (files only, allowed ext)
    remote_files: dict[str, dict[str, Any]] = {}
    for entry in remote_entries:
        if entry.get("type") != "file":
            continue
        name: str = entry.get("name", "")
        ext = os.path.splitext(name)[1].lower()
        if ext not in _ALLOWED_EXTENSIONS:
            logger.debug("Skipping non-certificate file: %s", name)
            continue
        remote_files[name] = entry

    # --- add / update ---------------------------------------------------------
    for name, entry in remote_files.items():
        remote_sha: str = entry.get("sha", "")
        local_sha: str = manifest.get(name, "")

        if local_sha == remote_sha and (ca_dir / name).exists():
            result.unchanged.append(name)
            continue

        # Need to download the file
        download_url: str = entry.get("download_url", "")
        if not download_url:
            logger.warning("No download_url for %s, skipping", name)
            result.errors.append(f"No download_url for {name}")
            continue

        try:
            file_resp = requests.get(download_url, timeout=timeout)
            file_resp.raise_for_status()
        except Exception as exc:
            logger.error("Failed to download %s: %s", name, exc)
            result.errors.append(f"Failed to download {name}: {exc}")
            continue

        content = file_resp.content

        # Integrity check: verify the downloaded content matches the expected
        # git-blob SHA reported by the GitHub API.
        actual_sha = _git_blob_sha(content)
        if actual_sha != remote_sha:
            logger.error(
                "SHA mismatch for %s: expected %s, got %s – skipping",
                name,
                remote_sha,
                actual_sha,
            )
            result.errors.append(f"Integrity check failed for {name}")
            continue

        dest = ca_dir / name
        try:
            dest.write_bytes(content)
        except Exception as exc:
            logger.error("Failed to write %s: %s", dest, exc)
            result.errors.append(f"Failed to write {name}: {exc}")
            continue

        if local_sha:
            result.updated.append(name)
            logger.info("Updated CA certificate: %s", name)
        else:
            result.added.append(name)
            logger.info("Added CA certificate: %s", name)

        manifest[name] = remote_sha

    # --- remove ---------------------------------------------------------------
    local_cert_files: set[str] = {
        p.name
        for p in ca_dir.iterdir()
        if p.is_file() and os.path.splitext(p.name)[1].lower() in _ALLOWED_EXTENSIONS
    }
    for name in local_cert_files - set(remote_files):
        try:
            (ca_dir / name).unlink()
            manifest.pop(name, None)
            result.removed.append(name)
            logger.info("Removed CA certificate: %s", name)
        except Exception as exc:
            logger.error("Failed to remove %s: %s", name, exc)
            result.errors.append(f"Failed to remove {name}: {exc}")

    _save_manifest(ca_dir, manifest)

    logger.info(
        "CA cert store update complete: %s",
        result,
    )
    return result

