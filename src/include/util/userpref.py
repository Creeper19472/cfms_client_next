import os
import json
import asyncio
from include.classes.config import AppShared
from include.classes.preferences import UserPreference
from include.constants import USER_PREFERENCES_PATH


# Global list of callbacks to be called when favorites change
_favorites_change_callbacks = []


def register_favorites_change_callback(callback):
    """Register a callback to be called when favorites change."""
    if callback not in _favorites_change_callbacks:
        _favorites_change_callbacks.append(callback)


def unregister_favorites_change_callback(callback):
    """Unregister a callback."""
    if callback in _favorites_change_callbacks:
        _favorites_change_callbacks.remove(callback)


# TODO: Implement encryption for stored preferences
def load_user_preference(username: str) -> UserPreference:
    pref_path = (
        f"{USER_PREFERENCES_PATH}/{AppShared().server_address_hash}_{username}.json"
    )

    if not os.path.exists(pref_path):
        return UserPreference(favourites={"files": {}, "directories": {}})

    with open(pref_path, "r", encoding="utf-8") as file:
        data: dict = json.load(file)
        return UserPreference(
            theme=data.get("theme", "light"),
            favourites=data.get("favourites", []),
        )


def save_user_preference(username: str, preferences: UserPreference) -> None:
    pref_path = (
        f"{USER_PREFERENCES_PATH}/{AppShared().server_address_hash}_{username}.json"
    )
    os.makedirs(os.path.dirname(pref_path), exist_ok=True)

    with open(pref_path, "w", encoding="utf-8") as file:
        json.dump(
            {
                "theme": preferences.theme,
                "favourites": preferences.favourites,
            },
            file,
            # indent=4,
        )
    
    # Notify all registered callbacks that favorites have changed
    for callback in _favorites_change_callbacks:
        try:
            if asyncio.iscoroutinefunction(callback):
                # Schedule async callbacks
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(callback())
                except RuntimeError:
                    pass  # No event loop running
            else:
                callback()
        except Exception:
            pass  # Silently ignore callback errors

