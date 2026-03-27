from typing import TYPE_CHECKING
from include.ui.controls.contextmenus.management import UserManagementContextMenu

if TYPE_CHECKING:
    from include.ui.controls.views.admin.account import UserListView

from include.util.locale import get_translation
t = get_translation()
_ = t.gettext


def update_user_controls(view: "UserListView", users: list[dict], _update=True):
    view.controls = []  # reset
    view.controls.extend(
        [
            UserManagementContextMenu(
                username=user["username"],
                nickname=user.get("nickname"),
                groups=user.get("groups", []),
                last_login=user.get("last_login"),
                user_listview=view,
            )
            for user in users
        ]
    )
    if _update:
        view.update()
