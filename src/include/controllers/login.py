import base64
import os
from typing import TYPE_CHECKING, cast

from include.classes.services.download import DownloadManagerService
from include.controllers.base import Controller
from include.ui.controls.dialogs.admin.accounts import PasswdUserDialog
from include.ui.controls.dialogs.twofa_verify import TwoFactorVerifyDialog
from include.util.requests import do_request
from include.util.userpref import load_user_preference

if TYPE_CHECKING:
    from include.ui.controls.views.login import LoginForm

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class LoginFormController(Controller["LoginForm"]):
    def __init__(self, control: "LoginForm"):
        super().__init__(control)

    async def action_login(self):
        await self._action_login()
        self.control.enable_interactions()

    async def _action_login(self):
        username = self.control.username_field.value.strip()
        password = self.control.password_field.value

        response = await do_request(
            "login",
            {
                "username": username,
                "password": password,
            },
        )

        if (code := response["code"]) == 200:
            # Regular login without 2FA
            await self._complete_login(username, response["data"])

        elif code == 202:
            # Server indicates 2FA verification is required
            # Store partial login state
            self.app_shared.pending_2fa_verification = True

            # Get the verification method from response
            method = response["data"].get("method", "totp")

            if method == "totp":
                # Show 2FA verification dialog for TOTP
                twofa_dialog = TwoFactorVerifyDialog(
                    on_verify_callback=self._verify_2fa_code,
                    on_cancel_callback=self._cancel_2fa_login,
                )
                self.control.page.show_dialog(twofa_dialog)
            else:
                self.control.send_error(f"Unsupported 2FA method: {method}")
            return

        elif code == 403:
            self.control.page.show_dialog(
                PasswdUserDialog(
                    username, tip=_("Password must be changed before login.")
                )
            )
            return

        else:
            self.control.send_error(
                _("Login failed: ({code}) {message}").format(
                    code=code, message=response["message"]
                )
            )

    async def _complete_login(self, username: str, data: dict):
        """Complete the login process after authentication."""
        # Save current user's tasks before switching users
        # This prevents data loss when switching between users
        download_service = None
        if self.app_shared.service_manager:
            download_service = cast(
                DownloadManagerService,
                self.app_shared.service_manager.get_service("download_manager"),
            )

        if self.app_shared.username and self.app_shared.username != username:
            if download_service:
                await download_service._save_tasks()

        self.app_shared.username = username
        self.app_shared.nickname = data.get("nickname")
        self.app_shared.token = data["token"]
        self.app_shared.token_exp = data.get("exp")
        self.app_shared.user_permissions = data["permissions"]
        self.app_shared.user_groups = data["groups"]
        self.app_shared.user_2fa_enabled = data.get("has_2fa", False)
        self.app_shared.pending_2fa_verification = False
        self.app_shared.user_perference = load_user_preference(username)

        # Store parent_view reference for cleaner code
        parent_view = self.control.parent_view

        try:
            # Hide login form and show loading view
            self.control.visible = False
            parent_view.data_loading_view.visible = True
            parent_view.avatar_preview.visible = True
            parent_view.update()

            # Get and download avatar if available
            parent_view.data_loading_view.set_status(_("Downloading avatar"))
            from include.util.avatar import get_user_avatar, download_avatar_file

            # Get avatar task data from server
            task_data = await get_user_avatar(username)
            if task_data:
                # Download avatar using task_data (force download on login to ensure up-to-date)
                avatar_path = await download_avatar_file(
                    task_data, username, force_download=True
                )
                self.app_shared.avatar_path = avatar_path
                if avatar_path and os.path.exists(avatar_path):
                    # Update the avatar preview with the downloaded avatar
                    with open(avatar_path, "rb") as f:
                        avatar_base64 = base64.b64encode(f.read()).decode("utf-8")
                        parent_view.avatar_preview.preview_avatar.foreground_image_src = (
                            f"data:image;base64,{avatar_base64}"
                        )
                    parent_view.avatar_preview.preview_avatar.content = None
                    parent_view.avatar_preview.update()

            # Reload download tasks for the logged-in user
            if download_service:
                parent_view.data_loading_view.set_status(_("Loading tasks"))
                await download_service.reload_tasks_for_user()

            self.control.clear_fields()
        finally:
            # Reset visibility for next login
            self.control.visible = True
            parent_view.data_loading_view.visible = False
            parent_view.data_loading_view.clear_status()

        self.control.page.run_task(self.control.page.push_route, "/home")

    async def _verify_2fa_code(self, code: str, is_recovery_code: bool = False) -> bool:
        """
        Verify 2FA code and complete login.

        Args:
            code: The 6-digit verification code or recovery code
            is_recovery_code: True if using recovery code, False if using TOTP

        Returns:
            True if verification successful, False otherwise
        """

        username = self.control.username_field.value.strip()
        password = self.control.password_field.value

        try:
            request_data = {
                "username": username,
                "password": password,
                "2fa_token": code,  # Recovery code and TOTP use the same key
            }

            response = await do_request("login", request_data)

            if response["code"] == 200:
                self.control.page.run_task(
                    self._complete_login, username, response["data"]
                )
                return True
            else:
                return False

        except Exception as e:
            self.control.send_error(f"2FA verification error: {str(e)}")
            return False

    async def _cancel_2fa_login(self):
        """Handle cancellation of 2FA login."""
        self.app_shared.username = None
        self.app_shared.pending_2fa_verification = False
