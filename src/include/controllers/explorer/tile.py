from typing import TYPE_CHECKING
from include.controllers.base import BaseController
from include.ui.controls.dialogs.wait import wait
from include.ui.controls.dialogs.contextmenu.explorer import (
    GetDirectoryInfoDialog,
    GetDocumentInfoDialog,
    RenameDialog,
)
from include.ui.controls.dialogs.contextmenu.move import MoveDialog
from include.ui.controls.dialogs.authorize import AuthorizeDialog
from include.ui.controls.dialogs.view_access_entries import ViewAccessEntriesDialog
from include.ui.controls.components.rulemanager import RuleManager
from include.ui.util.path import get_directory, get_document
from include.util.requests import do_request
from include.ui.util.notifications import send_error
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.contextmenus.explorer import (
        FileContextMenu,
        DirectoryContextMenu,
    )

t = get_translation()
_ = t.gettext


class FileContextMenuController(BaseController["FileContextMenu"]):
    def __init__(self, control: "FileContextMenu") -> None:
        super().__init__(control)

    async def action_open_file(self):
        await get_document(
            self.control.file_id,
            filename=self.control.filename,
            page=self.control.page,
        )

    async def action_delete_file(self):
        response = await do_request(
            action="delete_document",
            data={"document_id": self.control.file_id},
            username=self.app_shared.username,
            token=self.app_shared.token,
        )
        if (code := response["code"]) != 200:
            send_error(
                self.control.page,
                _("Deletion failed: ({code}) {message}").format(
                    code=code, message=response["message"]
                ),
            )
        else:
            await get_directory(
                self.control.parent_listview.parent_manager.current_directory_id,
                self.control.parent_listview,
            )

    async def action_rename_file(self):
        self.control.page.show_dialog(
            RenameDialog("document", self.control.file_id, self.control.parent_listview)
        )

    async def action_move_file(self):
        self.control.page.show_dialog(
            MoveDialog("document", self.control.file_id, self.control.parent_listview)
        )

    async def action_authorize(self):
        self.control.page.show_dialog(
            AuthorizeDialog("document", self.control.file_id, self.control.parent_listview)
        )

    async def action_view_access_entries(self):
        self.control.page.show_dialog(
            ViewAccessEntriesDialog("document", self.control.file_id, self.control.parent_listview)
        )

    async def action_set_access_rules(self):
        self.control.page.show_dialog(RuleManager(self.control.file_id, "document"))

    async def action_open_document_info(self):
        self.control.page.show_dialog(GetDocumentInfoDialog(self.control.file_id))


class DirectoryContextMenuController(BaseController["DirectoryContextMenu"]):
    def __init__(self, control: "DirectoryContextMenu") -> None:
        super().__init__(control)

    async def action_open_directory(self):
        self.control.parent_listview.parent_manager.indicator.go(self.control.dir_name)
        await get_directory(
            self.control.directory_id, view=self.control.parent_listview
        )

    @wait("delete_directory")
    async def action_delete_directory(self):
        response = await do_request(
            action="delete_directory",
            data={"folder_id": self.control.directory_id},
            username=self.app_shared.username,
            token=self.app_shared.token,
        )
        if (code := response["code"]) != 200:
            send_error(
                self.control.page,
                _("Deletion failed: ({code}) {message}").format(
                    code=code, message=response["message"]
                ),
            )
        else:
            await get_directory(
                self.control.parent_listview.parent_manager.current_directory_id,
                self.control.parent_listview,
            )

    async def action_rename_directory(self):
        self.control.page.show_dialog(
            RenameDialog(
                "directory", self.control.directory_id, self.control.parent_listview
            )
        )

    async def action_move_directory(self):
        self.control.page.show_dialog(
            MoveDialog(
                "directory", self.control.directory_id, self.control.parent_listview
            )
        )

    async def action_authorize(self):
        self.control.page.show_dialog(
            AuthorizeDialog(
                "directory", self.control.directory_id, self.control.parent_listview
            )
        )

    async def action_view_access_entries(self):
        self.control.page.show_dialog(
            ViewAccessEntriesDialog(
                "directory", self.control.directory_id, self.control.parent_listview
            )
        )

    async def action_set_access_rules(self):
        self.control.page.show_dialog(
            RuleManager(self.control.directory_id, "directory")
        )

    async def action_open_directory_info(self):
        self.control.page.show_dialog(GetDirectoryInfoDialog(self.control.directory_id))
