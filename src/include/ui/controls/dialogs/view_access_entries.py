"""Dialog for viewing access entries for files and directories."""

from datetime import datetime
from typing import TYPE_CHECKING, Literal

import flet as ft
import flet_datatable2 as fdt

from include.classes.config import AppShared
from include.controllers.dialogs.view_access_entries import ViewAccessEntriesDialogController
from include.ui.controls.dialogs.base import AlertDialog
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileListView

t = get_translation()
_ = t.gettext


class ViewAccessEntriesDialog(AlertDialog):
    """Dialog for viewing access entries to files or directories."""

    def __init__(
        self,
        object_type: Literal["document", "directory"],
        object_id: str,
        parent_listview: "FileListView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = ViewAccessEntriesDialogController(self)
        self.object_type = object_type
        self.object_id = object_id
        self.parent_listview = parent_listview
        self.app_shared = AppShared()

        match self.object_type:
            case "document":
                self.object_display_name = _("File")
            case "directory":
                self.object_display_name = _("Directory")
            case _:
                raise ValueError(f"Invalid object type: {object_type}")

        self.modal = False
        self.title = ft.Text(
            _("View Access Entries for {display_name}").format(
                display_name=self.object_display_name
            )
        )

        # Progress indicator
        self.progress_ring = ft.ProgressRing(visible=False)

        # Data table for displaying access entries
        self.access_entries_table = fdt.DataTable2(
            columns=[
                fdt.DataColumn2(
                    label=ft.Text(_("ID")),
                    size=fdt.DataColumnSize.S,
                ),
                fdt.DataColumn2(
                    label=ft.Text(_("Entity Type")),
                    size=fdt.DataColumnSize.S,
                ),
                fdt.DataColumn2(
                    label=ft.Text(_("Entity Identifier")),
                    size=fdt.DataColumnSize.M,
                ),
                fdt.DataColumn2(
                    label=ft.Text(_("Target Type")),
                    size=fdt.DataColumnSize.S,
                ),
                fdt.DataColumn2(
                    label=ft.Text(_("Target Identifier")),
                    size=fdt.DataColumnSize.M,
                ),
                fdt.DataColumn2(
                    label=ft.Text(_("Access Type")),
                    size=fdt.DataColumnSize.S,
                ),
                fdt.DataColumn2(
                    label=ft.Text(_("Start Time")),
                    size=fdt.DataColumnSize.M,
                ),
                fdt.DataColumn2(
                    label=ft.Text(_("End Time")),
                    size=fdt.DataColumnSize.M,
                ),
                fdt.DataColumn2(
                    label=ft.Text(_("Actions")),
                    size=fdt.DataColumnSize.S,
                ),
            ],
            horizontal_margin=12,
            data_row_height=60,
            min_width=900,
        )

        # Refresh button
        self.refresh_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip=_("Refresh"),
            on_click=self.refresh_button_click,
        )

        # Close button
        self.close_button = ft.TextButton(
            _("Close"), on_click=self.close_button_click
        )

        # Build content layout
        self.content = ft.Column(
            controls=[
                ft.Row(
                    [
                        ft.Text(
                            _("Access entries for this {type}").format(
                                type=self.object_display_name.lower()
                            ),
                            size=14,
                        ),
                        self.refresh_button,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(),
                self.progress_ring,
                ft.Container(
                    content=self.access_entries_table,
                    expand=True,
                ),
            ],
            width=900,
            height=500,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

        self.actions = [self.close_button]

    def did_mount(self):
        """Called when dialog is mounted to the page."""
        super().did_mount()
        # Automatically fetch access entries when dialog opens
        self.disable_interactions()
        self.page.run_task(self.controller.action_fetch_access_entries)

    def disable_interactions(self):
        """Disable all interactive elements during processing."""
        self.refresh_button.disabled = True
        self.close_button.disabled = True
        self.progress_ring.visible = True
        self.modal = True
        # Disable all delete buttons in the table
        for row in self.access_entries_table.rows:
            for cell in row.cells:
                if cell.content and isinstance(cell.content, ft.IconButton):
                    cell.content.disabled = True
        self.update()

    def enable_interactions(self):
        """Re-enable all interactive elements after processing."""
        self.refresh_button.disabled = False
        self.close_button.disabled = False
        self.progress_ring.visible = False
        self.modal = False
        # Re-enable all delete buttons in the table
        for row in self.access_entries_table.rows:
            for cell in row.cells:
                if cell.content and isinstance(cell.content, ft.IconButton):
                    cell.content.disabled = False
        self.update()

    def update_table(self, entries: list[dict]):
        """Update the data table with the fetched access entries."""
        self.access_entries_table.rows.clear()

        for entry in entries:
            # Format timestamps with error handling
            try:
                start_time_str = datetime.fromtimestamp(entry["start_time"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            except (ValueError, OSError, KeyError):
                start_time_str = _("Invalid date")
            
            # Check for end_time properly (None check to handle timestamp 0)
            if entry.get("end_time") is not None:
                try:
                    end_time_str = datetime.fromtimestamp(entry["end_time"]).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                except (ValueError, OSError, KeyError):
                    end_time_str = _("Invalid date")
            else:
                end_time_str = _("No expiry")

            # Create delete button for this entry
            entry_id = entry.get("id")
            delete_button = ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_color=ft.Colors.RED_400,
                tooltip=_("Revoke"),
                data=entry_id,
                on_click=self.delete_button_click,
            )

            self.access_entries_table.rows.append(
                fdt.DataRow2(
                    cells=[
                        ft.DataCell(ft.Text(str(entry.get("id", "")))),
                        ft.DataCell(ft.Text(entry.get("entity_type", ""))),
                        ft.DataCell(ft.Text(entry.get("entity_identifier", ""))),
                        ft.DataCell(ft.Text(entry.get("target_type", ""))),
                        ft.DataCell(ft.Text(entry.get("target_identifier", ""))),
                        ft.DataCell(ft.Text(entry.get("access_type", ""))),
                        ft.DataCell(ft.Text(start_time_str)),
                        ft.DataCell(ft.Text(end_time_str)),
                        ft.DataCell(delete_button),
                    ]
                )
            )

        self.access_entries_table.update()

    async def refresh_button_click(self, event):
        """Handle refresh button click."""
        self.disable_interactions()
        self.page.run_task(self.controller.action_fetch_access_entries)

    async def delete_button_click(self, event: ft.Event[ft.IconButton]):
        """Handle delete button click."""
        entry_id = event.control.data
        if entry_id is not None:
            self.disable_interactions()
            self.page.run_task(self.controller.action_revoke_access, entry_id)

    async def close_button_click(self, event: ft.Event[ft.TextButton]):
        """Handle close button click."""
        self.close()
