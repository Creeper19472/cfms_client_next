#!/usr/bin/env python3
"""
Automated Version Management Script for CFMS Client NEXT

This script automates the version number update process across all necessary files:
- src/include/constants.py (BUILD_VERSION and MODIFIED)
- pyproject.toml (version)
- src/include/ui/controls/dialogs/CHANGELOG.md (new entry)

Usage:
    python scripts/bump_version.py [major|minor|patch] [--title "Release Title"] [--content "Description"] [--tag] [--commit]

Examples:
    # Bump patch version (0.2.37 -> 0.2.38) with interactive prompts
    python scripts/bump_version.py patch

    # Bump minor version with custom title and auto-commit
    python scripts/bump_version.py minor --title "New Features" --commit

    # Bump major version, create tag and commit
    python scripts/bump_version.py major --title "Breaking Changes" --tag --commit
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Tuple


class VersionBumper:
    """Handles version bumping across all project files."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.constants_file = repo_root / "src" / "include" / "constants.py"
        self.pyproject_file = repo_root / "pyproject.toml"
        self.changelog_file = (
            repo_root / "src" / "include" / "ui" / "controls" / "dialogs" / "CHANGELOG.md"
        )

    def get_current_version(self) -> str:
        """Extract current version from constants.py."""
        if not self.constants_file.exists():
            raise FileNotFoundError(f"Constants file not found: {self.constants_file}")

        content = self.constants_file.read_text(encoding="utf-8")
        match = re.search(r'BUILD_VERSION\s*=\s*"v([\d.]+)"', content)
        if not match:
            raise ValueError("Could not find BUILD_VERSION in constants.py")

        return match.group(1)

    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse semantic version string into (major, minor, patch) tuple."""
        parts = version.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")

        try:
            return int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            raise ValueError(f"Invalid version format: {version}")

    def bump_version(self, current: str, bump_type: str) -> str:
        """
        Bump version based on type.

        Args:
            current: Current version string (e.g., "0.2.37")
            bump_type: One of "major", "minor", or "patch"

        Returns:
            New version string
        """
        major, minor, patch = self.parse_version(current)

        if bump_type == "major":
            return f"{major + 1}.0.0"
        elif bump_type == "minor":
            return f"{major}.{minor + 1}.0"
        elif bump_type == "patch":
            return f"{major}.{minor}.{patch + 1}"
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

    def update_constants_file(self, new_version: str, modified_date: str) -> None:
        """Update BUILD_VERSION and MODIFIED in constants.py."""
        if not self.constants_file.exists():
            raise FileNotFoundError(f"Constants file not found: {self.constants_file}")

        content = self.constants_file.read_text(encoding="utf-8")

        # Update BUILD_VERSION
        content = re.sub(
            r'BUILD_VERSION\s*=\s*"v[\d.]+"',
            f'BUILD_VERSION = "v{new_version}"',
            content,
        )

        # Update MODIFIED
        content = re.sub(
            r'MODIFIED\s*=\s*"\d+"', f'MODIFIED = "{modified_date}"', content
        )

        self.constants_file.write_text(content, encoding="utf-8")
        print(f"✓ Updated {self.constants_file.relative_to(self.repo_root)}")

    def update_pyproject_file(self, new_version: str) -> None:
        """Update version in pyproject.toml."""
        if not self.pyproject_file.exists():
            raise FileNotFoundError(f"pyproject.toml not found: {self.pyproject_file}")

        content = self.pyproject_file.read_text(encoding="utf-8")

        # Update version in [project] section
        content = re.sub(
            r'version\s*=\s*"[\d.]+"', f'version = "{new_version}"', content, count=1
        )

        self.pyproject_file.write_text(content, encoding="utf-8")
        print(f"✓ Updated {self.pyproject_file.relative_to(self.repo_root)}")

    def update_changelog(self, new_version: str, release_date: date, title: str, content: str) -> None:
        """Add new entry to CHANGELOG.md."""
        if not self.changelog_file.exists():
            raise FileNotFoundError(f"CHANGELOG not found: {self.changelog_file}")

        changelog_content = self.changelog_file.read_text(encoding="utf-8")

        # Format new entry
        new_entry = f"""## v{new_version}
**Released on:** {release_date.strftime('%Y-%m-%d')}

**Title:** {title}

{content}

---

