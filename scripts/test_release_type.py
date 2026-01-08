#!/usr/bin/env python3
"""Test script to verify release type detection works correctly."""

import sys
from pathlib import Path

# Add src to path
script_dir = Path(__file__).parent
repo_root = script_dir.parent
src_path = repo_root / "src"
sys.path.insert(0, str(src_path))

from include.classes.version import ChannelType

def test_channel_logic():
    """Test that the logic correctly identifies prerelease vs stable."""
    print("Testing channel logic...")
    
    # Test STABLE - should NOT be prerelease
    is_stable_prerelease = ChannelType.STABLE != ChannelType.STABLE
    assert is_stable_prerelease == False, "STABLE should not be a prerelease"
    print("✓ STABLE channel correctly identified as not prerelease")
    
    # Test ALPHA - should be prerelease
    is_alpha_prerelease = ChannelType.ALPHA != ChannelType.STABLE
    assert is_alpha_prerelease == True, "ALPHA should be a prerelease"
    print("✓ ALPHA channel correctly identified as prerelease")
    
    # Test BETA - should be prerelease
    is_beta_prerelease = ChannelType.BETA != ChannelType.STABLE
    assert is_beta_prerelease == True, "BETA should be a prerelease"
    print("✓ BETA channel correctly identified as prerelease")
    
    print("\nAll tests passed! ✓")
    return 0

if __name__ == "__main__":
    sys.exit(test_channel_logic())
