from typing import TYPE_CHECKING
from datetime import datetime
import flet as ft

if TYPE_CHECKING:
    from include.ui.controls.views.manage.group import GroupListView


def update_group_controls(view: "GroupListView", groups: list[dict], _update_page=True):
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
                    # on_click=on_group_right_click_menu,
                ),
                data=group["name"],
                on_secondary_tap=lambda _: _.page.update()
                # on_secondary_tap=on_group_right_click_menu,
                # on_long_press_start=on_group_right_click_menu,
                # on_hover=lambda e: update_mouse_position(e),
            )
            for group in groups
        ]
    )
    if _update_page:
        view.update()
