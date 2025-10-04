from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ChangelogEntry:
    version: str
    title: str
    content: str
    date: date  # e.g., "2024-06-01"