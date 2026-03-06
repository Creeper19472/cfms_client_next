"""Progress dialog shown while a CA certificate store update is running."""

from __future__ import annotations

import flet as ft

from include.ui.controls.dialogs.base import AlertDialog
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

__all__ = ["CACertUpdateProgressDialog"]


class CACertUpdateProgressDialog(AlertDialog):
    """Modal dialog that shows a progress ring while the CA cert update runs.

    Usage::

        dialog = CACertUpdateProgressDialog()
        self.page.show_dialog(dialog)
        try:
            result = await service.update_now()
        finally:
            dialog.close()
    """

    def __init__(self) -> None:
        self._status_text = ft.Text(
            _("Connecting to certificate repository…"),
            size=13,
            text_align=ft.TextAlign.CENTER,
        )
        super().__init__(
            title=ft.Text(_("Updating CA Certificates")),
            content=ft.Column(
                controls=[
                    ft.ProgressRing(width=48, height=48, stroke_width=4),
                    self._status_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                tight=True,
            ),
            modal=True,
        )

    def set_status(self, message: str) -> None:
        """Update the status message displayed below the progress ring."""
        self._status_text.value = message
        self.update()
