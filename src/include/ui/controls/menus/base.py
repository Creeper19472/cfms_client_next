from typing import Any

import flet as ft

from include.classes.shared import AppShared

__all__ = ["ContextMenu2"]


class ContextMenu2(ft.ContextMenu):
    """
    A context menu that displays a list of menu items with icons, titles, subtitles, and click handlers.
    Each menu item is represented as a dictionary with the following structure:

    ```python
    {
        "primary_items": [
            {
                "icon": ft.Icon,
                "content": str | ft.Control,
                "on_click": ControlEventHandler[PopupMenuItem] | None,
                "ref": ft.Ref | None
            },
            {},  # divider
            ...
        ]
    }
    ```
    """

    def __init__(
        self,
        content: ft.Control,
        on_enter: ft.ControlEventHandler[ft.GestureDetector] | None = None,
        on_exit: ft.ControlEventHandler[ft.GestureDetector] | None = None,
        menu_items: list[dict[str, Any]] = [],
        ref: ft.Ref | None = None,
    ):

        self.app_shared = AppShared()
        self._content = content
        self._on_enter = on_enter
        self._on_exit = on_exit
        self._ref = ref

        self.menu_items = menu_items  # Will trigger setter and UI build

        super().__init__(
            content=ft.GestureDetector(
                expand=True,
                expand_loose=True,
                on_long_press_start=self.trigger_open_menu,
                on_secondary_tap_down=self.trigger_open_menu,
                on_enter=self._on_enter,
                on_exit=self._on_exit,
                content=content,
            ),
            items=self._controls,
            ref=ref,
        )

    @property
    def menu_items(self):
        return self._menu_items

    @menu_items.setter
    def menu_items(self, value):
        self._menu_items = value
        self._controls = self._build_controls(value)

    def _build_controls(self, menu_items):
        required_keys = ["icon", "content", "on_click"]
        controls = []
        for item in menu_items:
            if not isinstance(item, dict):
                raise TypeError("Each item in menu_items must be a dict")

            if item == {}:
                controls.append(ft.PopupMenuItem())
                continue
            elif not all(key in item for key in required_keys):
                raise ValueError(
                    "Each item in menu_items must be a dict with keys: "
                    "'icon', 'content', 'on_click'"
                )

            item_require = set(item.get("require", {}))
            if (item_require & set(self.app_shared.user_permissions)) != item_require:
                continue

            item_icon = item["icon"]
            item_content = item["content"]
            item_on_click = item.get("on_click")
            item_ref = item.get("ref")  # Optional ref

            if item_on_click is not None and not callable(item_on_click):
                raise ValueError("'on_click' must be callable")

            controls.append(
                ft.PopupMenuItem(
                    icon=item_icon,
                    content=item_content,
                    on_click=item_on_click,
                    ref=item_ref,
                )
            )
        return controls

    async def trigger_open_menu(
        self,
        event: (
            ft.TapEvent[ft.GestureDetector] | ft.LongPressStartEvent[ft.GestureDetector]
        ),
    ):
        await self.open(
            local_position=event.local_position,
            global_position=event.global_position,
        )
