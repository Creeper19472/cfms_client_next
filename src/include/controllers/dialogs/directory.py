from typing import TYPE_CHECKING
import gettext
from include.classes.config import AppConfig
from include.classes.exceptions.request import (
    CreateDirectoryFailureError,
    RequestFailureError,
)
from include.ui.util.path import get_directory
from include.util.create import create_directory

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import (
        CreateDirectoryDialog,
        OpenDirectoryDialog,
    )

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class CreateDirectoryDialogController:
    def __init__(self, view: "CreateDirectoryDialog"):
        self.view = view
        self.app_config = AppConfig()

    async def action_create_directory(self, directory_name: str):
        try:
            await create_directory(
                self.app_config.get_not_none_attribute("conn"),
                self.view.parent_manager.current_directory_id,
                directory_name,
                self.app_config.username,
                self.app_config.token,
            )
        except CreateDirectoryFailureError as err:
            self.view.send_error(str(err))

        await get_directory(
            self.view.parent_manager.current_directory_id,
            self.view.parent_manager.file_listview,
        )
        self.view.close()


class OpenDirectoryDialogController:
    def __init__(self, view: "OpenDirectoryDialog"):
        self.view = view
        self.app_config = AppConfig()

    async def action_open_directory(self, directory_id: str):
        try:
            await get_directory(
                directory_id,
                self.view.parent_manager.file_listview,
                fallback="",
                _raise_on_error=True,
            )
        except RequestFailureError as exc:
            if exc.response:
                self.view.directory_textfield.error = (
                    _("Get directory failed: ") + 
                    f"({exc.response["code"]}) {exc.response["message"]}"
                )
            self.view.enable_interactions()
            return

        self.view.parent_manager.indicator.clear()
        self.view.parent_manager.indicator.go(directory_id)
        self.view.close()
