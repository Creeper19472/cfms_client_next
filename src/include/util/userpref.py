import os
import json
from include.classes.config import AppShared
from include.classes.preferences import UserPreference
from include.constants import USER_PREFERENCES_PATH


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
