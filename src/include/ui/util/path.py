from typing import TYPE_CHECKING
from datetime import datetime
import gettext
import flet as ft
from include.ui.util.notifications import send_error
from include.util.communication import build_request

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext

if TYPE_CHECKING:
    from include.ui.controls.filemanager import FileListView

__all__ = ["get_directory"]


def update_file_controls(
    view: "FileListView",
    folders: list[dict],
    documents: list[dict],
    parent_id: str | None = None,
):
    view.controls = []  # reset

    async def on_parent_button_clicked(event: ft.Event[ft.ListTile]):
        view.parent_manager.indicator.back()
        await get_directory(id=None if parent_id == "/" else parent_id, view=view)

    if parent_id != None:
        # print("parent_id: ", parent_id)
        view.controls = [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.ARROW_BACK),
                title=ft.Text("<...>"),
                subtitle=ft.Text(f"Parent directory"),
                on_click=on_parent_button_clicked,
            )
        ]

    view.controls.extend(
        [
            ft.GestureDetector(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.FOLDER),
                    title=ft.Text(folder["name"]),
                    subtitle=ft.Text(
                        f"Created time: {datetime.fromtimestamp(folder['created_time']).strftime('%Y-%m-%d %H:%M:%S')}"
                    ),
                    data=(folder["id"], folder["name"]),
                    # on_click=on_folder_clicked,
                ),
                on_secondary_tap=lambda _: print("aaa")# on_folder_right_click_menu,
                # on_long_press_start=on_folder_right_click_menu,
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
                        f"Last modified: {datetime.fromtimestamp(document['last_modified']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                        + (
                            f"{document["size"] / 1024 / 1024:.3f} MB"
                            if document["size"] > 0
                            else "0 Byte"
                        )
                    ),
                    is_three_line=True,
                    data=(document["id"], document["title"]),
                    # on_click=lambda e: open_document(e.page, *e.control.data),
                ),
                on_secondary_tap=lambda _: print("aaa") # on_document_right_click_menu,
                # on_long_press_start=on_document_right_click_menu,
                # on_hover=lambda e: update_mouse_position(e),
            )
            for document in documents
        ]
    )
    view.update()


async def get_directory(id: str | None, view: "FileListView"):
    view.parent_manager.current_directory_id = id
    view.parent_manager.progress_ring.visible = True
    view.parent_manager.progress_ring.update()
    view.visible = False
    view.update()

    assert type(view.page) == ft.Page
    response = await build_request(
        view.parent_manager.conn,
        action="list_directory",
        data={"folder_id": id},
        username=view.page.session.get("username"),
        token=view.page.session.get("token"),
    )

    if (code := response["code"]) != 200:
        update_file_controls(view, [], [], view.parent_manager.previous_directory_id)
        send_error(view.page, _(f"加载失败: ({code}) {response['message']}"))
    else:
        update_file_controls(
            view,
            response["data"]["folders"],
            response["data"]["documents"],
            response["data"]["parent_id"],
        )

    view.parent_manager.progress_ring.visible = False
    view.parent_manager.progress_ring.update()
    view.visible = True
    view.update()
