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
        """Build and filter popup menu items based on permissions."""
        required_keys = {"icon", "content", "on_click"}
        
        # Filter and validate items
        filtered_items = self._filter_menu_items(menu_items, required_keys)
        
        # Convert to controls
        return [
            ft.PopupMenuItem() if item == {} 
            else self._create_popup_item(item)
            for item in filtered_items
        ]

    def _filter_menu_items(self, menu_items: list[dict[str, Any]], required_keys: set) -> list:
        """Filter menu items by validation and user permissions."""
        filtered = []
        
        for item in menu_items:
            if not isinstance(item, dict):
                raise TypeError("Each item in menu_items must be a dict")
            
            # Handle divider
            if item == {}:
                if filtered and filtered[-1] != {}:
                    filtered.append(item)
                continue
            
            # Validate required keys
            if not required_keys.issubset(item.keys()):
                raise ValueError(
                    f"Each item must contain keys: {required_keys}"
                )
            
            # Check permissions
            required_perms = set(item.get("require", []))
            user_perms = set(self.app_shared.user_permissions)
            if required_perms and not (required_perms & user_perms) == required_perms:
                continue
            
            filtered.append(item)
        
        # Remove trailing divider
        if filtered and filtered[-1] == {}:
            filtered.pop()
        
        return filtered

    def _create_popup_item(self, item: dict[str, Any]) -> ft.PopupMenuItem:
        """Create a `ft.PopupMenuItem` from item dictionary."""
        on_click = item.get("on_click")
        
        if on_click is not None and not callable(on_click):
            raise ValueError("'on_click' must be callable")
        
        return ft.PopupMenuItem(
            icon=item["icon"],
            content=item["content"],
            on_click=on_click,
            ref=item.get("ref"),
        )

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
