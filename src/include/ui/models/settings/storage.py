"""Storage settings model (declarative)."""

from typing import cast

import flet as ft
import flet_permission_handler as fph
from flet_model import route
from flet_material_symbols import Symbols

from include.classes.preferences import UserPreference
from include.ui.controls.banners.settings import ExternalStorageWarningBanner
from include.ui.frameworks.settings import (
    DeclarativeSettingsPage,
    SettingsField,
    settings_page,
)
from include.util.locale import get_translation
from include.util.userpref import save_user_preference

t = get_translation()
_ = t.gettext


@settings_page
@route("storage_settings")
class StorageSettingsModel(DeclarativeSettingsPage):
    """Settings page for external storage configuration."""

    # Overview metadata
    settings_name = _("Storage")
    settings_description = _("Configure external storage options")
    settings_icon = Symbols.STORAGE
    settings_route_suffix = "storage_settings"

    # ---------------------------------------------------------------------------
    # Declarative fields
    # ---------------------------------------------------------------------------

    # Both fields are UI-only (persist=False); _on_load / _on_save translate
    # between these controls and the UserPreference dataclass.
    use_external_storage: SettingsField[bool] = SettingsField(
        label=_("Use external storage"),
        persist=False,
    )
    external_storage_path: SettingsField[str] = SettingsField(
        label=_("External storage path"),
        depends_on="use_external_storage",
        browse=True,
        persist=False,
        description=_(
            "The application will only save files to the specified location if the "
            '"Use external storage" switch is enabled and an external storage path '
            "is set."
        ),
    )

    # ---------------------------------------------------------------------------
    # Custom switch-change hook: permission check
    # ---------------------------------------------------------------------------

    async def _on_switch_change(self, event: ft.Event[ft.Switch]) -> None:
        """Show a permission warning when external storage is enabled without
        the required OS permission."""
        ph = fph.PermissionHandler()
        if (
            bool(event.control.value)
            and await ph.get_status(fph.Permission.MANAGE_EXTERNAL_STORAGE)
            != fph.PermissionStatus.GRANTED
        ):
            self.page.show_dialog(ExternalStorageWarningBanner())
        await super()._on_switch_change(event)

    # ---------------------------------------------------------------------------
    # Load / save hooks: read from and write to UserPreference
    # ---------------------------------------------------------------------------

    async def _on_load(self) -> None:
        """Populate fields from the current UserPreference dataclass."""
        user_pref = cast(UserPreference, self.app_shared.user_perference)
        self.use_external_storage = user_pref.use_external_storage
        self.external_storage_path = user_pref.external_storage_path

    async def _on_save(self) -> str | None:
        """Persist field values back to UserPreference."""
        user_pref = cast(UserPreference, self.app_shared.user_perference)
        user_pref.use_external_storage = self.use_external_storage
        user_pref.external_storage_path = self.external_storage_path
        save_user_preference(cast(str, self.app_shared.username), user_pref)
        return None
