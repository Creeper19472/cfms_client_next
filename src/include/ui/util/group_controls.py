from datetime import datetime
from typing import TYPE_CHECKING
import gettext

import flet as ft

from include.constants import LOCALE_PATH
from include.ui.controls.contextmenus.group import GroupContextMenu

if TYPE_CHECKING:
    from include.ui.controls.views.admin.group import GroupListView

from include.util.locale import get_translation
t = get_translation()
_ = t.gettext


def update_group_controls(view: "GroupListView", groups: list[dict], _update_page=True):
    view.controls = []  # reset
    view.controls.extend(
        [
            GroupContextMenu(
                group_name=group["name"],
                display_name=group["display_name"],
                permissions=group["permissions"],
                members=group["members"],
                group_listview=view,
            )
            for group in groups
        ]
    )
    if _update_page:
        view.update()
