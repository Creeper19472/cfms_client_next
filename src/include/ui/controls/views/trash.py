"""Trash/Recycle Bin view for listing and managing deleted items."""

from datetime import datetime
from typing import TYPE_CHECKING

import flet as ft
from flet_material_symbols import Symbols

from include.classes.shared import AppShared
from include.controllers.trash.view import TrashViewController
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.models.trash import TrashModel

t = get_translation()
_ = t.gettext


class TrashItemTile(ft.ListTile):
    """A list tile representing a single deleted item (document or directory)."""

    def __init__(
        self,
        item_id: str,
        item_name: str,
        item_type: str,  # "document" or "directory"
        created_time: float | None,
        on_restore: ft.ControlEventHandler[ft.IconButton] | None = None,
        on_purge: ft.ControlEventHandler[ft.IconButton] | None = None,
        ref: ft.Ref | None = None,
    ):
        self.item_id = item_id
        self.item_name = item_name
        self.item_type = item_type
        self.created_time = created_time

        icon = Symbols.DESCRIPTION if item_type == "document" else Symbols.FOLDER

        subtitle_text = _("ID: {item_id}").format(item_id=item_id)
        if created_time is not None:
            subtitle_text += "\n" + _("Created at: {created_at}").format(
                created_at=datetime.fromtimestamp(created_time).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

        restore_button = ft.IconButton(
            icon=Symbols.RESTORE,
            tooltip=_("Restore"),
            on_click=on_restore,
            disabled=on_restore is None,
        )
        purge_button = ft.IconButton(
            icon=Symbols.DELETE_FOREVER,
            tooltip=_("Permanently Delete"),
            icon_color=ft.Colors.RED_400,
            on_click=on_purge,
            disabled=on_restore is None,
        )

        super().__init__(
            leading=ft.Icon(icon, color=ft.Colors.GREY_500),
            title=ft.Text(
                item_name,
                color=ft.Colors.GREY_400,
                style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH),
            ),
            subtitle=ft.Text(subtitle_text, color=ft.Colors.GREY_600),
            trailing=ft.Row(
                controls=[restore_button, purge_button],
                tight=True,
                spacing=0,
            ),
            is_three_line=True,
            ref=ref,
        )


class RestoreDialog(ft.AlertDialog):
    """Dialog for restoring a deleted item with optional rename/move."""

    def __init__(
        self,
        item_id: str,
        item_name: str,
        item_type: str,  # "document" or "directory"
        on_confirm,
    ):
        self.item_id = item_id
        self.item_name = item_name
        self.item_type = item_type
        self.on_confirm = on_confirm

        self.new_name_field = ft.TextField(
            label=_("Restore with name"),
            hint_text=_("Leave blank to keep original"),
            expand=True,
        )

        self.confirm_button = ft.TextButton(
            _("Restore"),
            on_click=self._on_confirm_click,
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"),
            on_click=self._on_cancel_click,
        )

        super().__init__(
            title=ft.Text(_("Restore Item")),
            content=ft.Column(
                controls=[
                    ft.Text(
                        _('Restore "{name}"?').format(name=item_name),
                        size=15,
                    ),
                    self.new_name_field,
                ],
                width=400,
                tight=True,
            ),
            actions=[self.confirm_button, self.cancel_button],
            scrollable=True,
        )

    async def _on_confirm_click(self, event):
        new_name = (
            self.new_name_field.value.strip() if self.new_name_field.value else None
        )
        self.open = False
        self.update()
        # Pass item_type back through the callback to ensure reliability
        await self.on_confirm(self.item_id, self.item_type, new_name)

    async def _on_cancel_click(self, event):
        self.open = False
        self.update()


class PurgeConfirmDialog(ft.AlertDialog):
    """Dialog to confirm permanent deletion of an item."""

    def __init__(self, item_name: str, on_confirm):
        self.on_confirm = on_confirm

        self.confirm_button = ft.TextButton(
            _("Delete Permanently"),
            style=ft.ButtonStyle(color=ft.Colors.RED_400),
            on_click=self._on_confirm_click,
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"),
            on_click=self._on_cancel_click,
        )

        super().__init__(
            title=ft.Text(_("Permanently Delete")),
            content=ft.Column(
                controls=[
                    ft.Text(
                        _(
                            'Are you sure you want to permanently delete "{name}"?'
                        ).format(name=item_name),
                        size=15,
                    ),
                    ft.Text(
                        _("This action cannot be undone."),
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400,
                    ),
                ],
                width=400,
                tight=True,
            ),
            actions=[self.confirm_button, self.cancel_button],
            scrollable=True,
        )

    async def _on_confirm_click(self, event):
        self.open = False
        self.update()
        await self.on_confirm()

    async def _on_cancel_click(self, event):
        self.open = False
        self.update()


