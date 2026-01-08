#!/usr/bin/env python3
"""Script to determine if the current version is a prerelease based on CHANNEL constant."""

import sys
from pathlib import Path

# Add src to path to import constants
script_dir = Path(__file__).parent
repo_root = script_dir.parent
src_path = repo_root / "src"
sys.path.insert(0, str(src_path))

from include.constants import CHANNEL
from include.classes.version import ChannelType

def main():
    """Determine if the current version is a prerelease."""
    is_prerelease = CHANNEL != ChannelType.STABLE
    
    # Output in a format that GitHub Actions can use
    print(f"{str(is_prerelease).lower()}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
