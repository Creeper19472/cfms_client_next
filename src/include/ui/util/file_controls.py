from typing import TYPE_CHECKING
from datetime import datetime
import gettext
import flet as ft

from include.ui.controls.rightmenu.explorer import (
    DocumentRightMenuDialog,
    DirectoryRightMenuDialog,
)
from include.ui.util.path import get_directory, get_document

t = gettext.translation("client", "ui/locale", fallback=True)
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
        view.parent_manager.indicator.back()
        view.parent_manager.current_directory_id = (
            None if parent_id == "/" else parent_id
        )
        await get_directory(view.parent_manager.current_directory_id, view=view)

    async def folder_listtile_click(event: ft.Event[ft.ListTile]):
        view.parent_manager.indicator.go(event.control.data[1])
        view.parent_manager.current_directory_id = event.control.data[0]
        await get_directory(event.control.data[0], view=view)

    async def document_listtile_click(event: ft.Event[ft.ListTile]):
        await get_document(
            event.control.data[0], filename=event.control.data[1], view=view
        )

    async def document_right_click(
        event: (
            ft.TapEvent[ft.GestureDetector] | ft.LongPressStartEvent[ft.GestureDetector]
        ),
    ):
        assert event.control.content
        event.page.show_dialog(
            DocumentRightMenuDialog(event.control.content.data[0], view)
        )

    async def folder_right_click(
        event: (
            ft.TapEvent[ft.GestureDetector] | ft.LongPressStartEvent[ft.GestureDetector]
        ),
    ):
        assert event.control.content
        event.page.show_dialog(
            DirectoryRightMenuDialog(event.control.content.data[0], view)
        )

    if parent_id != None:
        # print("parent_id: ", parent_id)
        view.controls = [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.ARROW_BACK),
                title=ft.Text("<...>"),
                subtitle=ft.Text(_("Parent directory")),
                on_click=parent_button_click,
            )
        ]

    view.controls.extend(
        [
            ft.GestureDetector(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.FOLDER),
                    title=ft.Text(folder["name"]),
                    subtitle=ft.Text(
                        _("Created time: {created_time}").format(
                            created_time=datetime.fromtimestamp(
                                folder["created_time"]
                            ).strftime("%Y-%m-%d %H:%M:%S")
                        )
                    ),
                    data=(folder["id"], folder["name"]),
                    on_click=folder_listtile_click,
                ),
                on_secondary_tap=folder_right_click,
                on_long_press_start=folder_right_click,
                # on_hover=on_folder_hover
                # on_hover=lambda e: update_mouse_position(e),
            )
            for folder in folders
        ]
    )
    view.controls.extend(
        [
            ft.GestureDetector(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.FILE_COPY),
                    title=ft.Text(document["title"]),
                    subtitle=ft.Text(
                        _("Last modified: {last_modified}\n").format(
                            datetime.fromtimestamp(document["last_modified"]).strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        )
                        + (
                            f"{document["size"] / 1024 / 1024:.3f} MB"
                            if document["size"] > 0
                            else "0 Byte"
                        )
                    ),
                    is_three_line=True,
                    data=(document["id"], document["title"]),
                    on_click=document_listtile_click,
                ),
                on_secondary_tap=document_right_click,
                on_long_press_start=document_right_click,
                # on_hover=lambda e: update_mouse_position(e),
            )
            for document in documents
        ]
    )
    view.update()
