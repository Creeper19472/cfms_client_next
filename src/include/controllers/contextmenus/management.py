from typing import TYPE_CHECKING
from include.controllers.base import BaseController
from include.ui.controls.dialogs.admin.accounts import (
    RenameUserNicknameDialog,
    EditUserGroupDialog,
    ViewUserInfoDialog,
    PasswdUserDialog,
)
from include.ui.controls.dialogs.wait import wait
from include.ui.util.notifications import send_error
from include.util.requests import do_request_2
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.contextmenus.management import UserContextMenu

t = get_translation()
_ = t.gettext


class UserContextMenuController(BaseController["UserContextMenu"]):
    def __init__(self, control: "UserContextMenu") -> None:
        super().__init__(control)

    @wait("delete_user")
    async def action_delete_user(self):
        response = await do_request_2(
            action="delete_user",
            data={"username": self.control.username},
            username=self.app_config.username,
            token=self.app_config.token,
        )

        if response.code != 200:
            send_error(
                self.control.page,
                _("Failed to delete user: ({code}) {message}").format(
                    code=response.code, message=response.message
                ),
            )
        else:
            await self.control.user_listview.parent_manager.refresh_user_list()

    async def action_open_rename_dialog(self):
        self.control.page.show_dialog(
            RenameUserNicknameDialog(
                self.control.username, self.control.user_listview.parent_manager
            )
        )

    async def action_edit_user_groups(self):
        self.control.page.show_dialog(
            EditUserGroupDialog(
                self.control.username, self.control.user_listview.parent_manager
            )
        )

    async def action_passwd_user(self):
        self.control.page.show_dialog(
            PasswdUserDialog(self.control.username, passwd_other=True)
        )

    async def action_view_user_info(self):
        self.control.page.show_dialog(ViewUserInfoDialog(self.control.username))
