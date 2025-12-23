"""Two-Factor Authentication verification dialog."""

import flet as ft

from include.ui.controls.dialogs.base import AlertDialog
from include.ui.util.notifications import send_error
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class TwoFactorVerifyDialog(AlertDialog):
    """
    Dialog for verifying 2FA code during login.

    This dialog prompts the user to enter their TOTP code
    when logging in with 2FA enabled.
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
        )

        self.on_verify_callback = on_verify_callback
        self.on_cancel_callback = on_cancel_callback

        # Code input field
        self.code_field = ft.TextField(
            label=_("Verification Code"),
            hint_text=_("Enter 6-digit code"),
            max_length=6,
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
            on_submit=self._on_verify_click,
            expand=True,
            expand_loose=True,
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

        self.loading_ring = ft.ProgressRing(visible=False, width=20, height=20)

        # Dialog content
        self.content = ft.Column(
            [
                ft.Text(
                    _("Enter the 6-digit code from your authenticator app"),
                    size=14,
                ),
                self.code_field,
                ft.Row(
                    [self.loading_ring],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            tight=True,
            spacing=15,
        )

        self.actions = [
            self.cancel_button,
            self.verify_button,
        ]

    def disable_interactions(self):
        """Disable all interactive elements."""
        self.code_field.disabled = True
        self.verify_button.disabled = True
        self.cancel_button.disabled = True
        self.loading_ring.visible = True
        self.update()

    def enable_interactions(self):
        """Enable all interactive elements."""
        self.code_field.disabled = False
        self.verify_button.disabled = False
        self.cancel_button.disabled = False
        self.loading_ring.visible = False
        self.update()

    async def _on_verify_click(self, e):
        """Handle verify button click."""
        code = self.code_field.value

        if not code or len(code) != 6:
            self.code_field.error = _("Please enter a 6-digit code")
            self.update()
            return

        self.disable_interactions()

        if self.on_verify_callback:
            success = await self.on_verify_callback(code)
            if success:
                self.close()
            else:
                self.enable_interactions()
                self.code_field.value = ""
                self.code_field.error = _("Invalid verification code")
                self.update()
        else:
            self.enable_interactions()

    async def _on_cancel_click(self, e):
        """Handle cancel button click."""
        if self.on_cancel_callback:
            await self.on_cancel_callback()
        self.close()
