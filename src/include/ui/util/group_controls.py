from typing import TYPE_CHECKING
from datetime import datetime
import flet as ft

from include.ui.controls.rightmenu.manage import GroupRightMenuDialog

if TYPE_CHECKING:
    from include.ui.controls.views.manage.group import GroupListView


def update_group_controls(view: "GroupListView", groups: list[dict], _update_page=True):

    async def group_right_click(
        event: (
            ft.TapEvent[ft.GestureDetector] | ft.LongPressStartEvent[ft.GestureDetector]
        ),
    ):
        assert event.control.content
        event.page.show_dialog(
            GroupRightMenuDialog(event.control.content.data, view)
        )

    async def group_click(
        event: ft.Event[ft.ListTile],
    ):
        assert event.control.data
        event.page.show_dialog(GroupRightMenuDialog(event.control.data, view))

    view.controls = []  # reset
    view.controls.extend(
        [
            ft.GestureDetector(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.GROUPS_3),
                    title=ft.Text(
                        group["display_name"]
                        if group["display_name"]
                        else group["name"]
                    ),
                    subtitle=ft.Text(
                        f"Permissions: {group["permissions"]}\n"
                        + f"Members: {group['members']}"
                    ),
                    is_three_line=True,
                    data=group["name"],
                    on_click=group_click,
                ),
                data=group["name"],
                on_secondary_tap=group_right_click,
                on_long_press_start=group_right_click,
            )
            for group in groups
        ]
    )
    if _update_page:
        view.update()
