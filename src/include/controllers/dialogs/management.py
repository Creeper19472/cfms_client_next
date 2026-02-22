from datetime import datetime
from typing import TYPE_CHECKING

import flet as ft

from include.controllers.base import Controller
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.dialogs.admin.accounts import (
        AddUserAccountDialog,
        RenameUserNicknameDialog,
        EditUserGroupDialog,
        ViewUserInfoDialog,
        BlockUserDialog,
        ListUserBlocksDialog,
    )

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class AddUserAccountDialogController(Controller["AddUserAccountDialog"]):
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
            username=self.app_shared.username,
            token=self.app_shared.token,
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


class RenameUserNicknameDialogController(Controller["RenameUserNicknameDialog"]):
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
            username=self.app_shared.username,
            token=self.app_shared.token,
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


class EditUserGroupDialogController(Controller["EditUserGroupDialog"]):
    def __init__(self, control: "EditUserGroupDialog"):
        super().__init__(control)

    async def submit_user_group_change(self, to_submit_list):

        response = await do_request(
            action="change_user_groups",
            data={
                "username": self.control.username,
                "groups": to_submit_list,
            },
            username=self.app_shared.username,
            token=self.app_shared.token,
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
            username=self.app_shared.username,
            token=self.app_shared.token,
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
            username=self.app_shared.username,
            token=self.app_shared.token,
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


class ViewUserInfoDialogController(Controller["ViewUserInfoDialog"]):
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
            username=self.app_shared.username,
            token=self.app_shared.token,
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


class BlockUserDialogController(Controller["BlockUserDialog"]):
    def __init__(self, control: "BlockUserDialog"):
        super().__init__(control)

    async def action_block_user(self):
        # Get block types from SegmentedButton
        block_types = list(self.control.block_types_button.selected)
        if not block_types:
            self.control.send_error(_("Please select at least one block type."))
            self.control.enable_interactions()
            return

        # Build target dict
        target_type = self.control.target_type_radio.value
        target: dict = {"type": target_type}
        if target_type != "all":
            if not self.control.target_id:
                self.control.send_error(_("Please select a target."))
                self.control.enable_interactions()
                return
            target["id"] = self.control.target_id

        data: dict = {
            "username": self.control.username,
            "block_types": block_types,
            "target": target,
        }

        # Add not_after if expiry is enabled
        if self.control.expires_enabled_checkbox.value:
            date_val = self.control.date_picker.value
            time_val = self.control.time_picker.value
            if date_val is None or time_val is None:
                self.control.send_error(
                    _("Please set a valid expiry date and time.")
                )
                self.control.enable_interactions()
                return
            data["not_after"] = datetime.combine(date_val, time_val).timestamp()

        response = await do_request(
            action="block_user",
            data=data,
            username=self.app_shared.username,
            token=self.app_shared.token,
        )
        if (code := response["code"]) != 200:
            self.control.send_error(
                _("Failed to block user: ({code}) {message}").format(
                    code=code, message=response["message"]
                )
            )
            self.control.enable_interactions()
        else:
            self.control.close()


class ListUserBlocksDialogController(Controller["ListUserBlocksDialog"]):
    def __init__(self, control: "ListUserBlocksDialog"):
        super().__init__(control)

    async def action_refresh_blocks(self):
        self.control.disable_interactions()

        response = await do_request(
            action="list_user_blocks",
            data={"username": self.control.username},
            username=self.app_shared.username,
            token=self.app_shared.token,
        )
        if (code := response["code"]) != 200:
            self.control.send_error(
                _("Failed to fetch user blocks: ({code}) {message}").format(
                    code=code, message=response["message"]
                )
            )
            self.control.enable_interactions()
            return

        blocks: list[dict] = response["data"].get("blocks", [])
        self.control.build_block_list(blocks)
        self.control.enable_interactions()

    async def action_revoke_block(self, block_id: str):
        response = await do_request(
            action="unblock_user",
            data={"block_id": block_id},
            username=self.app_shared.username,
            token=self.app_shared.token,
        )
        if (code := response["code"]) != 200:
            self.control.send_error(
                _("Failed to revoke block: ({code}) {message}").format(
                    code=code, message=response["message"]
                )
            )
        await self.action_refresh_blocks()
