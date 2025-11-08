from datetime import datetime
from typing import TYPE_CHECKING
import gettext

import flet as ft

from include.classes.config import AppConfig
from include.constants import LOCALE_PATH
from include.ui.util.path import get_directory
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.dialogs.contextmenu.explorer import (
        RenameDialog,
        GetDirectoryInfoDialog,
    )

from include.util.locale import get_translation
t = get_translation()
_ = t.gettext


class RenameDialogController:
    def __init__(self, view: "RenameDialog"):
        self.view = view
        self.app_config = AppConfig()

    async def action_rename_object(self, new_title: str):
        if self.view.object_type == "document":
            response = await do_request(
                "rename_document",
                {
                    "document_id": self.view.object_id,
                    "new_title": new_title,
                },
                "",
                self.app_config.username,
                self.app_config.token,
            )
        elif self.view.object_type == "directory":
            response = await do_request(
                "rename_directory",
                {
                    "folder_id": self.view.object_id,
                    "new_name": new_title,
                },
                "",
                self.app_config.username,
                self.app_config.token,
            )
        else:
            raise TypeError

        if (code := response["code"]) != 200:
            self.view.send_error(
                _("Rename failed: ({code}) {message}").format(
                    code=code, message=response["message"]
                )
            )
        else:
            await get_directory(
                self.view.file_listview.parent_manager.current_directory_id,
                self.view.file_listview,
            )

        self.view.close()


class GetDirectoryInfoController:
    def __init__(self, view: "GetDirectoryInfoDialog"):
        self.view = view
        self.app_config = AppConfig()

    async def fetch_directory_info(self):
        response = await do_request(
            action="get_directory_info",
            data={
                "directory_id": self.view.directory_id,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            self.view.close()
            self.view.send_error(
                _("Failed to fetch directory info: ({code}) {message}").format(
                    code=code, message=response["message"]
                )
            )
        else:
            self.view.info_listview.controls = [
                ft.Text(
                    _("Directory ID: {dir_id}").format(
                        dir_id=response["data"]["directory_id"]
                    ),
                    selectable=True,
                ),
                ft.Text(
                    _("Directory Name: {dir_name}").format(
                        dir_name=response["data"]["name"]
                    ),
                    selectable=True,
                ),
                ft.Text(
                    _("Child object count: {child_count}").format(
                        child_count=response["data"]["count_of_child"]
                    ),
                ),
                ft.Text(
                    _("Created: {created_time}").format(
                        created_time=datetime.fromtimestamp(
                            response["data"]["created_time"]
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    )
                ),
                ft.Text(
                    _("Parent directory ID: {parent_id}").format(
                        parent_id=response["data"]["parent_id"]
                    ),
                    selectable=True,
                ),
                ft.Text(
                    _("Access rules: {access_rules}").format(
                        access_rules=(
                            response["data"]["access_rules"]
                            if not response["data"]["info_code"]
                            else "Unavailable"
                        )
                    ),
                    selectable=True,
                ),
            ]
            self.view.enable_interactions()