"""

        # Find position to insert (after the header section)
        # Look for the first version entry or the end of header
        lines = changelog_content.split("\n")
        insert_pos = 0

        for i, line in enumerate(lines):
            # Find the end of the header (after the --- separator following the intro)
            if line.strip() == "---" and i > 0:
                insert_pos = i + 1
                break

        # Insert the new entry
        lines.insert(insert_pos, "")
        lines.insert(insert_pos + 1, new_entry.rstrip())

        updated_content = "\n".join(lines)
        self.changelog_file.write_text(updated_content, encoding="utf-8")
        print(f"✓ Updated {self.changelog_file.relative_to(self.repo_root)}")

    def run(
        self,
        bump_type: str,
        title: str = "",
        content: str = "",
        create_tag: bool = False,
        commit: bool = False,
    ) -> None:
        """
        Execute version bump process.

        Args:
            bump_type: Type of version bump (major, minor, patch)
            title: Release title (prompted if not provided)
            content: Release description (prompted if not provided)
            create_tag: Whether to create git tag
            commit: Whether to commit changes
        """
        # Get current version
        current_version = self.get_current_version()
        print(f"Current version: {current_version}")

        # Calculate new version
        new_version = self.bump_version(current_version, bump_type)
        print(f"New version: {new_version}")

        # Get current date
        today = date.today()
        modified_date = today.strftime("%Y%m%d")

        # Get title and content if not provided
        if not title:
            title = input("Enter release title: ").strip()
            if not title:
                title = f"{bump_type.capitalize()} release"

        if not content:
            print("Enter release description (press Enter twice to finish):")
            content_lines = []
            while True:
                line = input()
                if not line and content_lines and not content_lines[-1]:
                    break
                content_lines.append(line)
            content = "\n".join(content_lines).strip()
            if not content:
                content = f"This version includes {bump_type} updates and improvements."

        # Confirm changes
        print("\n" + "=" * 60)
        print("SUMMARY OF CHANGES:")
        print("=" * 60)
        print(f"Version: {current_version} -> {new_version}")
        print(f"Modified Date: {modified_date}")
        print(f"Release Title: {title}")
        print(f"Release Date: {today.strftime('%Y-%m-%d')}")
        print(f"\nDescription:\n{content}")
        print("=" * 60)

        confirm = input("\nProceed with version bump? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            sys.exit(0)

        # Update files
        print("\nUpdating files...")
        self.update_constants_file(new_version, modified_date)
        self.update_pyproject_file(new_version)
        self.update_changelog(new_version, today, title, content)

        print("\n✓ Version bump completed successfully!")

        # Git operations
        if commit or create_tag:
            import subprocess

            try:
                # Stage changes
                files_to_commit = [
                    str(self.constants_file.relative_to(self.repo_root)),
                    str(self.pyproject_file.relative_to(self.repo_root)),
                    str(self.changelog_file.relative_to(self.repo_root)),
                ]

                if commit:
                    print("\nCommitting changes...")
                    subprocess.run(
                        ["git", "add"] + files_to_commit,
                        cwd=self.repo_root,
                        check=True,
                    )
                    commit_msg = f"chore: bump version to v{new_version}"
                    subprocess.run(
                        ["git", "commit", "-m", commit_msg],
                        cwd=self.repo_root,
                        check=True,
                    )
                    print(f"✓ Changes committed: {commit_msg}")

                if create_tag:
                    print("\nCreating git tag...")
                    tag_name = f"v{new_version}"
                    tag_msg = f"Release {tag_name}: {title}"
                    subprocess.run(
                        ["git", "tag", "-a", tag_name, "-m", tag_msg],
                        cwd=self.repo_root,
                        check=True,
                    )
                    print(f"✓ Created tag: {tag_name}")
                    print(f"  To push tag: git push origin {tag_name}")

            except subprocess.CalledProcessError as e:
                print(f"\n⚠ Git operation failed: {e}")
                sys.exit(1)

        # Print next steps
        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        if not commit:
            print("1. Review the changes")
            print("2. Commit the changes:")
            print(f"   git add {' '.join(f.relative_to(self.repo_root).as_posix() for f in [self.constants_file, self.pyproject_file, self.changelog_file])}")
            print(f"   git commit -m 'chore: bump version to v{new_version}'")
        if not create_tag:
            print(f"3. Create and push tag:")
            print(f"   git tag -a v{new_version} -m 'Release v{new_version}: {title}'")
            print(f"   git push origin v{new_version}")
        if create_tag and not commit:
            print(f"Push changes and tag:")
            print(f"   git push && git push origin v{new_version}")
        elif create_tag and commit:
            print(f"Push changes and tag:")
            print(f"   git push && git push origin v{new_version}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Automate version number updates for CFMS Client NEXT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Bump patch version with prompts
  python scripts/bump_version.py patch

  # Bump minor version with title and auto-commit
  python scripts/bump_version.py minor --title "New Features" --commit

  # Bump major version, create tag and commit
  python scripts/bump_version.py major --title "Breaking Changes" --tag --commit
        """,
    )

    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Type of version bump to perform",
    )
    parser.add_argument(
        "--title", default="", help="Release title (will prompt if not provided)"
    )
    parser.add_argument(
        "--content",
        default="",
        help="Release description (will prompt if not provided)",
    )
    parser.add_argument(
        "--tag", action="store_true", help="Create git tag for the new version"
    )
    parser.add_argument(
        "--commit", action="store_true", help="Commit changes automatically"
    )

    args = parser.parse_args()

    # Find repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    # Run version bumper
    bumper = VersionBumper(repo_root)
    bumper.run(
        bump_type=args.bump_type,
        title=args.title,
        content=args.content,
        create_tag=args.tag,
        commit=args.commit,
    )


if __name__ == "__main__":
    main()
