"""Password confirmation dialog."""

import flet as ft

from include.ui.controls.dialogs.base import AlertDialog
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class PasswordConfirmDialog(AlertDialog):
    """
    Dialog for confirming user password.
    
    This dialog prompts the user to enter their password for security-sensitive operations.
    """
    
    def __init__(self, on_confirm_callback=None, on_cancel_callback=None, title=None, message=None):
        """
        Initialize the password confirmation dialog.
        
        Args:
            on_confirm_callback: Async function to call when user submits password
            on_cancel_callback: Async function to call when user cancels
            title: Optional custom title for the dialog
            message: Optional custom message to display
        """
        super().__init__(
            modal=True,
            scrollable=True,
            title=ft.Text(title or _("Confirm Password")),
        )
        
        self.on_confirm_callback = on_confirm_callback
        self.on_cancel_callback = on_cancel_callback
        
        # Password input field
        self.password_field = ft.TextField(
            label=_("Password"),
            password=True,
            can_reveal_password=True,
            autofocus=True,
            on_submit=self._on_confirm_click,
            expand=True,
        )
        
        # Buttons
        self.confirm_button = ft.TextButton(
            _("Confirm"),
            on_click=self._on_confirm_click,
        )
        
        self.cancel_button = ft.TextButton(
            _("Cancel"),
            on_click=self._on_cancel_click,
        )
        
        self.loading_ring = ft.ProgressRing(visible=False, width=20, height=20)
        
        # Dialog content
        content_controls = []
        
        if message:
            content_controls.append(
                ft.Text(
                    message,
                    size=14,
                )
            )
        
        content_controls.extend([
            self.password_field,
            ft.Row(
                [self.loading_ring],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ])
        
        self.content = ft.Column(
            content_controls,
            tight=True,
            spacing=15,
        )
        
        self.actions = [
            self.cancel_button,
            self.confirm_button,
        ]
    
    def disable_interactions(self):
        """Disable all interactive elements."""
        self.password_field.disabled = True
        self.confirm_button.disabled = True
        self.cancel_button.disabled = True
        self.loading_ring.visible = True
        self.update()
    
    def enable_interactions(self):
        """Enable all interactive elements."""
        self.password_field.disabled = False
        self.confirm_button.disabled = False
        self.cancel_button.disabled = False
        self.loading_ring.visible = False
        self.update()
    
    async def _on_confirm_click(self, e):
        """Handle confirm button click."""
        password = self.password_field.value
        
        if not password:
            self.password_field.error = _("Password cannot be empty")
            self.update()
            return
        
        self.disable_interactions()
        
        if self.on_confirm_callback:
            success = await self.on_confirm_callback(password)
            if success:
                self.close()
            else:
                self.enable_interactions()
                self.password_field.value = ""
                self.password_field.error = _("Invalid password")
                self.update()
        else:
            self.enable_interactions()
    
    async def _on_cancel_click(self, e):
        """Handle cancel button click."""
        if self.on_cancel_callback:
            await self.on_cancel_callback()
        self.close()
