from typing import Optional, TYPE_CHECKING
from datetime import datetime
import flet as ft
from flet_material_symbols import Symbols
from include.controllers.contextmenus.management import UserContextMenuController
from include.ui.controls.menus.base import ContextMenu2
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.views.admin.account import UserListView

t = get_translation()
_ = t.gettext


class UserManagementContextMenu(ContextMenu2):
    def __init__(
        self,
        username: str,
        user_listview: "UserListView",
        nickname: Optional[str] = None,
        groups: list[str] = [],
        last_login: Optional[float] = None,
        ref: ft.Ref | None = None,
    ):
        self.page: ft.Page

        self.username = username
        self.nickname = nickname
        self.groups = groups
        self.last_login = last_login
        self.user_listview = user_listview
        self.controller = UserContextMenuController(self)

        self._listtile = ft.ListTile(
            leading=ft.Icon(Symbols.ACCOUNT_CIRCLE, fill=1),
            title=ft.Text(nickname or username),
            subtitle=ft.Text(
                f"{groups}\n"
                + _("Last login: {last_login}").format(
                    last_login=(
                        datetime.fromtimestamp(last_login).strftime("%Y-%m-%d %H:%M:%S")
                        if last_login
                        else _("(Unknown)")
                    )
                )
            ),
            is_three_line=True,
            on_click=self.listtile_click,
        )

        super().__init__(
            self._listtile,
            ref=ref,
            menu_items=[
                {
                    "icon": Symbols.DELETE,
                    "content": _("Delete"),
                    "on_click": self.delete_button_click,
                },
                {
                    "icon": Symbols.DRIVE_FILE_RENAME_OUTLINE,
                    "content": _("Change Nickname"),
                    "on_click": self.rename_button_click,
                },
                {
                    "icon": Symbols.FORMAT_LIST_BULLETED,
                    "content": _("Edit User Group"),
                    "on_click": self.edit_group_button_click,
                },
                {
                    "icon": Symbols.PASSWORD,
                    "content": _("Reset Password"),
                    "on_click": self.passwd_button_click,
                },
                {
                    "icon": Symbols.INFO,
                    "content": _("Properties"),
                    "on_click": self.properties_button_click,
                },
                {},
                {
                    "icon": Symbols.BLOCK,
                    "content": _("Block User"),
                    "on_click": self.block_user_button_click,
                    "require": {"block"},
                },
                {
                    "icon": Symbols.MANAGE_ACCOUNTS,
                    "content": _("View/Revoke Blocks"),
                    "on_click": self.list_blocks_button_click,
                    "require": {"list_user_blocks"},
                },
            ],
        )

    async def listtile_click(self, event: ft.Event[ft.ListTile]):
        await self.open()

    async def delete_button_click(self, event: ft.Event[ft.PopupMenuItem]):
        self.page.run_task(self.controller.action_delete_user)

    async def rename_button_click(self, event: ft.Event[ft.PopupMenuItem]) -> None:
        self.page.run_task(self.controller.action_open_rename_dialog)

    async def edit_group_button_click(self, event: ft.Event[ft.PopupMenuItem]) -> None:
        self.page.run_task(self.controller.action_edit_user_groups)

    async def passwd_button_click(self, event: ft.Event[ft.PopupMenuItem]) -> None:
        self.page.run_task(self.controller.action_passwd_user)

    async def properties_button_click(self, event: ft.Event[ft.PopupMenuItem]) -> None:
        self.page.run_task(self.controller.action_view_user_info)

    async def block_user_button_click(self, event: ft.Event[ft.PopupMenuItem]) -> None:
        self.page.run_task(self.controller.action_block_user)

    async def list_blocks_button_click(self, event: ft.Event[ft.PopupMenuItem]) -> None:
        self.page.run_task(self.controller.action_list_user_blocks)
