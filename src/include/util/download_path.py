"""Utilities for resolving download storage paths."""

import os

from include.classes.shared import AppShared
from include.constants import FLET_APP_STORAGE_DATA


def get_download_root_path() -> str:
    """Return the root directory for downloaded files.

    Uses user external storage preferences when enabled and valid.
    Falls back to the app internal downloads directory otherwise.
    """
    internal_path = f"{FLET_APP_STORAGE_DATA}/downloads"

    user_pref = AppShared().user_perference
    if user_pref and user_pref.use_external_storage:
        external_path = (user_pref.external_storage_path or "").strip()
        if external_path:
            try:
                os.makedirs(external_path, exist_ok=True)
                return external_path
            except OSError:
                pass

    os.makedirs(internal_path, exist_ok=True)
    return internal_path


def get_download_file_path(filename: str) -> str:
    """Return a full filesystem path for a download filename."""
    return os.path.join(get_download_root_path(), filename)
