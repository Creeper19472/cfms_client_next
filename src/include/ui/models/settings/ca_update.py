"""CA Certificate Store settings page – kept for reference only.

This page has been merged into the Security settings page
(:class:`~include.ui.models.settings.safety.SafetySettingsModel`).
It is no longer registered in the settings overview.
"""

from __future__ import annotations

import time

from flet_model import route
import flet as ft

from include.classes.services.ca_update import CACertUpdateService
from include.ui.frameworks.settings import DeclarativeActionPage
from include.ui.util.notifications import send_error, send_success
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

# Maximum number of error messages shown in the UI notification
_MAX_DISPLAYED_ERRORS = 3


# NOTE: @settings_page and @route decorators removed – this page is no
# longer reachable or registered in the settings overview.
class CACertSettingsModel(DeclarativeActionPage):
    """Settings page for managing the local CA certificate store.

    Displays the last-checked timestamp and allows the user to trigger a
    manual certificate store update.  Progress is shown in-page while the
    update is running.
    """

    # Overview metadata
    settings_name = _("CA Certificates")
    settings_description = _("Manage trusted CA certificate store")
    settings_icon = ft.Icons.VERIFIED_USER_OUTLINED
    settings_route_suffix = "ca_certs_settings"

    def __init__(self, page: ft.Page, router: Router) -> None:
        super().__init__(page, router)

        # --- description -----------------------------------------------------
        self.description_text = ft.Text(
            _(
                "The CA certificate store contains the trusted root certificates "
                "used to verify secure connections to your server.  "
                "Keeping it up-to-date ensures that newly issued certificates are "
                "accepted and revoked certificates are rejected."
            ),
            size=14,
        )

        # --- last-checked info -----------------------------------------------
        self.last_checked_text = ft.Text(
            _("Last checked: Never"),
            size=13,
            color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
        )

        # --- progress indicator (hidden while idle) --------------------------
        self.progress_ring = ft.ProgressRing(visible=False, width=20, height=20)
        self.progress_text = ft.Text(_("Updating certificate store…"), visible=False)
        self.progress_row = ft.Row(
            controls=[self.progress_ring, self.progress_text],
            visible=False,
        )

        # --- result summary (hidden until an update has run) -----------------
        self.result_text = ft.Text(visible=False, size=13)

        # --- action button ---------------------------------------------------
        self.update_button = ft.Button(
            _("Check and Update Now"),
            icon=ft.Icons.REFRESH,
            on_click=self._on_update_click,
        )

        # --- layout ----------------------------------------------------------
        self.controls = [
            self.description_text,
            ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
            self.last_checked_text,
            ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
            self.update_button,
            self.progress_row,
            self.result_text,
        ]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _on_load(self) -> None:
        """Populate the last-checked timestamp from the running service."""
        self._refresh_last_checked_text()
        self.update()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_service(self) -> CACertUpdateService | None:
        """Return the :class:`CACertUpdateService` from the service manager."""
        sm = self.app_shared.service_manager
        if sm is None:
            return None
        service = sm.get_service("ca_cert_update")
        if not isinstance(service, CACertUpdateService):
            return None
        return service

    def _refresh_last_checked_text(self) -> None:
        """Update :attr:`last_checked_text` from the service state."""
        service = self._get_service()
        if service is None or service.last_updated is None:
            self.last_checked_text.value = _("Last checked: Never")
            return

        ts = service.last_updated
        formatted = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        self.last_checked_text.value = _("Last checked: {time}").format(time=formatted)

    def _set_busy(self, busy: bool) -> None:
        """Toggle the progress indicator and disable the button while busy."""
        self.update_button.disabled = busy
        self.progress_ring.visible = busy
        self.progress_text.visible = busy
        self.progress_row.visible = busy
        self.update()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _on_update_click(self, event: ft.Event[ft.Button]) -> None:  # type: ignore[override]
        """Handle the "Check and Update Now" button click."""
        service = self._get_service()
        if service is None:
            send_error(self.page, _("Certificate update service is not available."))
            return

        self.result_text.visible = False
        self._set_busy(True)

        try:
            result = await service.update_now()
        except Exception as exc:
            self._set_busy(False)
            send_error(self.page, _("Update failed: {error}").format(error=exc))
            return

        self._set_busy(False)
        self._refresh_last_checked_text()

        # Build result summary
        parts: list[str] = []
        if result.added:
            parts.append(
                _("{n} certificate(s) added").format(n=len(result.added))
            )
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
            send_success(
                self.page, _("Certificate store is already up-to-date.")
            )

        if parts:
            self.result_text.value = " · ".join(parts)
            self.result_text.visible = True

        self.update()
