#!/usr/bin/env python3
"""
Remove Pillow Dependency Script for Mobile Builds

This script removes the "pillow" dependency from pyproject.toml for mobile builds.
The pillow library is not needed for Android/mobile builds and can cause issues
during the APK build process.

Usage:
    python scripts/remove_pillow_dependency.py
"""

import sys
from pathlib import Path


def remove_pillow_from_pyproject(pyproject_path: Path) -> bool:
    """
    Remove pillow dependency from pyproject.toml.
    
    Args:
        pyproject_path: Path to pyproject.toml file
        
    Returns:
        True if pillow was found and removed, False otherwise
    """
    if not pyproject_path.exists():
        print(f"Error: pyproject.toml not found at {pyproject_path}", file=sys.stderr)
        return False
    
    content = pyproject_path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    
    new_lines = []
    pillow_removed = False
    in_dependencies = False
    
    for line in lines:
        stripped = line.strip()
        
        # Track if we're in the dependencies section
        # Handle both "dependencies = [" and "dependencies=[" formats
        if "dependencies" in stripped and "[" in stripped and "=" in stripped:
            in_dependencies = True
            new_lines.append(line)
            continue
        elif in_dependencies and stripped.startswith("]"):
            in_dependencies = False
            new_lines.append(line)
            continue
        
        # Remove pillow dependency line
        # Handle different quote styles and with/without trailing comma
        if in_dependencies:
            # Check if line contains pillow (case-insensitive, flexible quotes)
            lower_stripped = stripped.lower()
            if (lower_stripped == '"pillow",' or 
                lower_stripped == '"pillow"' or
                lower_stripped == "'pillow'," or
                lower_stripped == "'pillow'"):
                pillow_removed = True
                print(f"Removing line: {stripped}")
                continue
        
        new_lines.append(line)
    
    if pillow_removed:
        pyproject_path.write_text("".join(new_lines), encoding="utf-8")
        print(f"✓ Successfully removed pillow dependency from {pyproject_path.name}")
        return True
    else:
        print(f"⚠ Warning: pillow dependency not found in {pyproject_path.name}")
        return False


def main():
    """Main entry point."""
    # Find repository root (script is in scripts/ subdirectory)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    pyproject_path = repo_root / "pyproject.toml"
    
    print("=" * 60)
    print("Removing pillow dependency for mobile build")
    print("=" * 60)
    
    success = remove_pillow_from_pyproject(pyproject_path)
    
    if success:
        print("=" * 60)
        print("✓ Pillow dependency removed successfully")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("⚠ Pillow dependency was not found or could not be removed")
        print("=" * 60)
        sys.exit(0)  # Exit with 0 even if not found (it's okay if already removed)


if __name__ == "__main__":
    main()
