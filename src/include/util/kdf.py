"""Key derivation and data encryption utilities for CFMS client configuration protection.

Design:
- The user's login password is used to derive a Key Encryption Key (KEK) via
  PBKDF2-HMAC-SHA256 (NIST SP 800-132, 1 000 000 iterations).
- A random 256-bit Data Encryption Key (DEK) is generated once per user and
  encrypted with the KEK using AES-256-GCM (authenticated encryption).
- The encrypted DEK is stored server-side as ``key_content`` inside the user's
  keyring so it is available after every login.
- Local configuration files (preferences, download task lists) are encrypted
  with the plain DEK using AES-256-GCM and a per-write random nonce.
"""

import base64
import binascii
import hashlib
import json
import os

from Crypto.Cipher import AES

__all__ = [
    "generate_dek",
    "encrypt_dek",
    "decrypt_dek",
    "encrypt_config",
    "decrypt_config",
    "is_encrypted_config",
]

# ──────────────────────── constants ────────────────────────────────────────────
# Magic header that identifies an encrypted config file produced by this module.
# Starts with non-ASCII bytes that are unlikely to appear in a plain JSON file.
_ENCRYPTED_MAGIC = b"\xcf\xe5\xce\x01"

_KDF_ITERATIONS: int = 1_000_000  # NIST SP 800-132 recommended minimum for PBKDF2-HMAC-SHA256
_SALT_SIZE: int = 16  # 128-bit salt for PBKDF2
_KEY_SIZE: int = 32  # AES-256
_NONCE_SIZE: int = 12  # 96-bit nonce (GCM recommended)
_TAG_SIZE: int = 16  # 128-bit GCM authentication tag


# ──────────────────────── low-level helpers ─────────────────────────────────────
def _derive_kek(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit Key Encryption Key from *password* using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _KDF_ITERATIONS,
        dklen=_KEY_SIZE,
    )


# ──────────────────────── DEK lifecycle ─────────────────────────────────────────
def generate_dek() -> bytes:
    """Return a new random 256-bit Data Encryption Key."""
    return os.urandom(_KEY_SIZE)


def encrypt_dek(dek: bytes, password: str) -> str:
    """Encrypt *dek* with a KEK derived from *password*.

    The returned string is compact JSON containing every parameter needed to
    later decrypt the DEK.  It is safe to store this string as the
    ``key_content`` field in the server's keyring.

    Args:
        dek:      The 32-byte Data Encryption Key to protect.
        password: The user's login password.

    Returns:
        JSON string with fields ``v``, ``kdf``, ``iter``, ``salt``, ``nonce``,
        ``tag``, and ``ct``.
    """
    salt = os.urandom(_SALT_SIZE)
    kek = _derive_kek(password, salt)
    nonce = os.urandom(_NONCE_SIZE)
    cipher = AES.new(kek, AES.MODE_GCM, nonce=nonce, mac_len=_TAG_SIZE)
    ct, tag = cipher.encrypt_and_digest(dek)
    payload = {
        "v": 1,
        "kdf": "pbkdf2_hmac_sha256",
        "iter": _KDF_ITERATIONS,
        "salt": base64.b64encode(salt).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "tag": base64.b64encode(tag).decode(),
        "ct": base64.b64encode(ct).decode(),
    }
    return json.dumps(payload, separators=(",", ":"))


def decrypt_dek(encrypted_dek_str: str, password: str) -> bytes:
    """Decrypt a DEK that was previously encrypted with :func:`encrypt_dek`.

    Args:
        encrypted_dek_str: JSON string produced by :func:`encrypt_dek`.
        password:          The user's login password.

    Returns:
        The original 32-byte DEK.

    Raises:
        ValueError: If the payload format is unsupported, a required field is
                    missing or malformed, the KDF is unknown, or authentication
                    fails (wrong password / corrupted data).
    """
    try:
        payload = json.loads(encrypted_dek_str)
    except json.JSONDecodeError as exc:
        raise ValueError("Encrypted DEK is not valid JSON") from exc

    if payload.get("v") != 1:
        raise ValueError(
            f"Unsupported encrypted DEK version: {payload.get('v')!r}"
        )

    try:
        kdf_name: str = payload["kdf"]
        iterations: int = int(payload["iter"])
        salt = base64.b64decode(payload["salt"])
        nonce = base64.b64decode(payload["nonce"])
        tag = base64.b64decode(payload["tag"])
        ct = base64.b64decode(payload["ct"])
    except (KeyError, TypeError, binascii.Error) as exc:
        raise ValueError(f"Malformed encrypted DEK payload: {exc}") from exc

    if kdf_name != "pbkdf2_hmac_sha256":
        raise ValueError(f"Unsupported KDF: {kdf_name!r}")
    if iterations <= 0:
        raise ValueError(f"Invalid iteration count: {iterations}")

    kek = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=_KEY_SIZE,
    )
    cipher = AES.new(kek, AES.MODE_GCM, nonce=nonce, mac_len=_TAG_SIZE)
    try:
        return cipher.decrypt_and_verify(ct, tag)
    except ValueError as exc:
        raise ValueError(
            "DEK decryption failed: incorrect password or corrupted data"
        ) from exc


# ──────────────────────── config file encryption ────────────────────────────────
def encrypt_config(data: bytes, dek: bytes) -> bytes:
    """Encrypt *data* with *dek* using AES-256-GCM.

    Binary output layout::

        magic (4) | nonce (12) | tag (16) | ciphertext (variable)

    Args:
        data: Plaintext bytes (e.g. JSON-encoded configuration).
        dek:  32-byte Data Encryption Key.

    Returns:
        Opaque bytes beginning with :data:`_ENCRYPTED_MAGIC`.
    """
    nonce = os.urandom(_NONCE_SIZE)
    cipher = AES.new(dek, AES.MODE_GCM, nonce=nonce, mac_len=_TAG_SIZE)
    ct, tag = cipher.encrypt_and_digest(data)
    return _ENCRYPTED_MAGIC + nonce + tag + ct


def decrypt_config(encrypted: bytes, dek: bytes) -> bytes:
    """Decrypt bytes that were produced by :func:`encrypt_config`.

    Args:
        encrypted: Encrypted bytes including the magic header.
        dek:       32-byte Data Encryption Key.

    Returns:
        Original plaintext bytes.

    Raises:
        ValueError: If the magic header is absent or authentication fails.
    """
    magic_len = len(_ENCRYPTED_MAGIC)
    if not encrypted.startswith(_ENCRYPTED_MAGIC):
        raise ValueError("Not a valid encrypted config file (magic mismatch)")

    offset = magic_len
    nonce = encrypted[offset : offset + _NONCE_SIZE]
    offset += _NONCE_SIZE
    tag = encrypted[offset : offset + _TAG_SIZE]
    offset += _TAG_SIZE
    ct = encrypted[offset:]

    cipher = AES.new(dek, AES.MODE_GCM, nonce=nonce, mac_len=_TAG_SIZE)
    try:
        return cipher.decrypt_and_verify(ct, tag)
    except ValueError as exc:
        raise ValueError(
            "Config decryption failed: wrong key or corrupted data"
        ) from exc


def is_encrypted_config(data: bytes) -> bool:
    """Return ``True`` if *data* looks like an encrypted config file."""
    return data.startswith(_ENCRYPTED_MAGIC)
