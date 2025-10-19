from typing import Any
import flet as ft
from include.ui.controls.dialogs.base import AlertDialog

__all__ = ["RightMenuDialog"]


class RightMenuDialog(AlertDialog):
    def __init__(
        self,
        title: str | ft.Control | None = None,
        menu_items: list[dict[str, Any]] = [],
        modal: bool = False,
        ref: ft.Ref | None = None,
        visible: bool = True,
    ):
        # Validate menu_items structure
        required_keys = ["icon", "title", "subtitle", "on_click"]
        for item in menu_items:
            if not isinstance(item, dict) or not all(
                key in item for key in required_keys
            ):
                raise ValueError(
                    "Each item in menu_items must be a dict with keys: "
                    "'icon', 'title', 'subtitle', 'on_click'"
                )
            if not callable(item["on_click"]):
                raise ValueError("'on_click' must be callable")

        super().__init__(
            title=title, modal=modal, scrollable=True, ref=ref, visible=visible
        )
        # Create menu listview directly with ListTiles
        self.menu_listview = ft.ListView(
            controls=[
                ft.ListTile(
                    leading=ft.Icon(item["icon"]),
                    title=ft.Text(item["title"]),
                    subtitle=ft.Text(item["subtitle"]),
                    on_click=item["on_click"],
                    ref=item.get("ref"),  # Optional ref
                )
                for item in menu_items
            ]
        )
        self.content = ft.Container(self.menu_listview, width=480)
