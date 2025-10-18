from datetime import datetime
from typing import TYPE_CHECKING
import gettext
import flet as ft
from include.classes.config import AppConfig
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.dialogs.manage.accounts import (
        AddUserAccountDialog,
        RenameUserNicknameDialog,
        EditUserGroupDialog,
        ViewUserInfoDialog,
    )

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class AddUserAccountDialogController:
    def __init__(self, view: "AddUserAccountDialog"):
        self.view = view
        self.app_config = AppConfig()

    async def action_add_user_account(
        self,
    ):
        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="create_user",
            data={
                "username": self.view.username_field.value,
                "password": self.view.password_field.value,
                "nickname": self.view.nickname_field.value,
                "permissions": [],  # TODO
                "groups": [],
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            self.view.send_error(_(f"创建用户失败: ({code}) {response['message']}"))
        else:
            await self.view.parent_view.refresh_user_list()

        self.view.close()


class RenameUserNicknameDialogController:
    def __init__(self, view: "RenameUserNicknameDialog"):
        self.view = view
        self.app_config = AppConfig()

    async def action_rename_user_nickname(
        self,
    ):
        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="rename_user",
            data={
                "username": self.view.parent_dialog.username,
                "nickname": self.view.nickname_field.value,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )

        if (code := response["code"]) != 200:
            self.view.send_error(
                _(f"重命名用户昵称失败: ({code}) {response['message']}"),
            )
        else:
            await self.view.parent_dialog.parent_listview.parent_manager.refresh_user_list()

        self.view.close()


class EditUserGroupDialogController:
    def __init__(self, view: "EditUserGroupDialog"):
        self.view = view
        self.app_config = AppConfig()

    async def submit_user_group_change(self, to_submit_list):

        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="change_user_groups",
            data={
                "username": self.view.parent_dialog.username,
                "groups": to_submit_list,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            self.view.send_error(
                _(f"更改用户组失败: ({code}) {response['message']}"),
            )

        self.view.close()
        await self.view.parent_dialog.parent_listview.parent_manager.refresh_user_list()

    async def action_refresh_permission_list(self):
        self.view.disable_interactions()

        # Reset list
        self.view.group_listview.controls = []

        # Fetch user group information
        group_list_response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="list_groups",
            data={},
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := group_list_response["code"]) != 200:
            self.view.send_error(
                _(f"拉取用户组列表失败: ({code}) {group_list_response['message']}"),
            )
            return

        all_group_list = [
            group["name"] for group in group_list_response["data"]["groups"]
        ]

        user_data_response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="get_user_info",
            data={
                "username": self.view.parent_dialog.username,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := user_data_response["code"]) != 200:
            self.view.send_error(
                _(f"拉取用户信息失败: ({code}) {user_data_response['message']}"),
            )
            return
        user_membership_list = user_data_response["data"]["groups"]

        for each_group in all_group_list:
            self.view.group_listview.controls.append(
                ft.Checkbox(
                    label=each_group,  # May change to display name later
                    data=each_group,
                    on_change=None,  # Do nothing before submission
                    value=each_group in user_membership_list,
                )
            )

        self.view.enable_interactions()


class ViewUserInfoDialogController:
    def __init__(self, view: "ViewUserInfoDialog"):
        self.view = view
        self.app_config = AppConfig()

    async def action_refresh_user_info(self):

        self.view.progress_ring.visible = True
        self.view.info_listview.visible = False
        self.view.update()

        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="get_user_info",
            data={
                "username": self.view.parent_dialog.username,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            self.view.close()
            self.view.send_error(
                _(f"拉取用户信息失败: ({code}) {response['message']}"),
            )
        else:
            self.view.info_listview.controls = [
                ft.Text(_(f"用户名: {response['data']['username']}")),
                ft.Text(
                    _(f"用户昵称: {response['data']['nickname'] if response['data']['nickname'] else _('（无）')}")
                ),
                ft.Text(_(f"用户权限: {response['data']['permissions']}")),
                ft.Text(_(f"用户组： {response['data']['groups']}")),
                ft.Text(
                    _(f"用户注册时间: {datetime.fromtimestamp(response['data']['created_time']).strftime('%Y-%m-%d %H:%M:%S')}")
                ),
                ft.Text(
                    _(f"最后登录于: {datetime.fromtimestamp(response['data']['last_login']).strftime('%Y-%m-%d %H:%M:%S')}")
                ),
            ]
            self.view.progress_ring.visible = False
            self.view.info_listview.visible = True

        self.view.update()
