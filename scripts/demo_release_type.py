#!/usr/bin/env python3
"""Demonstration of how the release type detection works with different channels."""

import sys
from pathlib import Path

# Add src to path
script_dir = Path(__file__).parent
repo_root = script_dir.parent
src_path = repo_root / "src"
sys.path.insert(0, str(src_path))

from include.constants import CHANNEL
from include.classes.version import ChannelType

def main():
    """Demonstrate the current release type detection."""
    print("=" * 60)
    print("Release Type Detection Demonstration")
    print("=" * 60)
    print()
    
    # Show current configuration
    print(f"Current CHANNEL setting: {CHANNEL}")
    print(f"Current CHANNEL value: {CHANNEL.value}")
    print()
    
    # Determine release type
    is_prerelease = CHANNEL != ChannelType.STABLE
    
    print("Release Classification:")
    print(f"  Is Prerelease? {is_prerelease}")
    print(f"  GitHub Actions output: '{str(is_prerelease).lower()}'")
    print()
    
    # Show what would happen for each channel type
    print("Behavior for each channel type:")
    print("-" * 60)
    
    for channel_type in [ChannelType.STABLE, ChannelType.ALPHA, ChannelType.BETA]:
        is_pre = channel_type != ChannelType.STABLE
        release_type = "Pre-release" if is_pre else "Normal Release"
        print(f"  {channel_type.value.upper():8} → {release_type:15} (prerelease={str(is_pre).lower()})")
    
    print()
    print("=" * 60)
    print(f"✓ Current setting will create: {'Pre-release' if is_prerelease else 'Normal Release'}")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
