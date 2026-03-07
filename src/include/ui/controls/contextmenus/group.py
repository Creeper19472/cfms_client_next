from typing import TYPE_CHECKING
import flet as ft
from flet_material_symbols import Symbols
from include.controllers.contextmenus.group import GroupContextMenuController
from include.ui.controls.menus.base import ContextMenu2
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.views.admin.group import GroupListView

t = get_translation()
_ = t.gettext


class GroupContextMenu(ContextMenu2):
    def __init__(
        self,
        group_name: str,
        display_name: str,
        permissions: list[str],
        members: list[str],
        group_listview: "GroupListView",
        ref: ft.Ref | None = None,
    ):
        self.page: ft.Page

        self.group_name = group_name
        self.display_name = display_name
        self.permissions = permissions
        self.members = members
        self.group_listview = group_listview
        self.controller = GroupContextMenuController(self)

        self._listtile = ft.ListTile(
            leading=ft.Icon(Symbols.GROUPS_3),
            title=ft.Text(display_name if display_name else group_name),
            subtitle=ft.Text(
                _("Permissions: {permissions}\n").format(permissions=permissions)
                + _("Members: {members}").format(members=members)
            ),
            is_three_line=True,
            on_click=self.listtile_click,
        )

        super().__init__(
            self._listtile,
            ref=ref,
            menu_items=[
                {
                    "icon": Symbols.GROUP_REMOVE,
                    "content": _("Delete"),
                    "on_click": self.delete_button_click,
                },
                {
                    "icon": Symbols.DRIVE_FILE_RENAME_OUTLINE,
                    "content": _("Rename"),
                    "on_click": self.rename_button_click,
                },
                {
                    "icon": Symbols.SETTINGS,
                    "content": _("Set Permissions"),
                    "on_click": self.settings_button_click,
                },
            ],
        )

    async def listtile_click(self, event: ft.Event[ft.ListTile]):
        await self.open()

    async def delete_button_click(self, event: ft.Event[ft.PopupMenuItem]):
        self.page.run_task(self.controller.action_delete_group)

    async def rename_button_click(self, event: ft.Event[ft.PopupMenuItem]) -> None:
        self.page.run_task(self.controller.action_open_rename_dialog)

    async def settings_button_click(self, event: ft.Event[ft.PopupMenuItem]) -> None:
        self.page.run_task(self.controller.action_open_permissions_dialog)
