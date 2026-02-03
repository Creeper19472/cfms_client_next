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
    valid_channels = "|".join([c.value for c in ChannelType])
    pattern = rf"<!--\s*channel:\s*({valid_channels})\s*-->"
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


def get_latest_release(
    channel: Optional[ChannelType] = None,
) -> Optional[GithubRelease]:
    session = requests.Session()
    timeout = 5
    releases: list[dict] = []

    # Try the "latest" endpoint for stable/default, then the full list
    try:
        if channel is None or channel == ChannelType.STABLE:
            resp = session.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest", timeout=timeout)
            if resp.ok:
                releases.append(resp.json())
        resp = session.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases", timeout=timeout)
        if resp.ok:
            releases.extend(resp.json())
    except requests.exceptions.RequestException:
        raise  # let caller handle connectivity/timeouts

    if not releases:
        return None

    def parsed_channel_of(release: dict) -> ChannelType:
        return parse_channel_from_body(release.get("body", ""), release.get("prerelease", False))

    def matches_channel(parsed: ChannelType, requested: Optional[ChannelType]) -> bool:
        if requested is None or parsed == requested:
            return True
        # allow fallback priority: alpha <- beta <- stable
        if requested == ChannelType.ALPHA and parsed == ChannelType.BETA:
            return True
        if requested == ChannelType.BETA and parsed == ChannelType.STABLE:
            return True
        return False

    def tag_sort_key(release: dict):
        tag = str(release.get("tag_name", ""))
        # rNNN numeric previews
        if tag.startswith("r") and tag[1:].isdigit():
            return (2, int(tag[1:]))
        # semver vX.Y.Z or X.Y.Z
        m = re.match(r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", tag)
        if m:
            parts = [int(p) if p else 0 for p in m.groups()]
            return (1, parts[0], parts[1], parts[2])
        # fallback - sort lexicographically last
        return (0, tag)

    # Filter releases by channel preference
    candidates = []
    for r in releases:
        parsed = parsed_channel_of(r)
        if matches_channel(parsed, channel):
            candidates.append(r)

    if not candidates:
        return None

    latest_release = max(candidates, key=tag_sort_key)

    assets: list[GithubAsset] = []
    for asset in latest_release.get("assets", []):
        digest_obj = None
        raw_digest = asset.get("digest") or asset.get("content_type")  # tolerate different keys
        if isinstance(raw_digest, str) and raw_digest:
            try:
                digest_obj = AssetDigest(raw_digest)
            except Exception:
                digest_obj = None
        assets.append(
            GithubAsset(
                name=asset.get("name", ""),
                digest=digest_obj,
                download_link=asset.get("browser_download_url", ""),
            )
        )

    return GithubRelease(
        version=latest_release.get("tag_name", ""),
        info=latest_release.get("body", ""),
        release_link=latest_release.get("html_url", ""),
        assets=assets,
        channel=parsed_channel_of(latest_release),
    )


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

        return new_sem_ver > old_sem_ver
