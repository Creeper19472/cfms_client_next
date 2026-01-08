#!/usr/bin/env python3
"""Script to get the channel name from the CHANNEL constant."""

import sys
from pathlib import Path

# Add src to path to import constants
script_dir = Path(__file__).parent
repo_root = script_dir.parent
src_path = repo_root / "src"
sys.path.insert(0, str(src_path))

from include.constants import CHANNEL

def main():
    """Output the channel name."""
    # Output the channel value (alpha, beta, or stable)
    print(CHANNEL.value)
    return 0

if __name__ == "__main__":
    sys.exit(main())
