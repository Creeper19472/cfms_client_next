from typing import TYPE_CHECKING, Optional
import flet as ft
import gettext

from include.classes.config import AppConfig
from include.ui.controls.rightmenu.base import RightMenuDialog
from include.ui.controls.dialogs.manage.accounts import (
    RenameUserNicknameDialog,
    ViewUserInfoDialog,
    EditUserGroupDialog,
)
from include.ui.util.notifications import send_error
from include.util.requests import do_request

if TYPE_CHECKING:
    from ui.controls.views.manage.account import UserListView

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class UserRightMenuDialog(RightMenuDialog):
    def __init__(
        self,
        username: str,
        parent_listview: "UserListView",
        ref: ft.Ref | None = None,
        visible: bool = True,
    ):
        self.username = username
        self.app_config = AppConfig()
        self.parent_listview = parent_listview

        # Define menu items as a list for better maintainability
        menu_items = [
            {
                "icon": ft.Icons.DELETE,
                "title": _(_("删除")),
                "subtitle": _(_("删除此用户")),
                "on_click": self.delete_user,
            },
            {
                "icon": ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED,
                "title": _(_("更改昵称")),
                "subtitle": _(_("为用户更改昵称")),
                "on_click": self.rename_user,
            },
            {
                "icon": ft.Icons.FORMAT_LIST_BULLETED,
                "title": _(_("编辑用户组")),
                "subtitle": _(_("为用户更改所属的用户组")),
                "on_click": self.edit_user_group,
            },
            {
                "icon": ft.Icons.INFO_OUTLINED,
                "title": _(_("属性")),
                "subtitle": _(_("查看该用户的详细信息")),
                "on_click": self.view_user_info,
            },
        ]
        super().__init__(
            title=ft.Text(_(_("操作用户"))),
            menu_items=menu_items,
            ref=ref,
            visible=visible,
        )

    async def delete_user(self, event: ft.Event[ft.ListTile]):
        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="delete_user",
            data={"username": self.username},
            username=self.app_config.username,
            token=self.app_config.token,
        )

        if (code := response["code"]) != 200:
            send_error(self.page, _(f"删除用户失败: ({code}) {response['message']}"))
        else:
            await self.parent_listview.parent_manager.refresh_user_list()

        self.close()

    async def rename_user(self, event: ft.Event[ft.ListTile]) -> None:
        self.close()
        dialog = RenameUserNicknameDialog(self)
        self.page.show_dialog(dialog)

    async def edit_user_group(self, event: ft.Event[ft.ListTile]) -> None:
        self.close()
        dialog = EditUserGroupDialog(self)
        self.page.show_dialog(dialog)

    async def view_user_info(self, event: ft.Event[ft.ListTile]) -> None:
        self.close()
        dialog = ViewUserInfoDialog(self)
        self.page.show_dialog(dialog)
