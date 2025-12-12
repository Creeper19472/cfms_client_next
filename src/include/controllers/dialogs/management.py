from datetime import datetime
from typing import TYPE_CHECKING

import flet as ft

from include.controllers.base import BaseController
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.dialogs.admin.accounts import (
        AddUserAccountDialog,
        RenameUserNicknameDialog,
        EditUserGroupDialog,
        ViewUserInfoDialog,
    )

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class AddUserAccountDialogController(BaseController["AddUserAccountDialog"]):
    def __init__(self, control: "AddUserAccountDialog"):
        super().__init__(control)

    async def action_add_user_account(
        self,
    ):
        response = await do_request(
            action="create_user",
            data={
                "username": self.control.username_field.value,
                "password": self.control.password_field.value,
                "nickname": self.control.nickname_field.value,
                "permissions": [],  # TODO
                "groups": [],
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            self.control.send_error(
                _("Create user failed: ({code}) {message}").format(
                    code=code, message=response["message"]
                )
            )
        else:
            await self.control.parent_view.refresh_user_list()

        self.control.close()


class RenameUserNicknameDialogController(BaseController["RenameUserNicknameDialog"]):
    def __init__(self, control: "RenameUserNicknameDialog"):
        super().__init__(control)

    async def action_rename_user_nickname(
        self,
    ):
        response = await do_request(
            action="rename_user",
            data={
                "username": self.control.username,
                "nickname": self.control.nickname_field.value,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )

        if (code := response["code"]) != 200:
            self.control.send_error(
                _("Rename user nickname failed: ({code}) {message}").format(
                    code=code, message=response["message"]
                ),
            )
        else:
            await self.control.parent_manager.refresh_user_list()

        self.control.close()


class EditUserGroupDialogController(BaseController["EditUserGroupDialog"]):
    def __init__(self, control: "EditUserGroupDialog"):
        super().__init__(control)

    async def submit_user_group_change(self, to_submit_list):

        response = await do_request(
            action="change_user_groups",
            data={
                "username": self.control.username,
                "groups": to_submit_list,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            self.control.send_error(
                _("Change user group failed: ({code}) {message}").format(
                    code=code, message=response["message"]
                ),
            )

        self.control.close()
        await self.control.parent_manager.refresh_user_list()

    async def action_refresh_permission_list(self):
        self.control.disable_interactions()

        # Reset list
        self.control.group_listview.controls = []

        # Fetch user group information
        group_list_response = await do_request(
            action="list_groups",
            data={},
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := group_list_response["code"]) != 200:
            self.control.send_error(
                _("Failed to fetch user group list: ({code}) {message}").format(
                    code=code, message=group_list_response["message"]
                ),
            )
            return

        all_group_list = [
            group["name"] for group in group_list_response["data"]["groups"]
        ]

        user_data_response = await do_request(
            action="get_user_info",
            data={
                "username": self.control.username,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := user_data_response["code"]) != 200:
            self.control.send_error(
                _("Failed to fetch user info: ({code}) {message}").format(
                    code=code, message=user_data_response["message"]
                ),
            )
            return
        user_membership_list = user_data_response["data"]["groups"]

        for each_group in all_group_list:
            self.control.group_listview.controls.append(
                ft.Checkbox(
                    label=each_group,  # May change to display name later
                    data=each_group,
                    on_change=None,  # Do nothing before submission
                    value=each_group in user_membership_list,
                )
            )

        self.control.enable_interactions()


class ViewUserInfoDialogController(BaseController["ViewUserInfoDialog"]):
    def __init__(self, control: "ViewUserInfoDialog"):
        super().__init__(control)

    async def action_refresh_user_info(self):

        self.control.progress_ring.visible = True
        self.control.info_listview.visible = False
        self.control.update()

        response = await do_request(
            action="get_user_info",
            data={
                "username": self.control.username,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            self.control.close()
            self.control.send_error(
                _("Failed to fetch user info: ({code}) {message}").format(
                    code=code, message=response["message"]
                ),
            )
        else:
            self.control.info_listview.controls = [
                ft.Text(
                    _("Username: {username}").format(
                        username=response["data"]["username"]
                    )
                ),
                ft.Text(
                    _("User nickname: {nickname}").format(
                        nickname=(
                            response["data"]["nickname"]
                            if response["data"]["nickname"]
                            else _("(None)")
                        )
                    )
                ),
                ft.Text(
                    _("User permissions: {permissions}").format(
                        permissions=response["data"]["permissions"]
                    )
                ),
                ft.Text(
                    _("User groups: {groups}").format(groups=response["data"]["groups"])
                ),
                ft.Text(
                    _("User registration time: {created_time}").format(
                        created_time=datetime.fromtimestamp(
                            response["data"]["created_time"]
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    )
                ),
                ft.Text(
                    _("Last login: {last_login}").format(
                        last_login=datetime.fromtimestamp(
                            response["data"]["last_login"]
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    )
                ),
                ft.Text(
                    _("Password last changed: {passwd_changed_time}").format(
                        passwd_changed_time=datetime.fromtimestamp(
                            response["data"]["passwd_last_modified"]
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    )
                ),
            ]
            self.control.progress_ring.visible = False
            self.control.info_listview.visible = True

        self.control.update()
