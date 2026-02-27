#!/usr/bin/env python3
"""Script to extract changelog notes for the given version tag from CHANGELOG.md."""

import os
import sys
import uuid
from pathlib import Path


def get_changelog_notes(version_tag: str) -> str | None:
    """
    Extract the changelog notes for the given version tag.

    Expected CHANGELOG.md format:
        ## vX.Y.Z
        **Released on:** YYYY-MM-DD
        ...content...
        ---
        ## vX.Y.Z-1
        ...

    Each version section begins with an exact '## <version_tag>' heading and
    ends at the next '---' horizontal rule (or end of file).

    Args:
        version_tag: The version tag to look up (e.g., "v0.6.9").

    Returns:
        The changelog notes as a string, or None if not found.
    """
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    changelog_path = (
        repo_root / "src" / "include" / "ui" / "controls" / "dialogs" / "CHANGELOG.md"
    )

    if not changelog_path.exists():
        return None

    content = changelog_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    notes_lines = []
    in_section = False

    for line in lines:
        stripped = line.strip()
        if stripped == f"## {version_tag}":
            in_section = True
            continue
        elif in_section:
            if stripped == "---":
                break
            notes_lines.append(line)

    if not notes_lines:
        return None

    return "\n".join(notes_lines).strip()


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: get_changelog_notes.py <version_tag>", file=sys.stderr)
        return 1

    version_tag = sys.argv[1]
    notes = get_changelog_notes(version_tag)

    if notes is None:
        # No changelog for this version; maintain current behavior.
        return 0

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        delimiter = f"CHANGELOG_NOTES_EOF_{uuid.uuid4().hex}"
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"changelog_notes<<{delimiter}\n")
            f.write(notes)
            f.write(f"\n{delimiter}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
