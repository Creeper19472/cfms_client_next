"""Security settings model (declarative) — connection history policy
and CA certificate store management."""

import time

from flet_model import Router, route
import flet as ft
from flet_material_symbols import Symbols

from include.ui.frameworks.settings import (
    DeclarativeSettingsPage,
    HelpText,
    SectionHeader,
    Separator,
    SettingsField,
    settings_page,
)
from include.ui.util.notifications import send_error, send_success
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

# Maximum number of error messages shown in the UI notification
_MAX_DISPLAYED_ERRORS = 3


@settings_page
@route("safety_settings")
class SafetySettingsModel(DeclarativeSettingsPage):
    """Settings page for security policy and CA certificate management."""

    # Overview metadata
    settings_name = _("Security")
    settings_description = _(
        "Connection history, CA certificates and security settings"
    )
    settings_icon = Symbols.SECURITY
    settings_route_suffix = "safety_settings"

    # ---------------------------------------------------------------------------
    # Declarative fields
    # ---------------------------------------------------------------------------

    enable_conn_history_logging: SettingsField[bool] = SettingsField(
        label=_("Enable connection history logging"),
        key="enable_conn_history_logging",
        default=False,
        disabled=True,  # Feature not yet fully implemented
        description=_(
            "Decide whether the app should log the "
            "server address of the last connection. "
            "While this feature increases convenience, "
            "it may also increase the risk of exposing "
            "the server address."
        ),
    )

    # ---------------------------------------------------------------------------
    # CA certificates section (static structure declared here)
    # ---------------------------------------------------------------------------

    _ca_separator = Separator()
    _ca_header = SectionHeader(_("CA Certificates"))
    _ca_description = HelpText(
        _(
            "The CA certificate store contains trusted root certificates "
            "used to verify secure connections to your server."
        ),
        color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
    )

    def __init__(self, page: ft.Page, router: Router) -> None:
        # Create the dynamic CA cert controls *before* super().__init__() because
        # the base class calls _build_controls() during __init__, and our override
        # of that method references these attributes.
        self._ca_last_checked_text = ft.Text(
            _("Last checked: Never"),
            size=13,
            color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
        )
        self._ca_result_text = ft.Text(visible=False, size=13)
        self._ca_update_button = ft.Button(
            _("Check and Update Now"),
            icon=Symbols.REFRESH,
            on_click=self._on_ca_update_click,
        )

        super().__init__(page, router)

    # ------------------------------------------------------------------
    # Extend the declarative control list with the dynamic CA cert controls
    # ------------------------------------------------------------------

    def _build_controls(self) -> list[ft.Control]:
        """Build declarative field controls, then append the dynamic CA controls."""
        controls = super()._build_controls()
        controls += [
            self._ca_last_checked_text,
            self._ca_update_button,
            self._ca_result_text,
        ]
        return controls

    # ------------------------------------------------------------------
    # DeclarativeSettingsPage hook – called after values are loaded
    # ------------------------------------------------------------------

    async def _on_load(self) -> None:
        """Populate the CA cert last-checked timestamp from the running service."""
        self._ca_refresh_last_checked()
        self.update()

    # ------------------------------------------------------------------
    # CA cert helpers
    # ------------------------------------------------------------------

    def _ca_get_service(self):
        """Return the :class:`CACertUpdateService` from the service manager."""
        sm = self.app_shared.service_manager
        if sm is None:
            return None
        from include.classes.services.ca_update import CACertUpdateService

        return sm.get_service("ca_cert_update", CACertUpdateService)

    def _ca_refresh_last_checked(self) -> None:
        """Update the last-checked label from the service state."""
        service = self._ca_get_service()
        if service is None or service.last_updated is None:
            self._ca_last_checked_text.value = _("Last checked: Never")
            return
        ts = service.last_updated
        formatted = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        self._ca_last_checked_text.value = _("Last checked: {time}").format(
            time=formatted
        )

    # ------------------------------------------------------------------
    # CA cert event handlers
    # ------------------------------------------------------------------

    async def _on_ca_update_click(self, event: ft.Event[ft.Button]) -> None:
        """Handle the "Check and Update Now" button click.

        Shows a modal progress dialog while the update runs, then closes it
        and displays a result summary together with a success/error SnackBar.
        """
        from include.ui.controls.dialogs.ca_update_progress import (
            CACertUpdateProgressDialog,
        )

        service = self._ca_get_service()
        if service is None:
            send_error(self.page, _("Certificate update service is not available."))
            return

        self._ca_update_button.disabled = True
        self._ca_result_text.visible = False
        self.update()

        progress_dialog = CACertUpdateProgressDialog()
        self.page.show_dialog(progress_dialog)

        try:
            result = await service.update_now(
                on_progress=progress_dialog.make_progress_callback()
            )
        except Exception as exc:
            send_error(self.page, _("Update failed: {error}").format(error=exc))
            return
        finally:
            progress_dialog.close()
            self._ca_update_button.disabled = False
            self._ca_refresh_last_checked()
            self.update()

        # Build result summary
        parts: list[str] = []
        if result.added:
            parts.append(_("{n} certificate(s) added").format(n=len(result.added)))
        if result.updated:
            parts.append(_("{n} certificate(s) updated").format(n=len(result.updated)))
        if result.removed:
            parts.append(_("{n} certificate(s) removed").format(n=len(result.removed)))
        if result.unchanged:
            parts.append(
                _("{n} certificate(s) already up-to-date").format(
                    n=len(result.unchanged)
                )
            )

        if result.errors:
            error_summary = "; ".join(result.errors[:_MAX_DISPLAYED_ERRORS])
            send_error(
                self.page,
                _("Update completed with errors: {errors}").format(
                    errors=error_summary
                ),
            )
        elif result.changed:
            send_success(self.page, _("Certificate store updated successfully."))
        else:
            send_success(self.page, _("Certificate store is already up-to-date."))

        if parts:
            self._ca_result_text.value = " · ".join(parts)
            self._ca_result_text.visible = True

        self.update()
