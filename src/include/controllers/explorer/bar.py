from typing import TYPE_CHECKING
import flet as ft

from include.classes.ui.enum import SortMode, SortOrder
from include.controllers.base import BaseController

if TYPE_CHECKING:
    from include.ui.controls.components.explorer.bar import FileSortBar


class FileSortBarController(BaseController["FileSortBar"]):
    def __init__(
        self,
        control: "FileSortBar",
    ):
        super().__init__(control)

        self.sort_mode_mapping = {
            "name": SortMode.BY_NAME,
            "created_at": SortMode.BY_CREATED_AT,
            "modified": SortMode.BY_LAST_MODIFIED,
            "size": SortMode.BY_SIZE,
            "type": SortMode.BY_TYPE,
        }

    async def apply_sorting(self) -> None:
        assert (dropdown_value := self.control.sort_dropdown.value)
        sort_mode = self.sort_mode_mapping[dropdown_value]
        sort_order = (
            SortOrder.ASCENDING
            if self.control.order_button.icon == ft.Icons.ARROW_UPWARD
            else SortOrder.DESCENDING
        )
        self.control.parent_view.file_listview.sort_files(
            sort_mode=sort_mode, sort_order=sort_order
        )
