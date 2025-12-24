from typing import TYPE_CHECKING
from include.controllers.base import BaseController
from include.ui.controls.dialogs.admin.groups import (
    RenameGroupDialog,
    EditGroupPermissionDialog,
)
from include.ui.controls.dialogs.wait import wait
from include.ui.util.notifications import send_error
from include.util.requests import do_request
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.contextmenus.group import GroupContextMenu

t = get_translation()
_ = t.gettext


class GroupContextMenuController(BaseController["GroupContextMenu"]):
    def __init__(self, control: "GroupContextMenu") -> None:
        super().__init__(control)

    @wait("delete_group")
    async def action_delete_group(self):
        response = await do_request(
            action="delete_group",
            data={"group_name": self.control.group_name},
            username=self.app_shared.username,
            token=self.app_shared.token,
        )

        if (code := response["code"]) != 200:
            send_error(
                self.control.page,
                _("Failed to delete user group: ({code}) {message}").format(
                    code=code, message=response["message"]
                ),
            )
        else:
            await self.control.group_listview.parent_manager.refresh_group_list()

    async def action_open_rename_dialog(self):
        self.control.page.show_dialog(
            RenameGroupDialog(
                self.control.group_name, self.control.group_listview.parent_manager
            )
        )

    async def action_open_permissions_dialog(self):
        self.control.page.show_dialog(
            EditGroupPermissionDialog(
                self.control.group_name, self.control.group_listview.parent_manager
            )
        )
