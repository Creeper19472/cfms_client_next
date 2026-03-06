"""Utilities for checking and updating the local CA certificate store.

The certificate store is fetched from the GitHub repository referenced by
:data:`include.constants.CA_CERT_REPO`.  Certificate files use the OpenSSL
``c_rehash`` naming convention (``{8-hex-chars}.{n}``) and therefore do NOT
carry a ``.pem`` / ``.crt`` extension.  All non-hidden files (files whose
name does not start with ``.``) are treated as certificate files.

A per-file manifest (:file:`.manifest.json`) is stored in the CA directory
so that unchanged certificates are never re-downloaded.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

from include.constants import CA_CERT_API_URL

__all__ = [
    "CACertUpdateResult",
    "build_initial_manifest",
    "check_and_update_ca_certs",
    "has_expired_certificates",
    "load_last_check_time",
    "manifest_exists",
    "save_last_check_time",
]

logger = logging.getLogger(__name__)

# Name of the local manifest file that stores per-file git-blob SHAs.
_MANIFEST_FILENAME = ".manifest.json"

# Name of the file that persists the Unix timestamp of the last successful check.
_LAST_CHECK_FILENAME = ".last_check"


def _is_cert_file(name: str) -> bool:
    """Return ``True`` for files that should be managed in the CA directory.

    Accepts any non-empty filename that does not start with ``'.'`` so that
    OpenSSL ``c_rehash`` hash-number files (e.g. ``a1b2c3d4.0``) are
    included alongside traditional ``.pem``/``.crt`` names.  Hidden helper
    files such as :file:`.manifest.json` and :file:`.last_check` are
    excluded.
    """
    return bool(name) and not name.startswith(".")


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


def load_last_check_time(ca_dir: Path) -> Optional[float]:
    """Return the Unix timestamp of the last successful CA cert check, or
    ``None`` if no check has been recorded yet.

    The timestamp is persisted to :file:`.last_check` in *ca_dir* so it
    survives application restarts.
    """
    check_path = ca_dir / _LAST_CHECK_FILENAME
    if not check_path.exists():
        return None
    try:
        return float(check_path.read_text(encoding="utf-8").strip())
    except Exception as exc:
        logger.warning("Could not read last-check timestamp: %s", exc)
        return None


def save_last_check_time(ca_dir: Path, timestamp: float) -> None:
    """Persist *timestamp* (Unix time) as the last successful CA cert check."""
    check_path = ca_dir / _LAST_CHECK_FILENAME
    try:
        check_path.write_text(str(timestamp), encoding="utf-8")
    except Exception as exc:
        logger.warning("Could not write last-check timestamp: %s", exc)


def manifest_exists(ca_dir: Path) -> bool:
    """Return ``True`` if the CA certificate manifest already exists in *ca_dir*.

    This is used at application startup to decide whether to run the
    first-time initialisation wizard.
    """
    return (ca_dir / _MANIFEST_FILENAME).exists()


def build_initial_manifest(ca_dir: Path) -> dict[str, str]:
    """Build and persist the initial CA certificate manifest from local files.

    Scans *ca_dir* for all non-hidden files (OpenSSL hash-number names such
    as ``a1b2c3d4.0`` as well as any ``.pem``/``.crt`` files), computes their
    git-blob SHAs, saves a :file:`.manifest.json`, and records the current
    time as the last-check timestamp (so the 90-day periodic check clock
    starts from the moment of first installation).

    Parameters
    ----------
    ca_dir:
        Path to the local CA certificate directory.

    Returns
    -------
    dict[str, str]
        Mapping of ``filename → git-blob SHA`` for every file that was found.
    """
    ca_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, str] = {}
    for cert_file in ca_dir.iterdir():
        if not cert_file.is_file() or not _is_cert_file(cert_file.name):
            continue
        try:
            content = cert_file.read_bytes()
            manifest[cert_file.name] = _git_blob_sha(content)
            logger.debug("Manifest: recorded %s", cert_file.name)
        except Exception as exc:
            logger.warning("Could not read %s for manifest: %s", cert_file.name, exc)

    _save_manifest(ca_dir, manifest)
    # Start the 90-day periodic-check clock from now.
    save_last_check_time(ca_dir, time.time())
    logger.info("Initial CA cert manifest built: %d file(s)", len(manifest))
    return manifest


def has_expired_certificates(ca_dir: Path) -> bool:
    """Return ``True`` if any certificate file in *ca_dir* has expired.

    Uses :mod:`cryptography.x509` to parse each non-hidden file as a PEM
    certificate and compares its *Not After* field against the current UTC
    time.  Files that cannot be parsed are silently skipped (they are not
    considered expired).

    Parameters
    ----------
    ca_dir:
        Path to the local CA certificate directory.
    """
    try:
        from cryptography import x509 as _x509
    except ImportError:
        logger.debug("cryptography not available; skipping certificate expiry check")
        return False

    if not ca_dir.is_dir():
        return False

    now = datetime.now(tz=timezone.utc)
    for cert_file in ca_dir.iterdir():
        if not cert_file.is_file() or not _is_cert_file(cert_file.name):
            continue
        try:
            cert = _x509.load_pem_x509_certificate(cert_file.read_bytes())
            if cert.not_valid_after_utc < now:
                logger.warning(
                    "CA certificate has expired: %s (expired %s)",
                    cert_file.name,
                    cert.not_valid_after_utc.isoformat(),
                )
                return True
        except Exception as exc:
            logger.debug("Could not parse certificate %s: %s", cert_file.name, exc)
    return False


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
    3. For each remote non-hidden file:

       * If the filename is not in the manifest **or** the SHA has changed,
         download the file, verify its integrity against the expected git-blob
         SHA, write it to disk, and record the new SHA.
       * Otherwise mark it as unchanged.

    4. For each local non-hidden file *not* present in the remote listing,
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

    # Build a map of filename → entry for easy lookup (non-hidden files only).
    remote_files: dict[str, dict[str, Any]] = {}
    for entry in remote_entries:
        if entry.get("type") != "file":
            continue
        name: str = entry.get("name", "")
        if not _is_cert_file(name):
            logger.debug("Skipping hidden/non-certificate file: %s", name)
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
        if p.is_file() and _is_cert_file(p.name)
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


