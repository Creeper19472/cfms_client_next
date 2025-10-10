from re import S
from typing import TYPE_CHECKING, Optional
import flet as ft
import gettext

from include.classes.config import AppConfig
from include.ui.controls.dialogs.manage.accounts import (
    RenameUserNicknameDialog,
    ViewUserInfoDialog,
    EditUserGroupDialog,
)
from include.ui.util.notifications import send_error
from include.util.communication import build_request

if TYPE_CHECKING:
    from ui.controls.views.manage.account import UserListView

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class UserRightMenuDialog(ft.AlertDialog):
    def __init__(
        self,
        username: str,
        parent_listview: "UserListView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(_("操作用户"))

        self.username = username
        self.app_config = AppConfig()
        self.parent_listview = parent_listview

        self.menu_listview = ft.ListView(
            controls=[
                ft.Column(
                    [
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.DELETE),
                            title=ft.Text("删除"),
                            subtitle=ft.Text(f"删除此用户"),
                            on_click=self.delete_user,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(
                                ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED
                            ),
                            title=ft.Text("更改昵称"),
                            subtitle=ft.Text(f"为用户更改昵称"),
                            on_click=self.rename_user,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.FORMAT_LIST_BULLETED),
                            title=ft.Text("编辑用户组"),
                            subtitle=ft.Text(f"为用户更改所属的用户组"),
                            on_click=self.edit_user_group,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.INFO_OUTLINED),
                            title=ft.Text("属性"),
                            subtitle=ft.Text(f"查看该用户的详细信息"),
                            on_click=self.view_user_info,
                        ),
                    ],
                )
            ]
        )
        self.content = ft.Container(self.menu_listview, width=480)

    def close(self):
        self.open = False
        self.update()

    async def delete_user(self, event: ft.Event[ft.ListTile]):
        response = await build_request(
            self.app_config.get_not_none_attribute("conn"),
            action="delete_user",
            data={"username": self.username},
            username=self.app_config.username,
            token=self.app_config.token,
        )

        if (code := response["code"]) != 200:
            send_error(self.page, f"删除用户失败: ({code}) {response['message']}")
        else:
            await self.parent_listview.parent_manager.refresh_user_list()

        self.close()

    async def rename_user(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(RenameUserNicknameDialog(self))

    async def edit_user_group(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(EditUserGroupDialog(self))

    async def view_user_info(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(ViewUserInfoDialog(self))
