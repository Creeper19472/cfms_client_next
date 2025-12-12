# Version Management Script

This directory contains the automated version management script for CFMS Client NEXT.

## bump_version.py

Automates the version number update process across all necessary files.

### Features

- **Semantic Versioning**: Supports major, minor, and patch version bumps
- **Auto-date Stamping**: Automatically sets the MODIFIED date in YYYYMMDD format
- **Changelog Generation**: Creates properly formatted changelog entries
- **Git Integration**: Optional automatic commit and tag creation
- **Interactive Prompts**: Guides you through the release process
- **Validation**: Confirms changes before applying them

### Files Updated

1. `src/include/constants.py` - Updates `BUILD_VERSION` and `MODIFIED`
2. `pyproject.toml` - Updates the project version
3. `src/include/ui/controls/dialogs/CHANGELOG.md` - Adds new release entry

### Usage

#### Basic Usage with Interactive Prompts

```bash
# Bump patch version (0.2.37 -> 0.2.38)
python scripts/bump_version.py patch

# Bump minor version (0.2.37 -> 0.3.0)
python scripts/bump_version.py minor

# Bump major version (0.2.37 -> 1.0.0)
python scripts/bump_version.py major
```

The script will prompt you for:
- Release title
- Release description

#### Advanced Usage with Command-Line Arguments

```bash
# Bump version with title and auto-commit
python scripts/bump_version.py patch --title "Bug fixes" --commit

# Bump version and create git tag
python scripts/bump_version.py minor --title "New Features" --tag

# Full automation: bump, commit, and tag
python scripts/bump_version.py minor \
  --title "New Features Added" \
  --content "Added support for multiple file uploads and improved UI." \
  --commit --tag
```

### Options

- `--title TITLE`: Set the release title (skips prompt)
- `--content CONTENT`: Set the release description (skips prompt)
- `--commit`: Automatically commit the changes
- `--tag`: Create a git tag for the new version
- `--help`: Show help message

### Workflow

1. **Run the script** with your desired bump type
2. **Provide information** (if not using command-line args):
   - Release title
   - Release description
3. **Review summary** of all changes
4. **Confirm** to proceed
5. **Files are updated** automatically
6. **Optional**: Changes are committed and tagged

### Example Output

```
$ python scripts/bump_version.py patch --title "Bug fixes" --commit

Current version: 0.2.37
New version: 0.2.38
============================================================
SUMMARY OF CHANGES:
============================================================
Version: 0.2.37 -> 0.2.38
Modified Date: 20251213
Release Title: Bug fixes
Release Date: 2025-12-13

Description:
Fixed issues with file upload and improved error handling.
============================================================

Proceed with version bump? [y/N]: y

Updating files...
✓ Updated src/include/constants.py
✓ Updated pyproject.toml
✓ Updated src/include/ui/controls/dialogs/CHANGELOG.md

✓ Version bump completed successfully!

Committing changes...
✓ Changes committed: chore: bump version to v0.2.38

============================================================
NEXT STEPS:
============================================================
Push changes and tag:
   git push && git push origin v0.2.38
============================================================
```

### Best Practices

1. **Always review changes** before confirming
2. **Use meaningful titles** that describe the release
3. **Write clear descriptions** of what changed
4. **Create tags** for releases that will be deployed
5. **Commit and tag together** for release versions
6. **Test the build** after version bump

### Integration with CI/CD

The git tag created by this script can trigger the GitHub Actions workflow for building releases. When you push a tag matching `v*.*.*`, the workflow in `.github/workflows/desktop-and-mobile-builds.yml` will automatically:

1. Build Windows executable
2. Build Android APK
3. Create GitHub release
4. Upload build artifacts

### Troubleshooting

**Script can't find files:**
- Ensure you're running from the repository root or scripts directory
- Check that all required files exist

**Git operations fail:**
- Ensure you have git configured properly
- Check that you have uncommitted changes staged

**Version parsing error:**
- Ensure BUILD_VERSION in constants.py follows the format `v0.0.0`
