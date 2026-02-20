import base64
import os
from typing import TYPE_CHECKING, cast

from include.classes.exceptions.config import CorruptedEncryptedConfigError
from include.classes.preferences import UserPreference
from include.classes.services.download import DownloadManagerService
from include.controllers.base import Controller
from include.ui.controls.dialogs.admin.accounts import PasswdUserDialog
from include.ui.controls.dialogs.corrupted_config import CorruptedConfigDialog
from include.ui.controls.dialogs.twofa_verify import TwoFactorVerifyDialog
from include.util.requests import do_request
from include.util.userpref import load_user_preference
from include.util.kdf import generate_dek, encrypt_dek, decrypt_dek

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
            await self._complete_login(username, response["data"], password)

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

    async def _complete_login(self, username: str, data: dict, password: str = ""):
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
        # Clear any stale DEK from a previous session before setting up the new one
        self.app_shared.dek = None

        # Store parent_view reference for cleaner code
        parent_view = self.control.parent_view

        try:
            # Hide login form and show loading view
            self.control.visible = False
            parent_view.data_loading_view.visible = True
            parent_view.avatar_preview.visible = True
            parent_view.update()

            # ── DEK setup ──────────────────────────────────────────────────────
            parent_view.data_loading_view.set_status(_("Setting up encryption"))
            await self._setup_dek(data, password)

            # Load user preferences (uses DEK from AppShared automatically)
            try:
                self.app_shared.user_perference = load_user_preference(username)
            except CorruptedEncryptedConfigError as exc:
                if not await self._handle_corrupted_config(exc.file_path):
                    return  # user cancelled login
                # User chose to delete — continue with defaults
                self.app_shared.user_perference = UserPreference(
                    favourites={"files": {}, "directories": {}}
                )

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
                try:
                    await download_service.reload_tasks_for_user()
                except CorruptedEncryptedConfigError as exc:
                    if not await self._handle_corrupted_config(exc.file_path):
                        return  # user cancelled login
                    # User chose to delete — tasks stay empty, which is already the case

            self.control.clear_fields()
        finally:
            # Reset visibility for next login
            self.control.visible = True
            parent_view.data_loading_view.visible = False
            parent_view.data_loading_view.clear_status()

        self.control.page.run_task(self.control.page.push_route, "/home")

    async def _handle_corrupted_config(self, file_path: str) -> bool:
        """Show a dialog when an encrypted config file cannot be decrypted.

        Presents the user with two choices:
        - Delete the corrupted file and continue with default configuration.
        - Cancel the login, leaving the file intact.

        Args:
            file_path: Path to the unreadable encrypted file.

        Returns:
            ``True`` if the user chose to delete the file (caller should
            continue with defaults); ``False`` if the user cancelled (caller
            should abort login).
        """
        import asyncio

        decision_event = asyncio.Event()
        dialog = CorruptedConfigDialog(decision_event)
        self.control.page.show_dialog(dialog)
        await decision_event.wait()

        if dialog.user_confirmed:
            try:
                os.remove(file_path)
            except OSError:
                pass
            return True
        return False

    async def _setup_dek(self, login_data: dict, password: str) -> None:
        """Derive or generate the Data Encryption Key and store it in AppShared.

        If the server returned a ``preference_dek`` in the login response the
        encrypted DEK is decrypted with the password-derived KEK.  Otherwise a
        new DEK is generated, encrypted, uploaded to the server, and registered
        as the preference DEK.

        Failures are silently ignored so that a server that does not yet support
        the keyring feature does not prevent login.

        Args:
            login_data: The ``data`` dict from the successful login response.
            password:   The user's login password (used only for KEK derivation;
                        never stored).
        """
        if not password:
            return

        try:
            preference_dek = login_data.get("preference_dek")
            if preference_dek:
                # Server already has an encrypted DEK for this user – decrypt it.
                encrypted_dek_str: str = preference_dek["key_content"]
                self.app_shared.dek = decrypt_dek(encrypted_dek_str, password)
            else:
                # First login with keyring support: generate and upload the DEK.
                dek = generate_dek()
                encrypted_dek_str = encrypt_dek(dek, password)

                # Upload the encrypted DEK to the server's keyring.
                upload_response = await do_request(
                    "upload_user_key",
                    {"content": encrypted_dek_str, "label": "preference_dek"},
                    username=self.app_shared.username,
                    token=self.app_shared.token,
                )
                if upload_response.get("code") != 200:
                    return

                key_id: str = upload_response["data"]["id"]

                # Mark it as the preference DEK so future logins return it.
                set_pref_response = await do_request(
                    "set_user_preference_dek",
                    {"id": key_id},
                    username=self.app_shared.username,
                    token=self.app_shared.token,
                )
                if set_pref_response.get("code") != 200:
                    return

                self.app_shared.dek = dek
        except Exception:
            # Non-fatal: encryption is best-effort; login still succeeds.
            import logging
            logging.getLogger(__name__).warning(
                "DEK setup failed; configuration will not be encrypted this session",
                exc_info=True,
            )

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
                    self._complete_login, username, response["data"], password
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
