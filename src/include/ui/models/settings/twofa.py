"""Two-Factor Authentication settings model."""

from flet_model import Router, route
import flet as ft
from flet_material_symbols import Symbols

from include.ui.controls.dialogs.twofa_setup import TwoFactorSetupDialog
from include.ui.controls.dialogs.password_confirm import PasswordConfirmDialog
from include.ui.controls.dialogs.backup_codes import BackupCodesDialog
from include.ui.frameworks.settings import DeclarativeActionPage, settings_page
from include.ui.util.notifications import send_success, send_error
from include.util.requests import do_request_2
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


@settings_page
@route("twofa_settings")
class TwoFactorSettingsModel(DeclarativeActionPage):
    """Settings page for Two-Factor Authentication management.

    This page is action-based rather than preference-based: it fetches the
    current 2FA status from the server and lets the user enable or disable
    2FA via multi-step dialogs.  It therefore uses
    :class:`~include.ui.frameworks.settings.DeclarativeActionPage` (no Save
    button, async :meth:`_on_load` for server fetch) rather than
    :class:`~include.ui.frameworks.settings.DeclarativeSettingsPage`.
    """

    # Overview metadata
    settings_name = _("Two-Factor Authentication")
    settings_description = _("Manage two-factor authentication settings")
    settings_icon = Symbols.SIGNATURE
    settings_route_suffix = "twofa_settings"

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)

        # Backup codes collected during setup; shown after TOTP verification.
        self.pending_backup_codes: list[str] = []

        # Status / description text
        self.status_text = ft.Text(
            _("Two-Factor Authentication Status: Checking..."),
            size=16,
            weight=ft.FontWeight.BOLD,
        )
        self.description_text = ft.Text(
            _(
                "Two-factor authentication adds an extra layer of security to your account. "
                "You'll need to enter a code from your authenticator app in addition to your password when logging in."
            ),
            size=14,
        )

        # Action buttons
        self.toggle_button = ft.Button(
            _("Enable Two-Factor Authentication"),
            icon=Symbols.SECURITY,
            on_click=self._on_toggle_2fa,
            disabled=True,
        )
        self.disable_button = ft.Button(
            _("Disable Two-Factor Authentication"),
            icon=Symbols.SECURITY_UPDATE_WARNING,
            on_click=self._on_disable_2fa,
            visible=False,
            color=ft.Colors.ERROR,
        )
        self.loading_ring = ft.ProgressRing(visible=False)

        self.controls = [
            self.status_text,
            self.description_text,
            ft.Divider(),
            ft.Row(
                [self.loading_ring],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            self.toggle_button,
            self.disable_button,
        ]

    # ------------------------------------------------------------------
    # _on_load: fetch 2FA status from server
    # ------------------------------------------------------------------

    async def _on_load(self) -> None:
        """Load the current 2FA status from the server."""
        self.loading_ring.visible = True
        self.update()

        try:
            response = await do_request_2(
                "get_2fa_status",
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.code == 200:
                is_enabled = response.data.get("enabled", False)
                self._update_ui_for_status(is_enabled)
            else:
                send_error(
                    self.page,
                    _("Failed to load 2FA status: {resp_msg}").format(
                        resp_msg=response.message
                    ),
                )

        except Exception as e:
            send_error(
                self.page, _("Error loading 2FA status: {strerr}").format(strerr=str(e))
            )
        finally:
            self.loading_ring.visible = False
            self.toggle_button.disabled = False
            self.update()

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def _update_ui_for_status(self, is_enabled: bool) -> None:
        """Update UI based on 2FA status."""
        if is_enabled:
            self.status_text.value = _("Two-Factor Authentication Status: Enabled")
            self.status_text.color = ft.Colors.GREEN
            self.toggle_button.visible = False
            self.disable_button.visible = True
        else:
            self.status_text.value = _("Two-Factor Authentication Status: Disabled")
            self.status_text.color = ft.Colors.ORANGE
            self.toggle_button.visible = True
            self.disable_button.visible = False

        self.app_shared.user_2fa_enabled = is_enabled
        self.update()

    # ------------------------------------------------------------------
    # Enable 2FA flow
    # ------------------------------------------------------------------

    async def _on_toggle_2fa(self, e) -> None:
        """Handle enabling 2FA."""
        self.toggle_button.disabled = True
        self.loading_ring.visible = True
        self.update()

        try:
            response = await do_request_2(
                "setup_2fa",
                data={"method": "totp"},
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.code == 200:
                secret = response.data.get("secret")
                provisioning_uri = response.data.get("provisioning_uri")
                backup_codes: list[str] = response.data.get("backup_codes", [])
                self.pending_backup_codes = backup_codes

                if secret and provisioning_uri:
                    setup_dialog = TwoFactorSetupDialog(
                        secret=secret,
                        qr_uri=provisioning_uri,
                        on_verify_callback=self._verify_and_enable_2fa,
                        on_cancel_callback=self._cancel_2fa_setup,
                    )
                    self.page.show_dialog(setup_dialog)
                else:
                    send_error(self.page, _("Invalid setup data received from server"))
            else:
                send_error(
                    self.page,
                    _("Failed to initiate 2FA setup: {resp_msg}").format(
                        resp_msg=response.message
                    ),
                )

        except Exception as e:
            send_error(
                self.page, _("Error setting up 2FA: {strerror}").format(strerror=str(e))
            )
        finally:
            self.loading_ring.visible = False
            self.toggle_button.disabled = False
            self.update()

    async def _verify_and_enable_2fa(self, code: str) -> bool:
        """Verify the setup code and enable 2FA.

        Returns ``True`` on success, ``False`` otherwise.
        """
        try:
            response = await do_request_2(
                "validate_2fa",
                data={"token": code},
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.code == 200:
                self._update_ui_for_status(True)
                if self.pending_backup_codes:
                    backup_codes_dialog = BackupCodesDialog(
                        backup_codes=self.pending_backup_codes,
                        on_close_callback=self._on_backup_codes_saved,
                    )
                    self.page.show_dialog(backup_codes_dialog)
                else:
                    send_success(
                        self.page, _("Two-Factor Authentication enabled successfully!")
                    )
                return True
            else:
                return False

        except Exception as e:
            send_error(
                self.page, "Error verifying 2FA setup: {strerr}".format(strerr=str(e))
            )
            return False

    async def _on_backup_codes_saved(self) -> None:
        """Handle when the user confirms they've saved backup codes."""
        self.pending_backup_codes = []
        send_success(self.page, _("Two-Factor Authentication enabled successfully!"))

    async def _cancel_2fa_setup(self) -> None:
        """Handle cancellation of 2FA setup."""
        self.pending_backup_codes = []
        try:
            await do_request_2(
                "cancel_2fa_setup",
                username=self.app_shared.username,
                token=self.app_shared.token,
            )
        except Exception:
            pass  # Silent fail on cancel

    # ------------------------------------------------------------------
    # Disable 2FA flow
    # ------------------------------------------------------------------

    async def _on_disable_2fa(self, e) -> None:
        """Handle disabling 2FA."""
        password_dialog = PasswordConfirmDialog(
            on_confirm_callback=self._confirm_disable_with_password,
            title=_("Disable Two-Factor Authentication"),
            message=_(
                "Please enter your password to disable two-factor authentication."
            ),
        )
        self.page.show_dialog(password_dialog)

    async def _confirm_disable_with_password(self, password: str) -> bool:
        """Confirm disabling 2FA with password verification.

        Returns ``True`` on success, ``False`` otherwise.
        """
        try:
            response = await do_request_2(
                "disable_2fa",
                data={"password": password},
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.code == 200:
                send_success(self.page, _("Two-Factor Authentication disabled"))
                self._update_ui_for_status(False)
                return True
            else:
                send_error(
                    self.page,
                    _("Failed to disable 2FA: {resp_msg}").format(
                        resp_msg=response.message
                    ),
                )
                return False

        except Exception as e:
            send_error(
                self.page, _("Error disabling 2FA: {strerr}").format(strerr=str(e))
            )
            return False
