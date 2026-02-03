"""Two-Factor Authentication settings model."""

from flet_model import Model, Router, route
import flet as ft

from include.classes.shared import AppShared
from include.ui.controls.dialogs.twofa_setup import TwoFactorSetupDialog
from include.ui.controls.dialogs.password_confirm import PasswordConfirmDialog
from include.ui.controls.dialogs.backup_codes import BackupCodesDialog
from include.ui.util.notifications import send_success, send_error
from include.ui.util.route import get_parent_route
from include.util.requests import do_request_2
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


@route("twofa_settings")
class TwoFactorSettingsModel(Model):
    """Model for Two-Factor Authentication settings page."""

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)

        self.appbar = ft.AppBar(
            title=ft.Text(_("Two-Factor Authentication")),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self._go_back),
        )
        self.app_shared = AppShared()

        # Store backup codes for display after verification
        self.pending_backup_codes: list[str] = []

        # 2FA status text
        self.status_text = ft.Text(
            _("Two-Factor Authentication Status: Checking..."),
            size=16,
            weight=ft.FontWeight.BOLD,
        )

        # Description text
        self.description_text = ft.Text(
            _(
                "Two-factor authentication adds an extra layer of security to your account. "
                "You'll need to enter a code from your authenticator app in addition to your password when logging in."
            ),
            size=14,
        )

        # Enable/Disable button
        self.toggle_button = ft.Button(
            _("Enable Two-Factor Authentication"),
            icon=ft.Icons.SECURITY,
            on_click=self._on_toggle_2fa,
            disabled=True,
        )

        # Disable button (shown when 2FA is enabled)
        self.disable_button = ft.Button(
            _("Disable Two-Factor Authentication"),
            icon=ft.Icons.SECURITY_UPDATE_WARNING,
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

    def did_mount(self) -> None:
        super().did_mount()
        self.page.run_task(self._load_2fa_status)

    async def _go_back(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(get_parent_route(self.page.route))

    async def _load_2fa_status(self):
        """Load the current 2FA status from server."""
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

    def _update_ui_for_status(self, is_enabled: bool):
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

    async def _on_toggle_2fa(self, e):
        """Handle enabling 2FA."""
        self.toggle_button.disabled = True
        self.loading_ring.visible = True
        self.update()

        try:
            # Request 2FA setup from server
            response = await do_request_2(
                "setup_2fa",
                data={"method": "totp"},
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.code == 200:
                # Server returned complete setup data
                secret = response.data.get("secret")
                provisioning_uri = response.data.get("provisioning_uri")
                backup_codes: list[str] = response.data.get("backup_codes", [])

                # Store backup codes for display after verification
                self.pending_backup_codes = backup_codes

                if secret and provisioning_uri:
                    # Show setup dialog
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
        """
        Verify the setup code and enable 2FA.

        Returns:
            True if successful, False otherwise
        """
        try:
            response = await do_request_2(
                "validate_2fa",
                data={"token": code},  # token is actually code.
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.code == 200:
                # Update UI status first
                self._update_ui_for_status(True)

                # Show backup codes if available
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

    async def _on_backup_codes_saved(self):
        """Handle when user confirms they've saved backup codes."""
        # Clear the pending backup codes
        self.pending_backup_codes = []
        # Show success message after backup codes dialog is closed
        send_success(self.page, _("Two-Factor Authentication enabled successfully!"))

    async def _cancel_2fa_setup(self):
        """Handle cancellation of 2FA setup."""
        # Clear pending backup codes
        self.pending_backup_codes = []

        try:
            # Notify server to cancel pending setup
            await do_request_2(
                "cancel_2fa_setup",
                username=self.app_shared.username,
                token=self.app_shared.token,
            )
        except Exception:
            pass  # Silent fail on cancel

    async def _on_disable_2fa(self, e):
        """Handle disabling 2FA."""
        # Show password confirmation dialog
        password_dialog = PasswordConfirmDialog(
            on_confirm_callback=self._confirm_disable_with_password,
            title=_("Disable Two-Factor Authentication"),
            message=_(
                "Please enter your password to disable two-factor authentication."
            ),
        )
        self.page.show_dialog(password_dialog)

    async def _confirm_disable_with_password(self, password: str) -> bool:
        """
        Confirm disabling 2FA with password verification.

        Args:
            password: The user's password

        Returns:
            True if successful, False otherwise
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
