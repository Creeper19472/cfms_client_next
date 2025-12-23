"""Backup codes display dialog."""

import flet as ft

from include.ui.controls.dialogs.base import AlertDialog
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class BackupCodesDialog(AlertDialog):
    """
    Dialog for displaying 2FA backup codes.
    
    Shows backup codes after 2FA is successfully enabled,
    prompting the user to save them securely.
    """
    
    def __init__(self, backup_codes: list[str], on_close_callback=None):
        """
        Initialize the backup codes dialog.
        
        Args:
            backup_codes: List of backup recovery codes
            on_close_callback: Async function to call when user closes the dialog
        """
        super().__init__(
            modal=True,
            scrollable=True,
            title=ft.Text(_("Save Your Backup Codes")),
        )
        
        self.backup_codes = backup_codes
        self.on_close_callback = on_close_callback
        
        # Create backup codes display
        codes_text = "\n".join(backup_codes)
        
        self.codes_field = ft.TextField(
            value=codes_text,
            multiline=True,
            read_only=True,
            min_lines=len(backup_codes),
            max_lines=len(backup_codes),
            text_size=14,
            border_color=ft.Colors.SECONDARY,
            expand=True,
            expand_loose=True,
        )
        
        # Close button
        self.close_button = ft.TextButton(
            _("I Have Saved My Codes"),
            on_click=self._on_close_click,
        )
        
        # Dialog content
        self.content = ft.Column(
            [
                ft.Text(
                    _("Two-Factor Authentication has been enabled successfully!"),
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREEN,
                ),
                ft.Divider(),
                ft.Text(
                    _("Save these backup codes in a secure location. "
                      "You can use them to access your account if you lose access to your authenticator app."),
                    size=14,
                ),
                ft.Text(
                    _("Each code can only be used once."),
                    size=12,
                    italic=True,
                    color=ft.Colors.ORANGE,
                ),
                ft.Container(height=10),
                self.codes_field,
                ft.Container(height=10),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE, size=20),
                        ft.Text(
                            _("Store these codes safely - they won't be shown again!"),
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ORANGE,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            tight=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
        
        self.actions = [
            self.close_button,
        ]
        
        self.actions_alignment = ft.MainAxisAlignment.CENTER
    
    async def _on_close_click(self, e):
        """Handle close button click."""
        if self.on_close_callback:
            await self.on_close_callback()
        self.close()
