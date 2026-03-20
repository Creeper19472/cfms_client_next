"""Connection settings model (declarative)."""

from typing import Literal

from flet_model import route
from flet_material_symbols import Symbols

from include.ui.frameworks.settings import (
    DeclarativeSettingsPage,
    HelpText,
    SectionHeader,
    BrowseMode,
    SettingsField,
    settings_page,
)
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


@settings_page
@route("conn_settings")
class ConnectionSettingsModel(DeclarativeSettingsPage):
    """Settings page for proxy and network connection settings."""

    # Overview metadata
    settings_name = _("Connect")
    settings_description = _("Change application proxy settings")
    settings_icon = Symbols.LINK_2
    settings_route_suffix = "conn_settings"

    # ---------------------------------------------------------------------------
    # Declarative fields
    # ---------------------------------------------------------------------------

    # UI-only toggle fields derived from the composite ``proxy_settings`` value.
    # They are not persisted directly; ``_on_load`` and ``_on_save`` translate
    # between the three-state ``proxy_settings`` stored in preferences and these
    # two independent boolean controls.

    basic_header: SectionHeader = SectionHeader(
        title=_("Basic"),
    )

    enable_proxy: SettingsField[bool] = SettingsField(
        label=_("Enable proxy"),
        persist=False,
    )
    follow_system_proxy: SettingsField[bool] = SettingsField(
        label=_("Follow system proxy settings"),
        depends_on="enable_proxy",
        persist=False,
    )

    # Persisted directly under their own preference keys.
    custom_proxy: SettingsField[str] = SettingsField(
        label=_("Custom Proxy"),
        key="custom_proxy",
        hint_text="e.g. socks5h://proxy:1080/",
        # Disabled when proxy is off *or* when system-proxy is on
        # (the custom URL field is irrelevant in both cases).
        depends_on=["enable_proxy", "!follow_system_proxy"],
    )
    force_ipv4: SettingsField[bool] = SettingsField(
        label=_("Force IPv4"),
        key="force_ipv4",
        default=False,
    )

    cert_section_header: SectionHeader = SectionHeader(
        title=_("Client Identity"),
    )
    cert_hint = HelpText(
        _(
            "This option only takes effect if both the certificate file and the "
            "key file are set."
        ),
    )

    client_cert_path: SettingsField[str] = SettingsField(
        label=_("Client certificate path"),
        key="client_cert_path",
        default="",
        description=_(
            "Path to the client certificate file (PEM format) used for "
            "mutual TLS authentication with the server. Leave blank if not used."
        ),
        browse=BrowseMode.FILE,
    )
    client_key_path: SettingsField[str] = SettingsField(
        label=_("Client private key path"),
        key="client_key_path",
        default="",
        description=_(
            "Path to the client private key file (PEM format) used for "
            "mutual TLS authentication with the server. Leave blank if not used."
        ),
        browse=BrowseMode.FILE,
    )

    # ---------------------------------------------------------------------------
    # Load / save hooks: translate the composite ``proxy_settings`` value
    # ---------------------------------------------------------------------------

    async def _on_load(self) -> None:
        """Derive ``enable_proxy`` and ``follow_system_proxy`` from the stored
        ``proxy_settings`` value after the persisted fields have been loaded."""
        proxy_settings: str | Literal[True] | None = self.app_shared.preferences[
            "settings"
        ].get("proxy_settings")
        self.enable_proxy = bool(proxy_settings)
        self.follow_system_proxy = proxy_settings is True

    async def _on_save(self) -> str | None:
        """Compute the composite ``proxy_settings`` value and write it to
        preferences before they are dumped to disk."""
        custom_proxy_value: str = self.custom_proxy or ""
        if self.enable_proxy:
            if self.follow_system_proxy:
                proxy_settings_value: str | Literal[True] | None = True
            else:
                proxy_settings_value = (
                    custom_proxy_value if custom_proxy_value else True
                )
        else:
            proxy_settings_value = None

        self.app_shared.preferences["settings"]["proxy_settings"] = proxy_settings_value
        return None
