"""Dialog for managing user avatar settings."""

from typing import TYPE_CHECKING

import flet as ft

from include.controllers.dialogs.avatar_settings import AvatarSettingsDialogController
from include.ui.controls.dialogs.base import AlertDialog
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.components.account import AccountBadge

t = get_translation()
_ = t.gettext


class AvatarSettingsDialog(AlertDialog):
    """Dialog for setting user avatar from document ID."""

    def __init__(
        self,
        account_badge: "AccountBadge",
        ref: ft.Ref | None = None,
        visible: bool = True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.account_badge = account_badge
        self.controller = AvatarSettingsDialogController(self)

        self.modal = False
        self.scrollable = True  # Make dialog scrollable
        self.title = ft.Text(_("Set Avatar"))

        # Progress ring for loading state
        self.progress_ring = ft.ProgressRing(visible=False)

        # Browse button - positioned ABOVE the input field
        self.browse_button = ft.Button(
            _("Browse Documents"),
            on_click=self.browse_documents_click,
            icon=ft.Icons.FOLDER_OPEN,
        )

        # Document ID input field
        self.document_id_field = ft.TextField(
            label=_("Document ID"),
            hint_text=_("Enter the ID of an image document"),
            on_submit=self.set_avatar_click,
            expand=True,
        )

        # Action buttons
        self.set_button = ft.TextButton(
            _("Set Avatar"),
            on_click=self.set_avatar_click,
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"),
            on_click=self.cancel_button_click,
        )

        # Error message text (hidden by default)
        self.error_text = ft.Text(
            color=ft.Colors.ERROR,
            visible=False,
        )

        self.content = ft.Column(
            controls=[
                ft.Text(_("Choose an image document to use as your avatar")),
                self.browse_button,  # Browse button is now ABOVE the input field
                ft.Text(_("Or enter document ID manually:")),
                self.document_id_field,
                self.error_text,
            ],
            width=400,
            spacing=10,
            tight=True,
        )

        self.actions = [
            self.progress_ring,
            self.set_button,
            self.cancel_button,
        ]

    def disable_interactions(self):
        """Disable all interactive elements during async operations."""
        self.document_id_field.disabled = True
        self.browse_button.disabled = True
        self.set_button.visible = False
        self.cancel_button.disabled = True
        self.progress_ring.visible = True
        self.error_text.visible = False
        self.modal = True

    def enable_interactions(self):
        """Re-enable interactive elements after async operations."""
        self.document_id_field.disabled = False
        self.browse_button.disabled = False
        self.set_button.visible = True
        self.cancel_button.disabled = False
        self.progress_ring.visible = False
        self.modal = False

    def show_error(self, message: str):
        """Display an error message in the dialog."""
        self.error_text.value = message
        self.error_text.visible = True
        self.update()

    async def browse_documents_click(self, event: ft.Event[ft.Button]):
        """Handle browse documents button click."""
        from include.ui.controls.dialogs.document_selector import DocumentSelectorDialog
        
        # Create and show document selector dialog
        def on_document_selected(document_id: str, document_name: str):
            """Callback when user selects a document."""
            self.document_id_field.value = document_id
            self.document_id_field.update()
        
        selector_dialog = DocumentSelectorDialog(on_select_callback=on_document_selected)
        self.page.show_dialog(selector_dialog)

    async def set_avatar_click(
        self, event: ft.Event[ft.TextButton] | ft.Event[ft.TextField]
    ):
        """Handle set avatar button click."""
        yield self.disable_interactions()

        # Validate input
        document_id = self.document_id_field.value
        if not document_id or not document_id.strip():
            self.document_id_field.error = _("Document ID cannot be empty")
            yield self.enable_interactions()
            return

        document_id = document_id.strip()
        self.document_id_field.error = None

        # Call controller to set avatar
        self.page.run_task(self.controller.action_set_avatar, document_id)

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        """Handle cancel button click."""
        self.close()
