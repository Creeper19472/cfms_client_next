"""Dialog shown when an encrypted local config file cannot be decrypted."""

import asyncio
from typing import Optional

import flet as ft

from include.ui.controls.dialogs.base import AlertDialog
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class CorruptedConfigDialog(AlertDialog):
    """
    Warning dialog displayed when a local config file is encrypted with a key
    that is no longer available (e.g. after a server reset).

    The user can choose to delete the affected file(s) and continue with an
    empty configuration, or cancel the login entirely.

    Usage::

        event = asyncio.Event()
        dialog = CorruptedConfigDialog(event)
        page.show_dialog(dialog)
        await event.wait()
        if dialog.user_confirmed:
            # delete files and continue
        else:
            # abort login
    """

    def __init__(self, decision_event: asyncio.Event):
        super().__init__(
            modal=True,
            title=ft.Text(_("Configuration Cannot Be Decrypted")),
        )

        self.decision_event = decision_event
        self.user_confirmed: bool = False  # True = delete and continue

        self.content = ft.Column(
            [
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=40, color=ft.Colors.AMBER),
                ft.Text(
                    _(
                        "The local configuration file is encrypted with a key that is no longer "
                        "available on the server (the server may have been reset). "
                        "The file cannot be decrypted."
                    ),
                    size=14,
                ),
                ft.Text(
                    _(
                        "You can delete the unreadable file and continue with the default "
                        "configuration, or cancel the login to keep the file intact."
                    ),
                    size=14,
                    color=ft.Colors.with_opacity(0.7, ft.Colors.ON_SURFACE),
                ),
            ],
            tight=True,
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.delete_button = ft.FilledButton(
            _("Delete and Continue"),
            icon=ft.Icons.DELETE_OUTLINE,
            on_click=self._on_delete_click,
        )

        self.cancel_button = ft.TextButton(
            _("Cancel Login"),
            on_click=self._on_cancel_click,
        )

        self.actions = [
            self.cancel_button,
            self.delete_button,
        ]

    async def _on_delete_click(self, e: ft.Event[ft.Button]):
        self.user_confirmed = True
        self.close()
        self.decision_event.set()

    async def _on_cancel_click(self, e: ft.Event[ft.TextButton]):
        self.user_confirmed = False
        self.close()
        self.decision_event.set()
