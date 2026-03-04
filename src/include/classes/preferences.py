from dataclasses import dataclass, field


@dataclass
class UserPreference:
    theme: str = "light"
    # e.g. {"files": []}
    favourites: dict[str, dict[str, str]] = field(
        default_factory=lambda: {"files": {}, "directories": {}}
    )
    use_external_storage: bool = False
    external_storage_path: str = ""
