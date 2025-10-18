from datetime import datetime
from typing import TYPE_CHECKING
import gettext
import flet as ft
from include.classes.config import AppConfig
from include.ui.util.path import get_directory
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.dialogs.rightmenu.explorer import (
        RenameDialog,
        GetDirectoryInfoDialog,
    )

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class RenameDialogController:
    def __init__(self, view: "RenameDialog"):
        self.view = view
        self.app_config = AppConfig()

    async def action_rename_object(self, new_title: str):
        if type(self.view.parent_dialog).__name__ == "DocumentRightMenuDialog":
            response = await do_request(
                self.app_config.get_not_none_attribute("conn"),
                "rename_document",
                {
                    "document_id": self.view.parent_dialog.document_id,  # pyright: ignore[reportAttributeAccessIssue]
                    "new_title": new_title,
                },
                "",
                self.app_config.username,
                self.app_config.token,
            )
        elif type(self.view.parent_dialog).__name__ == "DirectoryRightMenuDialog":
            response = await do_request(
                self.app_config.get_not_none_attribute("conn"),
                "rename_directory",
                {
                    "folder_id": self.view.parent_dialog.directory_id,  # pyright: ignore[reportAttributeAccessIssue]
                    "new_name": new_title,
                },
                "",
                self.app_config.username,
                self.app_config.token,
            )
        else:
            raise TypeError

        if (code := response["code"]) != 200:
            self.view.send_error(_(f"Renamefailed: ({code}) {response['message']}"))
        else:
            await get_directory(
                self.view.parent_dialog.parent_listview.parent_manager.current_directory_id,
                self.view.parent_dialog.parent_listview,
            )

        self.view.close()


class GetDirectoryInfoController:
    def __init__(self, view: "GetDirectoryInfoDialog"):
        self.view = view
        self.app_config = AppConfig()

    async def fetch_directory_info(self):
        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="get_directory_info",
            data={
                "directory_id": self.view.parent_dialog.directory_id,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            self.view.close()
            self.view.send_error(_(f"Failed to fetch directory info: ({code}) {response['message']}"))
        else:
            self.view.info_listview.controls = [
                ft.Text(
                    _(f"DirectoryID: {response['data']['directory_id']}"), selectable=True
                ),
                ft.Text(_(f"Directory Name: {response['data']['name']}"), selectable=True),
                ft.Text(
                    _(f"Child object count: {response['data']['count_of_child']}"),
                ),
                ft.Text(
                    _(
                        f"Created: {datetime.fromtimestamp(response['data']['created_time']).strftime('%Y-%m-%d %H:%M:%S')}"
                    ),
                ),
                ft.Text(
                    _(f"Parent directory ID: {response['data']['parent_id']}"), selectable=True
                ),
                ft.Text(
                    _(
                        f"Access rules: {response['data']['access_rules'] if not response['data']['info_code'] else 'Unavailable'}"
                    ),
                    selectable=True,
                ),
            ]
            self.view.enable_interactions()
