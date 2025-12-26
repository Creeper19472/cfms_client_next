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
from typing import List, Tuple

from include.classes.changelog import ChangelogEntry


def _format_content_for_markdown(lines: List[str]) -> str:
    """
    Format content lines to preserve Markdown paragraph breaks and collapse
    "soft" line wraps (lines broken only for width) into single logical lines.

    Rules implemented:
    - Paragraphs are separated by one or more blank lines -> output paragraphs
      separated by a double newline ("\n\n").
    - Within a paragraph, consecutive non-empty lines are treated as the same
      paragraph and joined with single spaces (soft wraps collapsed).
    - Fenced code blocks (``` ... ```) and indented code blocks (lines starting
      with 4 spaces or a tab) are preserved verbatim (no collapsing).
    - Each list item (lines starting with -, *, + or digit.) is treated as its
      own paragraph so items remain on separate lines; wrapped lines that
      follow a list item and are not new list items are treated as continuation
      of that item and collapsed into it.
    """
    if not lines:
        return ""

    def is_fence(line: str) -> bool:
        return line.strip().startswith("```")

    def is_indented_code(line: str) -> bool:
        return line.startswith("    ") or line.startswith("\t")

    def is_list_item(line: str) -> bool:
        return re.match(r"^\s*([-*+]|[0-9]+[.])\s+", line) is not None

    paragraphs: List[Tuple[str, List[str]]] = (
        []
    )  # (type, lines) type: 'text'|'code'|'list'
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        # Blank line -> paragraph separator
        if line.strip() == "":
            i += 1
            # Ensure we don't add multiple adjacent separators: just continue to next
            # flushing happens when we encounter content
            # Represent separators by leaving a gap between appended paragraphs
            # (no action needed)
            continue

        # Fenced code block
        if is_fence(line):
            fence_lines = [line.rstrip("\n")]
            i += 1
            # collect until closing fence or EOF (include closing fence)
            while i < n:
                fence_lines.append(lines[i].rstrip("\n"))
                if is_fence(lines[i]):
                    i += 1
                    break
                i += 1
            paragraphs.append(("code", fence_lines))
            continue

        # Indented code block: collect consecutive indented lines
        if is_indented_code(line):
            code_lines = []
            while i < n and is_indented_code(lines[i]):
                code_lines.append(lines[i].rstrip("\n"))
                i += 1
            paragraphs.append(("code", code_lines))
            continue

        # List item handling: each list item becomes its own paragraph
        if is_list_item(line):
            item_lines = [line.strip()]
            i += 1
            # collect continuation lines that belong to this list item (non-empty,
            # non-list-item, non-fence, non-indented)
            while (
                i < n
                and lines[i].strip() != ""
                and not is_list_item(lines[i])
                and not is_fence(lines[i])
                and not is_indented_code(lines[i])
            ):
                item_lines.append(lines[i].strip())
                i += 1
            paragraphs.append(("list", item_lines))
            continue

        # Regular text paragraph: collect until blank line or special block
        text_lines = [line.strip()]
        i += 1
        while (
            i < n
            and lines[i].strip() != ""
            and not is_fence(lines[i])
            and not is_indented_code(lines[i])
            and not is_list_item(lines[i])
        ):
            text_lines.append(lines[i].strip())
            i += 1
        paragraphs.append(("text", text_lines))

    # Now build output: join paragraphs with double newlines.
    out_parts: List[str] = []
    for p_type, p_lines in paragraphs:
        if p_type == "code":
            # Preserve exact lines and their newlines
            out_parts.append("\n".join(p_lines).rstrip())
        elif p_type == "list":
            # Keep each list item on its own line; collapse soft wraps within the item
            # Items were collected per item, but p_lines may include surrounding content if needed
            # Join the collected lines for this single item with a single space
            out_parts.append(" ".join(p_lines).strip())
        else:  # 'text'
            # Collapse soft wraps into single lines: join with spaces, preserve paragraph text
            joined = " ".join(p_lines).strip()
            out_parts.append(joined)

    # Join paragraphs with blank line (Markdown paragraph separator)
    return "\n\n".join(out_parts).strip()


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

    content = changelog_path.read_text(encoding="utf-8")
    entries = []

    # Split by version sections (## v...)
    # Pattern matches versions like: v0.2.36, v1.0.0, v1.0.0-beta, 0.2.36
    version_pattern = r"^## (v?[\d.]+(?:-[\w.]+)?)$"

    # Split content into sections
    lines = content.split("\n")
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

                # Format content with proper Markdown paragraph breaks
                entry_content = _format_content_for_markdown(current_content_lines)
                entries.append(
                    ChangelogEntry(
                        version=current_version,
                        title=current_title,
                        content=entry_content,
                        date=current_date,
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
                if next_line.startswith("**Released on:**"):
                    # Extract date from format: **Released on:** 2025-11-19
                    date_str = next_line.replace("**Released on:**", "").strip()
                    try:
                        current_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError as e:
                        raise ValueError(
                            f"Invalid date format '{date_str}' for version {current_version} in {changelog_path}. "
                            f"Expected format: YYYY-MM-DD"
                        ) from e
                    i += 1
                    break
                i += 1

            # Look for the title line
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith("**Title:**"):
                    # Extract title from format: **Title:** Some Title
                    current_title = next_line.replace("**Title:**", "").strip()
                    i += 1
                    break
                i += 1

            # Skip empty line after title
            if i < len(lines) and not lines[i].strip():
                i += 1

            continue

        # Check for separator (---)
        if line.startswith("---"):
            i += 1
            continue

        # Skip the document header and intro lines
        if line.startswith("#") and "Changelog" in line:
            i += 1
            continue

        # Skip intro text only before we find any version
        if current_version is None and line.startswith("This document contains"):
            i += 1
            continue

        # Skip blank lines only before we find any version
        # Once we're in a version, blank lines are significant for paragraph breaks
        if current_version is None and not line:
            i += 1
            continue

        # Collect content lines for current version (including blank lines)
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

        # Format content with proper Markdown paragraph breaks
        entry_content = _format_content_for_markdown(current_content_lines)
        entries.append(
            ChangelogEntry(
                version=current_version,
                title=current_title,
                content=entry_content,
                date=current_date,
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
    current_dir = Path(__file__).parent.parent / "ui" / "controls" / "dialogs"
    changelog_path = current_dir / "CHANGELOG.md"

    return parse_changelog(changelog_path)
