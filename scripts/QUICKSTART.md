# Quick Start Guide - Version Management

## One-Line Commands

```bash
# Patch version bump (0.2.37 → 0.2.38) - Interactive
python scripts/bump_version.py patch

# Minor version bump with title - Auto commit and tag
python scripts/bump_version.py minor --title "New Features" --commit --tag

# Major version bump - Full automation
python scripts/bump_version.py major --title "Breaking Changes" --content "Major refactoring" --commit --tag
```

## Common Workflows

### Regular Release
```bash
# 1. Bump version, commit, and tag
python scripts/bump_version.py patch --title "Bug fixes" --commit --tag

# 2. Push to remote
git push && git push origin v0.2.38
```

### Feature Release
```bash
# Bump minor version
python scripts/bump_version.py minor --title "New feature added" --commit --tag
git push && git push origin v0.3.0
```

### What Gets Updated

1. **src/include/constants.py**
   - `BUILD_VERSION = "v0.2.38"`
   - `MODIFIED = "20251212"`

2. **pyproject.toml**
   - `version = "0.2.38"`

3. **src/include/ui/controls/dialogs/CHANGELOG.md**
   - New entry at the top with release info

## Tips

- Use `--commit` to auto-commit changes
- Use `--tag` to create git tags (triggers CI/CD)
- Without flags, you can review changes before committing
- Title and content can be entered interactively if not provided

See [README.md](README.md) for complete documentation.
