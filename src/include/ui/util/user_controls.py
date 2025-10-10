from typing import TYPE_CHECKING
from datetime import datetime
import flet as ft

from include.ui.controls.rightmenu.manage.account import UserRightMenuDialog

if TYPE_CHECKING:
    from include.ui.controls.views.manage.account import UserListView


def update_user_controls(view: "UserListView", users: list[dict], _update=True):

    async def user_right_click(
        event: (
            ft.TapEvent[ft.GestureDetector] | ft.LongPressStartEvent[ft.GestureDetector]
        ),
    ):
        assert event.control.content
        event.page.show_dialog(UserRightMenuDialog(event.control.content.data[0], view))

    async def user_click(
        event: ft.Event[ft.ListTile],
    ):
        assert event.control.data
        event.page.show_dialog(UserRightMenuDialog(event.control.data, view))

    view.controls = []  # reset
    view.controls.extend(
        [
            ft.GestureDetector(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.ACCOUNT_CIRCLE),
                    title=ft.Text(
                        user["nickname"] if user["nickname"] else user["username"]
                    ),
                    subtitle=ft.Text(
                        f"{user["groups"]}\n"
                        + f"Last login: {datetime.fromtimestamp(user['last_login']).strftime('%Y-%m-%d %H:%M:%S') if user['last_login'] else "Unknown"}"
                    ),
                    is_three_line=True,
                    data=user["username"],
                    on_click=user_click,
                ),
                data=user["username"],
                on_secondary_tap=user_right_click,
                on_long_press_start=user_right_click,
            )
            for user in users
        ]
    )
    if _update:
        view.update()
