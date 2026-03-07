"""Two-Factor Authentication verification dialog."""

import flet as ft
from flet_material_symbols import Symbols

from include.ui.controls.dialogs.base import AlertDialog
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

DESCRIPTION_ENTER_CODE = _("Enter the 6-digit code from your authenticator app")
DESCRIPTION_ENTER_RECOVERY = _("Enter one of your recovery codes")
DESCRIPTION_USE_CODE_INSTEAD = _("Use authenticator code instead")
DESCRIPTION_USE_RECOVERY_INSTEAD = _("Use recovery code instead")


class TwoFactorVerifyDialog(AlertDialog):
    """
    Dialog for verifying 2FA code during login.

    This dialog prompts the user to enter their TOTP code or recovery code
    when logging in with 2FA enabled. Users can toggle between entering
    a 6-digit authenticator code or a recovery code.
    """

    def __init__(self, on_verify_callback=None, on_cancel_callback=None):
        """
        Initialize the 2FA verification dialog.

        Args:
            on_verify_callback: Async function to call when user submits code
            on_cancel_callback: Async function to call when user cancels
        """
        super().__init__(
            modal=True,
            scrollable=True,
            title=ft.Text(_("Two-Factor Authentication")),
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.on_verify_callback = on_verify_callback
        self.on_cancel_callback = on_cancel_callback
        self.use_recovery_code = False  # Track which input mode is active

        # Code input field (for TOTP)
        self.code_field = ft.TextField(
            label=_("Verification Code"),
            hint_text=_("Enter 6-digit code"),
            max_length=6,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(r"^[0-9]*$"),
            autofocus=True,
            on_submit=self._on_verify_click,
            expand=True,
            expand_loose=True,
            width=450,
        )

        # Recovery code input field
        self.recovery_code_field = ft.TextField(
            label=_("Recovery Code"),
            hint_text=_("Enter recovery code"),
            max_length=20,
            keyboard_type=ft.KeyboardType.TEXT,
            autofocus=False,
            on_submit=self._on_verify_click,
            expand=True,
            expand_loose=True,
            visible=False,
            width=450,
        )

        # Buttons
        self.verify_button = ft.TextButton(
            _("Verify"),
            on_click=self._on_verify_click,
        )

        self.cancel_button = ft.TextButton(
            _("Cancel"),
            on_click=self._on_cancel_click,
        )

        # Toggle link to switch between code and recovery code
        self.toggle_link = ft.TextButton(
            DESCRIPTION_USE_RECOVERY_INSTEAD,
            icon=Symbols.SETTINGS_BACKUP_RESTORE,
            on_click=self._on_toggle_input,
        )

        self.loading_ring = ft.ProgressRing(visible=False, width=20, height=20)

        # Dialog content with description text
        self.description_text = ft.Text(
            DESCRIPTION_ENTER_CODE,
            size=14,
        )

        # Dialog content
        self.content = ft.Column(
            [
                self.description_text,
                self.code_field,
                self.recovery_code_field,
                ft.Row(
                    [self.loading_ring],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            tight=True,
            spacing=15,
        )

        self.actions = [
            self.toggle_link,
            ft.Row(
                [
                    self.cancel_button,
                    self.verify_button,
                ],
                tight=True,  # Keep the action buttons as a compact group so the dialog's actions_alignment controls their overall placement
            ),
        ]

    def disable_interactions(self):
        """Disable all interactive elements."""
        self.code_field.disabled = True
        self.recovery_code_field.disabled = True
        self.verify_button.disabled = True
        self.cancel_button.disabled = True
        self.toggle_link.disabled = True
        self.loading_ring.visible = True
        self.update()

    def enable_interactions(self):
        """Enable all interactive elements."""
        self.code_field.disabled = False
        self.recovery_code_field.disabled = False
        self.verify_button.disabled = False
        self.cancel_button.disabled = False
        self.toggle_link.disabled = False
        self.loading_ring.visible = False
        self.update()

    async def _on_toggle_input(self, event: ft.Event[ft.TextButton]):
        """Toggle between verification code and recovery code input."""
        assert type(self.page) == ft.Page
        self.use_recovery_code = not self.use_recovery_code

        if self.use_recovery_code:
            # Switch to recovery code mode
            self.code_field.visible = False
            self.recovery_code_field.visible = True
            self.description_text.value = DESCRIPTION_ENTER_RECOVERY
            self.toggle_link.content = DESCRIPTION_USE_CODE_INSTEAD
            self.toggle_link.icon = Symbols.PASSWORD
            self.page.run_task(self.recovery_code_field.focus)
        else:
            # Switch to verification code mode
            self.code_field.visible = True
            self.recovery_code_field.visible = False
            self.description_text.value = DESCRIPTION_ENTER_CODE
            self.toggle_link.content = DESCRIPTION_USE_RECOVERY_INSTEAD
            self.toggle_link.icon = Symbols.SETTINGS_BACKUP_RESTORE
            self.page.run_task(self.code_field.focus)

        # Clear any previous errors
        self.code_field.error = None
        self.recovery_code_field.error = None

    async def _on_verify_click(
        self, event: ft.Event[ft.TextButton] | ft.Event[ft.TextField]
    ):
        """Handle verify button click."""
        if self.use_recovery_code:
            # Validate recovery code
            code = self.recovery_code_field.value
            if not code or len(code.strip()) == 0:
                self.recovery_code_field.error = _("Please enter a recovery code")
                self.update()
                return
        else:
            # Validate 6-digit verification code
            code = self.code_field.value
            if not code or len(code) != 6:
                self.code_field.error = _("Please enter a 6-digit code")
                self.update()
                return

        # Clear errors
        self.code_field.error = None
        self.recovery_code_field.error = None

        self.disable_interactions()

        if self.on_verify_callback:
            success = await self.on_verify_callback(code, self.use_recovery_code)
            if success:
                self.close()
            else:
                self.enable_interactions()
                if self.use_recovery_code:
                    self.recovery_code_field.value = ""
                    self.recovery_code_field.error = _("Invalid recovery code")
                else:
                    self.code_field.value = ""
                    self.code_field.error = _("Invalid verification code")
                self.update()
        else:
            self.enable_interactions()

    async def _on_cancel_click(self, event: ft.Event[ft.TextButton]):
        """Handle cancel button click."""
        if self.on_cancel_callback:
            await self.on_cancel_callback()
        self.close()
