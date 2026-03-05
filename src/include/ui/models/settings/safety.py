"""Safety / security settings model (declarative)."""

from flet_model import route
import flet as ft

from include.ui.settings_framework import (
    DeclarativeSettingsPage,
    SettingsField,
    settings_page,
)
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


@settings_page
@route("safety_settings")
class SafetySettingsModel(DeclarativeSettingsPage):
    """Settings page for connection-history logging policy."""

    # Overview metadata
    settings_name = "Safety"
    settings_description = "Adjust application connection history policy"
    settings_icon = ft.Icons.SECURITY
    settings_route_suffix = "safety_settings"

    # ---------------------------------------------------------------------------
    # Declarative fields
    # ---------------------------------------------------------------------------

    enable_conn_history_logging: bool = SettingsField(
        label="Enable connection history logging",
        key="enable_conn_history_logging",
        default=False,
        disabled=True,  # Feature not yet fully implemented
        description=(
            "Decide whether the app should log the "
            "server address of the last connection. "
            "While this feature increases convenience, "
            "it may also increase the risk of exposing "
            "the server address."
        ),
    )
