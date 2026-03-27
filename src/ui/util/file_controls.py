from typing import TYPE_CHECKING

import flet as ft
from flet_material_symbols import Symbols

from include.ui.controls.contextmenus.explorer import DirectoryContextMenu, FileContextMenu
from include.ui.util.path import get_directory

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileListView

# __all__ = ["get_directory"]


def update_file_controls(
    view: "FileListView",
    folders: list[dict],
    documents: list[dict],
    parent_id: str | None = None,
):
    view.controls = []  # reset

    async def parent_button_click(event: ft.Event[ft.ListTile]):
        view.parent_manager.current_directory_id = (
            None if parent_id == "/" else parent_id
        )
        if await get_directory(view.parent_manager.current_directory_id, view=view):
            view.parent_manager.indicator.back()

    if (
        parent_id != None
        and view.parent_manager.current_directory_id
        != view.parent_manager.root_directory_id
    ):
        # print("parent_id: ", parent_id)
        view.controls = [
            ft.ListTile(
                leading=ft.Icon(Symbols.ARROW_BACK),
                title=ft.Text("<...>"),
                subtitle=ft.Text(_("Parent directory")),
                on_click=parent_button_click,
            )
        ]

    # Check if in selection mode
    if view.selection_mode:
        # In selection mode, create tiles directly without context menus
        from include.ui.controls.components.explorer.tile import DirectoryTile, FileTile
        
        def on_directory_selection_changed(dir_id: str, is_selected: bool):
            """Handle directory selection change."""
            if is_selected:
                view.selected_directory_ids.add(dir_id)
            else:
                view.selected_directory_ids.discard(dir_id)
            # Update selection toolbar count
            count = view.get_selected_count()
            view.parent_manager.selection_toolbar.update_selection_count(count)
        
        def on_file_selection_changed(file_id: str, is_selected: bool):
            """Handle file selection change."""
            if is_selected:
                view.selected_file_ids.add(file_id)
            else:
                view.selected_file_ids.discard(file_id)
            # Update selection toolbar count
            count = view.get_selected_count()
            view.parent_manager.selection_toolbar.update_selection_count(count)
        
        view.controls.extend(
            [
                DirectoryTile(
                    dir_name=folder["name"],
                    directory_id=folder["id"],
                    created_at=folder["created_time"],
                    selection_mode=True,
                    is_selected=folder["id"] in view.selected_directory_ids,
                    on_selection_changed=on_directory_selection_changed,
                )
                for folder in folders
            ]
        )
        view.controls.extend(
            [
                FileTile(
                    filename=document["title"],
                    file_id=document["id"],
                    size=document["size"],
                    last_modified=document["last_modified"],
                    selection_mode=True,
                    is_selected=document["id"] in view.selected_file_ids,
                    on_selection_changed=on_file_selection_changed,
                )
                for document in documents
            ]
        )
    else:
        # Normal mode with context menus
        view.controls.extend(
            [
                DirectoryContextMenu(
                    parent_listview=view,
                    directory_id=folder["id"],
                    dir_name=folder["name"],
                    created_at=folder["created_time"],
                )
                for folder in folders
            ]
        )
        view.controls.extend(
            [
                FileContextMenu(
                    parent_listview=view,
                    file_id=document["id"],
                    filename=document["title"],
                    size=document["size"],
                    last_modified=document["last_modified"],
                )
                for document in documents
            ]
        )
    view.update()
