from datetime import date

from dataclasses import dataclass



@dataclass(frozen=True)
class ChangelogEntry:
    version: str
    title: str
    content: str
    date: date  # e.g., "2024-06-01"