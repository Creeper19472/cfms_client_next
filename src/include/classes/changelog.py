"""Changelog data models for version tracking."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ChangelogEntry:
    """
    Represents a single changelog entry for a version release.
    
    Attributes:
        version: Version string (e.g., "1.0.0")
        title: Brief title of the release
        content: Detailed description of changes
        date: Release date
    """
    version: str
    title: str
    content: str
    date: date