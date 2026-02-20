import os
import json
from typing import Optional
from include.classes.shared import AppShared
from include.classes.preferences import UserPreference
from include.constants import USER_PREFERENCES_PATH
from include.util.kdf import encrypt_config, decrypt_config, is_encrypted_config


def load_user_preference(username: str) -> UserPreference:
    pref_path = (
        f"{USER_PREFERENCES_PATH}/{AppShared().server_address_hash}_{username}.json"
    )

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
            return UserPreference(favourites={"files": {}, "directories": {}})
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
        favourites=data.get("favourites", {}),
    )


def save_user_preference(username: str, preferences: UserPreference) -> None:
    pref_path = (
        f"{USER_PREFERENCES_PATH}/{AppShared().server_address_hash}_{username}.json"
    )
    os.makedirs(os.path.dirname(pref_path), exist_ok=True)

    data = {
        "theme": preferences.theme,
        "favourites": preferences.favourites,
    }
    _write_pref_file(pref_path, data, AppShared().dek)


def _write_pref_file(path: str, data: dict, dek: Optional[bytes]) -> None:
    """Write *data* to *path*, encrypted when *dek* is provided."""
    plaintext = json.dumps(data, separators=(",", ":")).encode("utf-8")
    if dek is not None:
        with open(path, "wb") as f:
            f.write(encrypt_config(plaintext, dek))
    else:
        with open(path, "wb") as f:
            f.write(plaintext)
