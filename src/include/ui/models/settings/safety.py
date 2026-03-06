"""Security settings model (declarative) — connection history policy
and CA certificate store management."""

from __future__ import annotations

import time

from flet_model import Router, route
import flet as ft

from include.ui.frameworks.settings import (
    DeclarativeSettingsPage,
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
    settings_description = _("Connection history, CA certificates and security settings")
    settings_icon = ft.Icons.SECURITY
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

    def __init__(self, page: ft.Page, router: Router) -> None:
        super().__init__(page, router)

        # --- CA certificate management section --------------------------------
        self._ca_last_checked_text = ft.Text(
            _("Last checked: Never"),
            size=13,
            color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
        )
        self._ca_progress_ring = ft.ProgressRing(visible=False, width=20, height=20)
        self._ca_progress_text = ft.Text(
            _("Updating certificate store…"), visible=False
        )
        self._ca_progress_row = ft.Row(
            controls=[self._ca_progress_ring, self._ca_progress_text],
            visible=False,
        )
        self._ca_result_text = ft.Text(visible=False, size=13)
        self._ca_update_button = ft.Button(
            _("Check and Update Now"),
            icon=ft.Icons.REFRESH,
            on_click=self._on_ca_update_click,
        )

        # Append the CA cert section to the auto-generated field controls.
        self.controls.extend(
            [
                ft.Divider(height=24),
                ft.Text(
                    _("CA Certificates"),
                    size=16,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    _(
                        "The CA certificate store contains trusted root certificates "
                        "used to verify secure connections to your server."
                    ),
                    size=13,
                    color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
                ),
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                self._ca_last_checked_text,
                ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                self._ca_update_button,
                self._ca_progress_row,
                self._ca_result_text,
            ]
        )

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
        service = sm.get_service("ca_cert_update")
        if not isinstance(service, CACertUpdateService):
            return None
        return service

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

    def _ca_set_busy(self, busy: bool) -> None:
        """Toggle the CA cert progress indicator and button disabled state."""
        self._ca_update_button.disabled = busy
        self._ca_progress_ring.visible = busy
        self._ca_progress_text.visible = busy
        self._ca_progress_row.visible = busy
        self.update()

    # ------------------------------------------------------------------
    # CA cert event handlers
    # ------------------------------------------------------------------

    async def _on_ca_update_click(self, event: ft.Event[ft.Button]) -> None:
        """Handle the "Check and Update Now" button click."""
        service = self._ca_get_service()
        if service is None:
            send_error(self.page, _("Certificate update service is not available."))
            return

        self._ca_result_text.visible = False
        self._ca_set_busy(True)

        try:
            result = await service.update_now()
        except Exception as exc:
            self._ca_set_busy(False)
            send_error(self.page, _("Update failed: {error}").format(error=exc))
            return

        self._ca_set_busy(False)
        self._ca_refresh_last_checked()

        # Build result summary
        parts: list[str] = []
        if result.added:
            parts.append(_("{n} certificate(s) added").format(n=len(result.added)))
        if result.updated:
            parts.append(
                _("{n} certificate(s) updated").format(n=len(result.updated))
            )
        if result.removed:
            parts.append(
                _("{n} certificate(s) removed").format(n=len(result.removed))
            )
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

