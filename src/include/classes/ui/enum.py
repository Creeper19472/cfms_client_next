"""UI enumeration types for sorting and display options."""

from enum import Enum

__all__ = ["SortMode", "SortOrder"]


class SortMode(Enum):
    """Defines how files/items should be sorted."""
    BY_NAME = 0
    BY_CREATED_AT = 1
    BY_LAST_MODIFIED = 2
    BY_SIZE = 3
    BY_TYPE = 4


class SortOrder(Enum):
    """Defines the order direction for sorting."""
    ASCENDING = 0
    DESCENDING = 1