from typing import Optional
from enum import Enum
import re
import requests

from include.constants import GITHUB_REPO
from include.classes.version import ChannelType
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


SUPPORTED_PLATFORM = {"windows": "windows", "android": ".apk"}


class AssetDigestType(Enum):
    SHA256 = "sha256"


class AssetDigest:
    def __init__(self, raw: str):
        _raw = raw.split(":")
        if len(_raw) != 2:
            raise ValueError("Wrong raw components")
        self.type = AssetDigestType(_raw[0])
        self.digest = _raw[1]


class GithubAsset:
    def __init__(
        self,
        name: str = "",
        digest: Optional[AssetDigest] = None,
        download_link: str = "",
    ):
        self.name = name
        self.digest = digest
        self.download_link = download_link


class GithubRelease:
    def __init__(
        self,
        version: str = "",
        info: str = "",
        release_link: str = "",
        assets: list[GithubAsset] = [],
        channel: Optional[ChannelType] = None,
    ):
        self.version = version  # <- tag_name
        self.info = info  # <- body
        self.release_link = release_link  # <- html_url
        self.assets = assets  # <- assets
        self.channel = channel  # <- parsed from body or prerelease flag


def parse_channel_from_body(body: str, is_prerelease: bool) -> ChannelType:
    """
    Parse channel type from release body.
    
    Looks for structured metadata like: <!-- channel: alpha -->
    Falls back to prerelease flag if metadata not found.
    
    Args:
        body: Release body text
        is_prerelease: Whether the release is marked as prerelease
        
    Returns:
        ChannelType enum value
    """
    # Try to find channel metadata in HTML comment
    # Build regex pattern from valid channel types
    valid_channels = '|'.join([c.value for c in ChannelType])
    pattern = rf'<!--\s*channel:\s*({valid_channels})\s*-->'
    match = re.search(pattern, body, re.IGNORECASE)
    if match:
        channel_str = match.group(1).lower()
        return ChannelType(channel_str)
    
    # Fallback: if prerelease flag is set, assume alpha as default
    # If not prerelease, it's stable
    if is_prerelease:
        return ChannelType.ALPHA
    else:
        return ChannelType.STABLE


def get_latest_release(channel: Optional[ChannelType] = None) -> Optional[GithubRelease]:
    """
    Get the latest release, optionally filtered by channel.
    
    Args:
        channel: If provided, only returns releases matching this channel.
                If None, returns the latest stable release (GitHub's /releases/latest).
    
    Returns:
        GithubRelease object or None if no matching release found
    """
    # If no channel specified or stable channel, use /releases/latest endpoint
    if channel is None or channel == ChannelType.STABLE:
        try:
            resp = requests.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            )
            if resp.status_code != 200:
                return None
        except requests.exceptions.ConnectionError:
            raise  # leave it to the parent to handle

        release_data = resp.json()
        assets = []
        for asset in release_data["assets"]:
            assets.append(
                GithubAsset(
                    name=asset["name"],
                    digest=AssetDigest(asset["digest"]),
                    download_link=asset["browser_download_url"],
                )
            )

        parsed_channel = parse_channel_from_body(
            release_data.get("body", ""),
            release_data.get("prerelease", False)
        )

        return GithubRelease(
            version=release_data["tag_name"],
            info=release_data["body"],
            release_link=release_data["html_url"],
            assets=assets,
            channel=parsed_channel,
        )
    
    # For alpha/beta channels, fetch all releases and filter
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases"
        )
        if resp.status_code != 200:
            return None
    except requests.exceptions.ConnectionError:
        raise  # leave it to the parent to handle

    releases_data = resp.json()
    
    # Filter and find the latest release matching the requested channel
    for release_data in releases_data:
        parsed_channel = parse_channel_from_body(
            release_data.get("body", ""),
            release_data.get("prerelease", False)
        )
        
        # Skip if channel doesn't match
        if parsed_channel != channel:
            continue
        
        # Found a matching release
        assets = []
        for asset in release_data["assets"]:
            assets.append(
                GithubAsset(
                    name=asset["name"],
                    digest=AssetDigest(asset["digest"]),
                    download_link=asset["browser_download_url"],
                )
            )

        return GithubRelease(
            version=release_data["tag_name"],
            info=release_data["body"],
            release_link=release_data["html_url"],
            assets=assets,
            channel=parsed_channel,
        )
    
    # No matching release found
    return None


def is_new_version(
    is_preview: bool,
    commit_count: int,
    version_name: str,
    version_tag: str,
) -> bool:
    # Remove prefix like 'r' or 'v'
    new_version = version_tag[1:]
    if is_preview:
        # Preview version: based on 'mihonapp/mihon-preview' repository releases
        # Tagged as 'r1234' format
        return new_version.isdigit() and int(new_version) > commit_count
    else:
        # Release version: based on 'mihonapp/mihon' repository releases
        # Tagged as 'v0.1.2' format
        old_version = version_name[1:]

        new_sem_ver = [int(part) for part in new_version.split(".")]
        old_sem_ver = [int(part) for part in old_version.split(".")]

        for index, (new_part, old_part) in enumerate(zip(new_sem_ver, old_sem_ver)):
            if new_part > old_part:
                return True

        return False
