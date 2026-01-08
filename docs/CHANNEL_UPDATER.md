# Channel-Based Update Checker

## Overview

This document describes the channel-based update checker implementation that allows users to freely switch between different version channels (stable, beta, and alpha).

## Features

1. **Channel Selection**: Users can select their preferred update channel in Settings > Updates
2. **Automatic Channel Detection**: Releases are automatically tagged with their channel type
3. **Smart Filtering**: The updater only shows releases matching the selected channel
4. **Backward Compatibility**: Works with existing releases that don't have channel metadata

## Architecture

### Components

1. **User Preferences** (`src/include/classes/config.py`)
   - Added `update_channel` setting (default: "alpha")
   - Stored in `preferences.yaml` under `settings.update_channel`

2. **GitHub Workflow** (`.github/workflows/desktop-and-mobile-builds.yml`)
   - New script: `scripts/get_channel_name.py` to extract channel from source
   - Adds structured metadata to release body: `<!-- channel: {alpha|beta|stable} -->`
   - Sets `prerelease` flag based on channel type

3. **Updater Module** (`src/include/util/upgrade/updater.py`)
   - `parse_channel_from_body()`: Parses channel metadata from release body
   - Enhanced `get_latest_release()`: Accepts optional channel parameter
   - For stable channel: Uses `/releases/latest` endpoint
   - For alpha/beta: Fetches all releases and filters by channel

4. **UI Components**
   - New settings page: `src/include/ui/models/settings/updates.py`
   - Updated about page: `src/include/ui/models/about.py`
   - Displays channel information when checking for updates

## Channel Types

### Stable
- Most thoroughly tested releases
- Recommended for production use
- Uses GitHub's `/releases/latest` endpoint
- Marked with `prerelease: false`

### Beta
- Pre-release versions with new features
- Generally stable, suitable for early adopters
- Marked with `prerelease: true` and `<!-- channel: beta -->`

### Alpha
- Cutting-edge development versions
- Frequent updates with latest features
- May be unstable
- Marked with `prerelease: true` and `<!-- channel: alpha -->`

## Usage

### For Users

1. Navigate to Settings > Updates
2. Select your preferred channel from the dropdown
3. Save the settings
4. Go to About page to check for updates
5. The system will now only show updates from your selected channel

### For Developers

When creating a new release:
1. Set `CHANNEL` in `src/include/constants.py` to desired channel type
2. Create a git tag (e.g., `v0.5.0`)
3. Push the tag to trigger the GitHub workflow
4. The workflow will automatically:
   - Determine the channel from the source code
   - Set the `prerelease` flag appropriately
   - Add channel metadata to the release body

## Backward Compatibility

The system handles releases without channel metadata:
- If `prerelease: false` → assumed to be stable
- If `prerelease: true` → assumed to be alpha (default for prereleases)
- Existing releases will continue to work as before

## Testing

To test the channel parsing:

```bash
python -c "
import sys
sys.path.insert(0, 'src')
from include.util.upgrade.updater import parse_channel_from_body, ChannelType

body = '<!-- channel: beta -->\nSome release notes'
channel = parse_channel_from_body(body, True)
print(f'Detected channel: {channel.value}')
"
```

To test the workflow scripts:

```bash
python scripts/get_channel_name.py  # Should output: alpha/beta/stable
python scripts/get_release_type.py  # Should output: true/false
```

## Future Enhancements

Possible future improvements:
1. Auto-update functionality per channel
2. Channel-specific notification preferences
3. Detailed changelog comparison between versions
4. Rollback to previous version
5. Beta program enrollment system
