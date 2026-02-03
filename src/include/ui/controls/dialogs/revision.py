"""Dialog for managing document revisions."""

from typing import TYPE_CHECKING
from datetime import datetime

import flet as ft

from include.classes.shared import AppShared
from include.controllers.dialogs.revision import RevisionDialogController
from include.ui.controls.dialogs.base import AlertDialog
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileListView

t = get_translation()
_ = t.gettext


class RevisionTile(ft.ListTile):
    """Custom tile for displaying a document revision."""

    def __init__(
        self,
        revision_id: int,
        parent_revision_id: int | None,
        created_time: float,
        is_current: bool,
        controller: "RevisionDialogController",
    ):
        self.revision_id = revision_id
        self.parent_revision_id = parent_revision_id
        self.created_time = created_time
        self.is_current = is_current
        self.controller = controller

        # Format creation time
        created_time_str = datetime.fromtimestamp(created_time).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Build title and subtitle
        title_text = _("Revision #{id}").format(id=revision_id)
        if is_current:
            title_text += _(" (Current)")

        subtitle_parts = [_("Created: {time}").format(time=created_time_str)]
        if parent_revision_id is not None:
            subtitle_parts.append(
                _("Parent: Revision #{id}").format(id=parent_revision_id)
            )

        # Icon based on current status
        icon = ft.Icons.HISTORY if not is_current else ft.Icons.CHECK_CIRCLE

        # Build action buttons
        action_buttons = []

        # View button (always available)
        view_button = ft.IconButton(
            icon=ft.Icons.VISIBILITY,
            tooltip=_("View/Download"),
            on_click=self.on_view_click,
        )
        action_buttons.append(view_button)

        # Set as current button (only for non-current revisions)
        if not is_current:
            set_current_button = ft.IconButton(
                icon=ft.Icons.PUBLISHED_WITH_CHANGES,
                tooltip=_("Set as Current"),
                on_click=self.on_set_current_click,
            )
            action_buttons.append(set_current_button)

            # Delete button (only for non-current revisions)
            delete_button = ft.IconButton(
                icon=ft.Icons.DELETE,
                tooltip=_("Delete"),
                on_click=self.on_delete_click,
            )
            action_buttons.append(delete_button)

        super().__init__(
            leading=ft.Icon(icon),
            title=title_text,
            subtitle=ft.Text("\n".join(subtitle_parts)),
            trailing=ft.Row(
                controls=action_buttons,
                expand=True,
                expand_loose=True,
                spacing=5,
                width=len(action_buttons)*40,
                alignment=ft.MainAxisAlignment.END,
            ),
            expand=True,
            expand_loose=True,
        )

    async def on_view_click(self, e: ft.Event[ft.IconButton]):
        """Handle view/download button click."""
        await self.controller.action_view_revision(self.revision_id, self.is_current)

    async def on_set_current_click(self, e: ft.Event[ft.IconButton]):
        """Handle set as current button click."""
        await self.controller.action_set_current_revision(self.revision_id)

    async def on_delete_click(self, e: ft.Event[ft.IconButton]):
        """Handle delete button click."""
        await self.controller.action_delete_revision(self.revision_id)


class RevisionDialog(AlertDialog):
    """Dialog for listing and managing document revisions."""

    def __init__(
        self,
        document_id: str,
        filename: str,
        parent_listview: "FileListView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.document_id = document_id
        self.filename = filename
        self.parent_listview = parent_listview
        self.app_shared = AppShared()
        self.controller = RevisionDialogController(self)

        self.title = ft.Text(
            _("View Revisions of {filename}").format(filename=filename)
        )
        self.expand = True
        self.expand_loose = True
        self.scrollable = True

        # Revisions list
        self.revisions_listview = ft.ListView(
            controls=[],
            spacing=5,
            expand=True,
            expand_loose=True,
            width=800
        )

        # Progress indicator
        self.progress_ring = ft.ProgressRing(visible=True)
        self.progress_text = ft.Text(_("Loading revisions..."), visible=True)

        # Error/info text
        self.info_text = ft.Text("", visible=False, color=ft.Colors.RED)

        # Refresh button
        self.refresh_button = ft.TextButton(
            _("Refresh"),
            icon=ft.Icons.REFRESH,
            on_click=self.on_refresh_click,
        )

        # Close button
        self.close_button = ft.TextButton(
            _("Close"),
            on_click=self.on_close_click,
        )

        # Layout
        self.content = ft.Column(
            controls=[
                ft.Row(
                    [
                        self.progress_ring,
                        self.progress_text,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                self.info_text,
                self.revisions_listview,
            ],
            expand=True,
            expand_loose=True,
            scroll=ft.ScrollMode.AUTO,
        )

        self.actions = [self.refresh_button, self.close_button]

    def did_mount(self):
        """Called when dialog is mounted to the page."""
        super().did_mount()
        # Automatically load revisions when dialog opens
        self.page.run_task(self.controller.action_load_revisions)

    async def on_refresh_click(self, e: ft.Event[ft.TextButton]):
        """Handle refresh button click."""
        await self.controller.action_load_revisions()

    async def on_close_click(self, e: ft.Event[ft.TextButton]):
        """Handle close button click."""
        self.close()

    def show_loading(self):
        """Show loading state."""
        self.progress_ring.visible = True
        self.progress_text.visible = True
        self.info_text.visible = False
        self.revisions_listview.controls.clear()
        self.refresh_button.disabled = True
        self.update()

    def hide_loading(self):
        """Hide loading state."""
        self.progress_ring.visible = False
        self.progress_text.visible = False
        self.refresh_button.disabled = False
        self.update()

    def display_revisions(self, revisions: list[dict]):
        """Display the list of revisions."""
        self.hide_loading()

        if not revisions:
            self.info_text.value = _("No revisions found.")
            self.info_text.visible = True
            self.update()
            return

        # Sort revisions by creation time (newest first)
        sorted_revisions = sorted(
            revisions, key=lambda r: r["created_time"], reverse=True
        )

        # Create tiles for each revision
        tiles = []
        for rev in sorted_revisions:
            tile = RevisionTile(
                revision_id=rev["id"],
                parent_revision_id=rev.get("parent_id"),
                created_time=rev["created_time"],
                is_current=rev["is_current"],
                controller=self.controller,
            )
            tiles.append(tile)

        self.revisions_listview.controls = tiles
        self.update()

    def show_error(self, message: str):
        """Display an error message."""
        self.hide_loading()
        self.info_text.value = message
        self.info_text.color = ft.Colors.RED
        self.info_text.visible = True
        self.update()
