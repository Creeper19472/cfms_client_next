# CFMS Client NEXT

Based on Websockets, CFMS client (NEXT) is the next generation of 
the client program for this system dedicated to confidential 
document management, using the newest version of Flet framework.

## Run the app

### uv

Run as a desktop app:

```
uv run flet run
```

Run as a web app:

```
uv run flet run --web
```

### Poetry

Install dependencies from `pyproject.toml`:

```
poetry install
```

Run as a desktop app:

```
poetry run flet run
```

Run as a web app:

```
poetry run flet run --web
```

For more details on running the app, refer to the [Getting Started Guide](https://flet.dev/docs/getting-started/).

## Version Management

To update the application version number, use the automated version management script:

```bash
# Bump patch version (0.2.37 -> 0.2.38)
python scripts/bump_version.py patch

# Bump minor version with auto-commit and tag
python scripts/bump_version.py minor --title "New Features" --commit --tag

# Bump major version
python scripts/bump_version.py major --title "Breaking Changes" --commit --tag
```

This script automatically updates:
- `src/include/constants.py` (BUILD_VERSION and MODIFIED date)
- `pyproject.toml` (version)
- `src/include/ui/controls/dialogs/CHANGELOG.md` (release entry)

## Release Type Detection

The repository uses a channel-based system to determine if GitHub releases should be marked as pre-releases or normal releases. The release type is determined by the `CHANNEL` constant in `src/include/constants.py`:

- **STABLE**: Creates a normal release
- **ALPHA**: Creates a pre-release  
- **BETA**: Creates a pre-release

For more details, see [docs/RELEASE_TYPE_DETECTION.md](docs/RELEASE_TYPE_DETECTION.md).

## Build the app

### Android

```
flet build apk -v
```

For more details on building and signing `.apk` or `.aab`, refer to the [Android Packaging Guide](https://docs.flet.dev/publish/android/).

### iOS

```
flet build ipa -v
```

For more details on building and signing `.ipa`, refer to the [iOS Packaging Guide](https://docs.flet.dev/publish/ios/).

### macOS

```
flet build macos -v
```

For more details on building macOS package, refer to the [macOS Packaging Guide](https://docs.flet.dev/publish/macos/).

### Linux

```
flet build linux -v
```

For more details on building Linux package, refer to the [Linux Packaging Guide](https://docs.flet.dev/publish/linux/).

### Windows

```
flet build windows -v
```

For more details on building Windows package, refer to the [Windows Packaging Guide](https://docs.flet.dev/publish/windows/).