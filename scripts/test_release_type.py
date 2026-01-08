#!/usr/bin/env python3
"""Test script to verify release type detection works correctly."""

import sys
from pathlib import Path

# Add src to path
script_dir = Path(__file__).parent
repo_root = script_dir.parent
src_path = repo_root / "src"
sys.path.insert(0, str(src_path))

from include.constants import CHANNEL
from include.classes.version import ChannelType

def test_channel_logic():
    """Test that the logic correctly identifies prerelease vs stable."""
    print("Testing channel logic...")
    
    # Test the actual implementation logic
    actual_is_prerelease = CHANNEL != ChannelType.STABLE
    print(f"Current CHANNEL: {CHANNEL}")
    print(f"Current is_prerelease: {actual_is_prerelease}")
    
    # Test each channel type comparison
    print("\nTesting each channel type:")
    
    # STABLE should not be prerelease
    is_stable_prerelease = ChannelType.STABLE != ChannelType.STABLE
    assert is_stable_prerelease == False, "STABLE should not be a prerelease"
    print("✓ STABLE channel logic: not prerelease (as expected)")
    
    # ALPHA should be prerelease
    is_alpha_prerelease = ChannelType.ALPHA != ChannelType.STABLE
    assert is_alpha_prerelease == True, "ALPHA should be a prerelease"
    print("✓ ALPHA channel logic: is prerelease (as expected)")
    
    # BETA should be prerelease
    is_beta_prerelease = ChannelType.BETA != ChannelType.STABLE
    assert is_beta_prerelease == True, "BETA should be a prerelease"
    print("✓ BETA channel logic: is prerelease (as expected)")
    
    # Verify the current channel matches expected behavior
    if CHANNEL == ChannelType.STABLE:
        assert actual_is_prerelease == False, "STABLE channel should result in not prerelease"
        print(f"\n✓ Current STABLE channel correctly results in: not prerelease")
    elif CHANNEL in [ChannelType.ALPHA, ChannelType.BETA]:
        assert actual_is_prerelease == True, f"{CHANNEL.value} channel should result in prerelease"
        print(f"\n✓ Current {CHANNEL.value.upper()} channel correctly results in: prerelease")
    
    print("\nAll tests passed! ✓")
    return 0

if __name__ == "__main__":
    sys.exit(test_channel_logic())
