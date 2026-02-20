import os
import json
from typing import Optional
from include.classes.shared import AppShared
from include.classes.preferences import UserPreference
from include.classes.exceptions.config import CorruptedEncryptedConfigError
from include.constants import USER_PREFERENCES_PATH
from include.util.kdf import encrypt_config, decrypt_config, is_encrypted_config


def get_user_preference_path(username: str) -> str:
    """Return the filesystem path for *username*'s preference file."""
    return f"{USER_PREFERENCES_PATH}/{AppShared().server_address_hash}_{username}.json"


def load_user_preference(username: str) -> UserPreference:
    pref_path = get_user_preference_path(username)

    if not os.path.exists(pref_path):
        return UserPreference(favourites={"files": {}, "directories": {}})

    dek = AppShared().dek

    with open(pref_path, "rb") as file:
        raw = file.read()

    if is_encrypted_config(raw):
        if dek is None:
            return UserPreference(favourites={"files": {}, "directories": {}})
        try:
            plaintext = decrypt_config(raw, dek)
            data: dict = json.loads(plaintext.decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            # DEK is present but decryption failed — the file was encrypted
            # with a different (old) DEK, e.g. after a server reset.
            raise CorruptedEncryptedConfigError(pref_path)
    else:
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return UserPreference(favourites={"files": {}, "directories": {}})
        # Migrate plain-JSON file to encrypted format when DEK is available
        if dek is not None:
            _write_pref_file(pref_path, data, dek)

    return UserPreference(
        theme=data.get("theme", "light"),
        favourites=_normalize_favourites(data.get("favourites")),
    )


def save_user_preference(username: str, preferences: UserPreference) -> None:
    pref_path = get_user_preference_path(username)
    os.makedirs(os.path.dirname(pref_path), exist_ok=True)

    data = {
        "theme": preferences.theme,
        "favourites": preferences.favourites,
    }
    _write_pref_file(pref_path, data, AppShared().dek)


def _normalize_favourites(raw) -> dict:
    """Return a favourites dict that always contains ``files`` and ``directories`` keys."""
    if not isinstance(raw, dict):
        return {"files": {}, "directories": {}}
    return {
        "files": raw.get("files", {}) if isinstance(raw.get("files"), dict) else {},
        "directories": raw.get("directories", {}) if isinstance(raw.get("directories"), dict) else {},
    }


def _write_pref_file(path: str, data: dict, dek: Optional[bytes]) -> None:
    """Write *data* to *path*, encrypted when *dek* is provided.

    When *dek* is ``None``, plaintext is written only if the existing file is
    not already encrypted.  If an encrypted file exists but no DEK is available,
    the file is left unchanged to prevent data loss and a security downgrade.
    """
    plaintext = json.dumps(data, separators=(",", ":")).encode("utf-8")
    if dek is not None:
        with open(path, "wb") as f:
            f.write(encrypt_config(plaintext, dek))
    else:
        # Do not overwrite an existing encrypted file when no DEK is available.
        if os.path.exists(path):
            try:
                with open(path, "rb") as existing_file:
                    if is_encrypted_config(existing_file.read()):
                        return
            except OSError:
                return
        with open(path, "wb") as f:
            f.write(plaintext)
