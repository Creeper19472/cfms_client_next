# Release Type Detection

This repository uses a channel-based system to determine whether GitHub releases should be marked as pre-releases or normal releases.

## How It Works

The release type is determined by the `CHANNEL` constant in `src/include/constants.py`:

- **STABLE**: Creates a normal release (not a pre-release)
- **ALPHA**: Creates a pre-release
- **BETA**: Creates a pre-release

## Implementation

### Scripts

- `scripts/get_release_type.py`: Reads the CHANNEL constant and outputs "true" or "false" for use in GitHub Actions
- `scripts/demo_release_type.py`: Demonstration script showing current configuration

### GitHub Workflow

The workflow file `.github/workflows/desktop-and-mobile-builds.yml` includes:

1. A "Determine Release Type" step in both Windows and APK build jobs
2. The step runs `scripts/get_release_type.py` to determine if the release should be a pre-release
3. The output is stored in the `release_type.prerelease` variable
4. Both release steps use this variable to set the `prerelease` parameter

## Example Behavior

| Channel Type | Release Type | GitHub Actions `prerelease` Value |
| ------------- | -------------- | ----------------------------------- |
| STABLE      | Normal       | `false`                          |
| ALPHA       | Pre-release  | `true`                           |
| BETA        | Pre-release  | `true`                           |

## Testing

To test the current configuration:

```bash
python scripts/demo_release_type.py
```

To run unit tests:

```bash
python scripts/test_release_type.py
```

## Changing the Channel

To change the release channel, edit `src/include/constants.py`:

```python
# For a stable release
CHANNEL = ChannelType.STABLE

# For an alpha pre-release
CHANNEL = ChannelType.ALPHA

# For a beta pre-release
CHANNEL = ChannelType.BETA
```
