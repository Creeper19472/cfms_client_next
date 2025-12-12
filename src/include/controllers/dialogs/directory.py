from typing import TYPE_CHECKING

from include.classes.exceptions.request import (
    CreateDirectoryFailureError,
    RequestFailureError,
)
from include.controllers.base import BaseController
from include.ui.util.path import get_directory
from include.util.create import create_directory

if TYPE_CHECKING:
    from include.ui.controls.dialogs.explorer import (
        CreateDirectoryDialog,
        OpenDirectoryDialog,
    )

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class CreateDirectoryDialogController(BaseController["CreateDirectoryDialog"]):
    def __init__(self, control: "CreateDirectoryDialog"):
        super().__init__(control)

    async def action_create_directory(self, directory_name: str):
        try:
            await create_directory(
                self.control.parent_manager.current_directory_id,
                directory_name,
                self.app_config.username,
                self.app_config.token,
            )
        except CreateDirectoryFailureError as err:
            self.control.send_error(str(err))

        await get_directory(
            self.control.parent_manager.current_directory_id,
            self.control.parent_manager.file_listview,
        )
        self.control.close()


class OpenDirectoryDialogController(BaseController["OpenDirectoryDialog"]):
    def __init__(self, control: "OpenDirectoryDialog"):
        super().__init__(control)

    async def action_open_directory(self, directory_id: str):

        directory_id = "" if directory_id == "/" else directory_id

        try:
            await get_directory(
                directory_id,
                self.control.parent_manager.file_listview,
                fallback=self.control.parent_manager.current_directory_id,
                _raise_on_error=True,
                _set_new_root=True,
            )
        except RequestFailureError as exc:
            if exc.response:
                self.control.directory_textfield.error = (
                    _("Get directory failed: ")
                    + f"({exc.response["code"]}) {exc.response["message"]}"
                )
            self.control.enable_interactions()
            return

        self.control.parent_manager.indicator.reset()
        self.control.parent_manager.indicator.go(directory_id)
        self.control.close()