class TrashView(ft.Container):
    """
    Trash/Recycle Bin view that lists deleted items for a specified directory.
    """

    def __init__(
        self,
        parent_model: "TrashModel",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.parent_model = parent_model
        self.app_shared = AppShared()
        self.controller = TrashViewController(self)

        self.current_folder_id: str = "/"

        self.margin = 10
        self.padding = 10
        self.expand = True
        self.alignment = ft.Alignment.TOP_CENTER

        self.folder_id_field = ft.TextField(
            label=_("Folder ID (use / for root)"),
            value="/",
            expand=True,
            on_submit=self._on_folder_id_submit,
        )
        self.browse_button = ft.IconButton(
            icon=Symbols.SEARCH,
            tooltip=_("Load deleted items"),
            on_click=self._on_browse_click,
        )

        self.progress_ring = ft.ProgressRing(visible=False)
        self.empty_label = ft.Text(
            _("No deleted items found in this directory."),
            color=ft.Colors.GREY_500,
            visible=False,
            size=14,
        )

        self.items_listview = ft.ListView(
            expand=True,
            spacing=2,
        )

        self.content = ft.Column(
            controls=[
                ft.Text(
                    _("Recycle Bin"),
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    _(
                        "View and manage deleted items. "
                        "Restore items to bring them back, or permanently delete them."
                    ),
                    color=ft.Colors.GREY_500,
                    size=14,
                ),
                ft.Divider(),
                ft.Row(
                    controls=[
                        self.folder_id_field,
                        self.browse_button,
                    ],
                    spacing=8,
                ),
                ft.Divider(),
                self.progress_ring,
                self.empty_label,
                self.items_listview,
            ],
            expand=True,
            spacing=8,
        )

    def did_mount(self):
        super().did_mount()

    def show_loading(self):
        self.progress_ring.visible = True
        self.empty_label.visible = False
        self.items_listview.controls.clear()
        self.update()

    def hide_loading(self):
        self.progress_ring.visible = False
        self.update()

    def update_items(self, folders: list[dict], documents: list[dict]):
        self.progress_ring.visible = False
        self.items_listview.controls.clear()

        if not folders and not documents:
            self.empty_label.visible = True
            self.update()
            return

        self.empty_label.visible = False
        user_perms = set(self.app_shared.user_permissions)
        can_restore = "restore" in user_perms
        can_purge = "purge" in user_perms

        if folders:
            self.items_listview.controls.append(
                ft.Text(
                    _("Directories ({count})").format(count=len(folders)),
                    weight=ft.FontWeight.W_600,
                    size=14,
                    color=ft.Colors.BLUE_200,
                )
            )
            for folder in folders:
                folder_id = folder["id"]
                folder_name = folder["name"]
                created_time = folder.get("created_time")

                tile = TrashItemTile(
                    item_id=folder_id,
                    item_name=folder_name,
                    item_type="directory",
                    created_time=created_time,
                    on_restore=(
                        self._make_restore_handler("directory", folder_id, folder_name)
                        if can_restore
                        else None
                    ),
                    on_purge=(
                        self._make_purge_handler("directory", folder_id, folder_name)
                        if can_purge
                        else None
                    ),
                )
                self.items_listview.controls.append(tile)

        if folders and documents:
            self.items_listview.controls.append(ft.Divider())

        if documents:
            self.items_listview.controls.append(
                ft.Text(
                    _("Documents ({count})").format(count=len(documents)),
                    weight=ft.FontWeight.W_600,
                    size=14,
                    color=ft.Colors.BLUE_200,
                )
            )
            for doc in documents:
                doc_id = doc["id"]
                doc_title = doc["title"]
                created_time = doc.get("created_time")

                tile = TrashItemTile(
                    item_id=doc_id,
                    item_name=doc_title,
                    item_type="document",
                    created_time=created_time,
                    on_restore=(
                        self._make_restore_handler("document", doc_id, doc_title)
                        if can_restore
                        else None
                    ),
                    on_purge=(
                        self._make_purge_handler("document", doc_id, doc_title)
                        if can_purge
                        else None
                    ),
                )
                self.items_listview.controls.append(tile)

        self.update()

    def _make_restore_handler(self, item_type: str, item_id: str, item_name: str):
        async def handler(event: ft.Event):
            dialog = RestoreDialog(
                item_id=item_id,
                item_name=item_name,
                item_type=item_type,
                on_confirm=self._on_restore_confirm,
            )
            self.page.show_dialog(dialog)

        return handler

    async def _on_restore_confirm(
        self, item_id: str, item_type: str, new_name: str | None
    ):
        """Execute restore after user confirms in the dialog."""
        if item_type == "document":
            await self.controller.action_restore_document(item_id, new_title=new_name)
        elif item_type == "directory":
            await self.controller.action_restore_directory(item_id, new_name=new_name)

    def _make_purge_handler(self, item_type: str, item_id: str, item_name: str):
        async def handler(event: ft.Event):
            async def on_confirm():
                if item_type == "document":
                    await self.controller.action_purge_document(item_id)
                else:
                    await self.controller.action_purge_directory(item_id)

            dialog = PurgeConfirmDialog(
                item_name=item_name,
                on_confirm=on_confirm,
            )
            self.page.show_dialog(dialog)

        return handler

    async def _on_folder_id_submit(self, event: ft.Event[ft.TextField]):
        await self._load_folder()

    async def _on_browse_click(self, event: ft.Event[ft.IconButton]):
        await self._load_folder()

    async def _load_folder(self):
        folder_id = (self.folder_id_field.value or "/").strip()
        if not folder_id:
            folder_id = "/"
        self.current_folder_id = folder_id
        await self.controller.load_deleted_items(folder_id)
