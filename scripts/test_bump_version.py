#!/usr/bin/env python3
"""
Test script for bump_version.py

This script validates the version bumper functionality without modifying actual files.
"""

import sys
import tempfile
from pathlib import Path
from datetime import date

# Add parent directory to path to import bump_version
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.bump_version import VersionBumper


def create_test_files(temp_dir: Path) -> tuple[Path, Path, Path]:
    """Create temporary test files with sample content."""
    
    # Create directory structure
    src_dir = temp_dir / "src" / "include"
    src_dir.mkdir(parents=True)
    
    ui_dir = temp_dir / "src" / "include" / "ui" / "controls" / "dialogs"
    ui_dir.mkdir(parents=True)
    
    # Create constants.py
    constants_file = src_dir / "constants.py"
    constants_file.write_text("""# Constants file
BUILD_VERSION = "v0.2.37"
MODIFIED = "20251212"
APP_VERSION = f"{BUILD_VERSION[1:]}.{MODIFIED}_alpha NEXT"
""")
    
    # Create pyproject.toml
    pyproject_file = temp_dir / "pyproject.toml"
    pyproject_file.write_text("""[project]
name = "cfms-client-next"
version = "0.2.37"
description = "Test"
""")
    
    # Create CHANGELOG.md
    changelog_file = ui_dir / "CHANGELOG.md"
    changelog_file.write_text("""# CFMS Client NEXT - Changelog

This document contains the release history.

---

## v0.2.37
**Released on:** 2025-12-12

**Title:** Test Release

This is a test release.

---
""")
    
    return constants_file, pyproject_file, changelog_file


def test_get_current_version():
    """Test version extraction."""
    print("Testing get_current_version...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        constants_file, _, _ = create_test_files(temp_path)
        
        bumper = VersionBumper(temp_path)
        version = bumper.get_current_version()
        
        assert version == "0.2.37", f"Expected 0.2.37, got {version}"
        print("✓ get_current_version works correctly")


def test_version_bumping():
    """Test version bump logic."""
    print("\nTesting version bumping logic...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        create_test_files(temp_path)
        
        bumper = VersionBumper(temp_path)
        
        # Test patch bump
        new_version = bumper.bump_version("0.2.37", "patch")
        assert new_version == "0.2.38", f"Patch bump failed: {new_version}"
        print("✓ Patch version bump works")
        
        # Test minor bump
        new_version = bumper.bump_version("0.2.37", "minor")
        assert new_version == "0.3.0", f"Minor bump failed: {new_version}"
        print("✓ Minor version bump works")
        
        # Test major bump
        new_version = bumper.bump_version("0.2.37", "major")
        assert new_version == "1.0.0", f"Major bump failed: {new_version}"
        print("✓ Major version bump works")


def test_update_constants_file():
    """Test constants.py update."""
    print("\nTesting constants.py update...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        constants_file, _, _ = create_test_files(temp_path)
        
        bumper = VersionBumper(temp_path)
        bumper.update_constants_file("0.2.38", "20251213")
        
        # Verify updates
        content = constants_file.read_text()
        assert 'BUILD_VERSION = "v0.2.38"' in content
        assert 'MODIFIED = "20251213"' in content
        print("✓ constants.py update works")


def test_update_pyproject_file():
    """Test pyproject.toml update."""
    print("\nTesting pyproject.toml update...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        _, pyproject_file, _ = create_test_files(temp_path)
        
        bumper = VersionBumper(temp_path)
        bumper.update_pyproject_file("0.2.38")
        
        # Verify update
        content = pyproject_file.read_text()
        assert 'version = "0.2.38"' in content
        print("✓ pyproject.toml update works")


def test_update_changelog():
    """Test CHANGELOG.md update."""
    print("\nTesting CHANGELOG.md update...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        _, _, changelog_file = create_test_files(temp_path)
        
        bumper = VersionBumper(temp_path)
        today = date.today()
        bumper.update_changelog(
            "0.2.38",
            today,
            "Test Update",
            "This is a test update."
        )
        
        # Verify update
        content = changelog_file.read_text()
        assert "## v0.2.38" in content
        assert f"**Released on:** {today.strftime('%Y-%m-%d')}" in content
        assert "**Title:** Test Update" in content
        assert "This is a test update." in content
        
        # Verify order (new entry should come before old one)
        v38_pos = content.find("## v0.2.38")
        v37_pos = content.find("## v0.2.37")
        assert v38_pos < v37_pos, "New entry should appear before old entry"
        
        print("✓ CHANGELOG.md update works")


def test_full_integration():
    """Test complete version bump process."""
    print("\nTesting full integration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        constants_file, pyproject_file, changelog_file = create_test_files(temp_path)
        
        bumper = VersionBumper(temp_path)
        
        # Simulate full update
        current_version = bumper.get_current_version()
        new_version = bumper.bump_version(current_version, "patch")
        today = date.today()
        modified_date = today.strftime("%Y%m%d")
        
        bumper.update_constants_file(new_version, modified_date)
        bumper.update_pyproject_file(new_version)
        bumper.update_changelog(new_version, today, "Integration Test", "Testing full flow")
        
        # Verify all files
        constants_content = constants_file.read_text()
        pyproject_content = pyproject_file.read_text()
        changelog_content = changelog_file.read_text()
        
        assert f'BUILD_VERSION = "v{new_version}"' in constants_content
        assert f'MODIFIED = "{modified_date}"' in constants_content
        assert f'version = "{new_version}"' in pyproject_content
        assert f"## v{new_version}" in changelog_content
        
        print("✓ Full integration test passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running bump_version.py tests")
    print("=" * 60)
    
    try:
        test_get_current_version()
        test_version_bumping()
        test_update_constants_file()
        test_update_pyproject_file()
        test_update_changelog()
        test_full_integration()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
