from typing import TYPE_CHECKING
from include.controllers.base import Controller

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileListView


class FileListViewController(Controller["FileListView"]):
    def __init__(
        self,
        control: "FileListView",
    ):
        super().__init__(control)
