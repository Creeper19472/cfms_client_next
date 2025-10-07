from typing import TYPE_CHECKING
from datetime import datetime
import flet as ft

if TYPE_CHECKING:
    from include.ui.controls.views.manage.account import UserListView


def update_user_controls(view: "UserListView", users: list[dict], _update=True):
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
                    # on_click=on_user_right_click_menu,
                ),
                data=user["username"],
                on_secondary_tap=lambda _: _.page.update() # on_user_right_click_menu,
                # on_long_press_start=on_user_right_click_menu,
            )
            for user in users
        ]
    )
    if _update:
        view.update()
