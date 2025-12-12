"""
Changelog parser for reading CHANGELOG.md files.

This module provides functionality to parse markdown-formatted changelog files
and convert them into ChangelogEntry instances for use in the application.

Expected CHANGELOG.md Format:
----------------------------
# CFMS Client NEXT - Changelog

## v0.2.36
**Released on:** 2025-11-19

**Title:** Add to Favourites Button for Documents & Directories

This version adds an 'Add to Favourites' button for documents and directories.
A variety of bug fixes and performance improvements have also be implemented.

---

## v0.2.33
**Released on:** 2025-11-12

**Title:** User Management Context Menu Rewrite

Content describing the changes...

---

Usage:
------
    from include.util.changelog_parser import get_changelogs_from_file
    
    # Get all changelog entries
    changelogs = get_changelogs_from_file()
    
    # Access the latest entry
    latest = changelogs[0]
    print(f"{latest.version}: {latest.title}")
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List

from include.classes.changelog import ChangelogEntry


def parse_changelog(changelog_path: Path) -> List[ChangelogEntry]:
    """
    Parse a CHANGELOG.md file and convert it to a list of ChangelogEntry instances.
    
    Args:
        changelog_path: Path to the CHANGELOG.md file
        
    Returns:
        List of ChangelogEntry instances, ordered from newest to oldest
        
    Raises:
        FileNotFoundError: If the changelog file doesn't exist
        ValueError: If the changelog format is invalid
    """
    if not changelog_path.exists():
        raise FileNotFoundError(f"Changelog file not found: {changelog_path}")
    
    content = changelog_path.read_text(encoding='utf-8')
    entries = []
    
    # Split by version sections (## v...)
    # Pattern matches versions like: v0.2.36, v1.0.0, v1.0.0-beta, 0.2.36
    version_pattern = r'^## (v?[\d.]+(?:-[\w.]+)?)$'
    
    # Split content into sections
    lines = content.split('\n')
    current_version = None
    current_date = None
    current_title = None
    current_content_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for version header
        version_match = re.match(version_pattern, line)
        if version_match:
            # Save previous entry if exists
            if current_version is not None:
                # Validate that all required fields are present
                if current_title is None:
                    raise ValueError(
                        f"Missing title for version {current_version} in {changelog_path}"
                    )
                if current_date is None:
                    raise ValueError(
                        f"Missing date for version {current_version} in {changelog_path}"
                    )
                
                entry_content = '\n'.join(current_content_lines).strip()
                entries.append(
                    ChangelogEntry(
                        version=current_version,
                        title=current_title,
                        content=entry_content,
                        date=current_date
                    )
                )
            
            # Start new entry
            current_version = version_match.group(1)
            current_content_lines = []
            current_date = None
            current_title = None
            
            # Look for the date line (next non-empty line after version)
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith('**Released on:**'):
                    # Extract date from format: **Released on:** 2025-11-19
                    date_str = next_line.replace('**Released on:**', '').strip()
                    try:
                        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError as e:
                        raise ValueError(
                            f"Invalid date format '{date_str}' for version {current_version} in {changelog_path}. "
                            f"Expected format: YYYY-MM-DD"
                        ) from e
                    i += 1
                    break
                elif next_line:
                    # Skip any other lines until we find the date
                    i += 1
                else:
                    i += 1
            
            # Look for the title line
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith('**Title:**'):
                    # Extract title from format: **Title:** Some Title
                    current_title = next_line.replace('**Title:**', '').strip()
                    i += 1
                    break
                elif next_line:
                    i += 1
                else:
                    i += 1
            
            # Skip empty line after title
            if i < len(lines) and not lines[i].strip():
                i += 1
            
            continue
        
        # Check for separator (---)
        if line.startswith('---'):
            i += 1
            continue
        
        # Skip the document header and intro lines
        if line.startswith('#') and 'Changelog' in line:
            i += 1
            continue
        
        if not line or line.startswith('This document contains'):
            i += 1
            continue
        
        # Collect content lines for current version
        if current_version is not None:
            current_content_lines.append(lines[i])
        
        i += 1
    
    # Don't forget the last entry
    if current_version is not None:
        # Validate that all required fields are present for the last entry
        if current_title is None:
            raise ValueError(
                f"Missing title for version {current_version} in {changelog_path}"
            )
        if current_date is None:
            raise ValueError(
                f"Missing date for version {current_version} in {changelog_path}"
            )
        
        entry_content = '\n'.join(current_content_lines).strip()
        entries.append(
            ChangelogEntry(
                version=current_version,
                title=current_title,
                content=entry_content,
                date=current_date
            )
        )
    
    return entries


def get_changelogs_from_file() -> List[ChangelogEntry]:
    """
    Get changelog entries from the CHANGELOG.md file in the dialogs directory.
    
    Returns:
        List of ChangelogEntry instances, ordered from newest to oldest
    """
    # Get the path to the CHANGELOG.md file in the dialogs directory
    current_dir = Path(__file__).parent.parent / 'ui' / 'controls' / 'dialogs'
    changelog_path = current_dir / 'CHANGELOG.md'
    
    return parse_changelog(changelog_path)
