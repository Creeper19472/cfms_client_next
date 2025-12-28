from datetime import datetime
from typing import TYPE_CHECKING

import flet as ft

from include.classes.config import AppShared
from include.controllers.explorer.tile import (
    FileContextMenuController,
    DirectoryContextMenuController,
)

from include.ui.controls.components.explorer.tile import FileTile, DirectoryTile
from include.ui.controls.menus.base import ContextMenu2
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileListView

t = get_translation()
_ = t.gettext


class FileContextMenu(ContextMenu2):
    def __init__(
        self,
        file_id: str,
        filename: str,
        size: int,
        last_modified: float,
        parent_listview: "FileListView",
        ref: ft.Ref | None = None,
    ):
        self.page: ft.Page
        self.file_id = file_id
        self.filename = filename
        self.size = size
        self.last_modified = last_modified
        self.parent_listview = parent_listview

        self.app_shared = AppShared()

        # Instantiate ListTile
        assert self.app_shared.user_perference
        self.filetile = FileTile(
            filename=filename,
            file_id=file_id,
            size=size,
            last_modified=last_modified,
            starred=file_id
            in self.app_shared.user_perference.favourites.get("files", []),
            on_click=self.listtile_click,
        )

        self.controller = FileContextMenuController(self)

        super().__init__(
            self.filetile,
            on_enter=self.filetile_on_enter,
            on_exit=self.filetile_on_exit,
            ref=ref,
            menu_items=[
                {
                    "icon": ft.Icons.DELETE,
                    "content": _("Delete"),
                    "on_click": self.delete_button_click,
                },
                {
                    "icon": ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED,
                    "content": _("Rename"),
                    "on_click": self.rename_button_click,
                },
                {
                    "icon": ft.Icons.DRIVE_FILE_MOVE_OUTLINED,
                    "content": _("Move"),
                    "on_click": self.move_button_click,
                    "require": {"move"},
                },
                {
                    "icon": ft.Icons.LOCK_PERSON_OUTLINED,
                    "content": _("Authorize"),
                    "on_click": self.authorize_button_click,
                },
                {
                    "icon": ft.Icons.LIST_ALT,
                    "content": _("View Access Entries"),
                    "on_click": self.view_access_entries_button_click,
                    "require": {"view_access_entries"},
                },
                {
                    "icon": ft.Icons.SETTINGS_OUTLINED,
                    "content": _("Set Permissions"),
                    "on_click": self.set_access_rules_button_click,
                    "require": {"set_access_rules"},
                },
                {
                    "icon": ft.Icons.INFO_OUTLINED,
                    "content": _("Properties"),
                    "on_click": self.open_document_info_click,
                },
            ],
        )

    async def filetile_on_enter(self, event: ft.Event[ft.GestureDetector]):
        self.filetile.star_button.visible = True
        self.filetile.update()

    async def filetile_on_exit(self, event: ft.Event[ft.GestureDetector]):
        if not self.filetile.starred:
            self.filetile.star_button.visible = False
            self.filetile.update()

    async def listtile_click(self, event: ft.Event[ft.ListTile]):
        self.page.run_task(self.controller.action_open_file)

    async def delete_button_click(self, event: ft.Event[ft.PopupMenuItem]):
        self.page.run_task(self.controller.action_delete_file)

    async def rename_button_click(self, event: ft.Event[ft.PopupMenuItem]):
        self.page.run_task(self.controller.action_rename_file)

    async def move_button_click(self, event: ft.Event[ft.PopupMenuItem]):
        self.page.run_task(self.controller.action_move_file)

    async def authorize_button_click(self, event: ft.Event[ft.PopupMenuItem]):
        self.page.run_task(self.controller.action_authorize)

    async def view_access_entries_button_click(self, event: ft.Event[ft.PopupMenuItem]):
        self.page.run_task(self.controller.action_view_access_entries)

    async def set_access_rules_button_click(self, event: ft.Event[ft.PopupMenuItem]):
        self.page.run_task(self.controller.action_set_access_rules)

    async def open_document_info_click(self, event: ft.Event[ft.PopupMenuItem]):
        self.page.run_task(self.controller.action_open_document_info)


class DirectoryContextMenu(ContextMenu2):
    def __init__(
        self,
        parent_listview: "FileListView",
        directory_id: str,
        dir_name: str,
        created_at: float,
        ref: ft.Ref | None = None,
    ):

        self.page: ft.Page
        self.parent_listview = parent_listview
        self.controller = DirectoryContextMenuController(self)

        self.directory_id = directory_id
        self.dir_name = dir_name
        self.created_at = created_at

        # has to set manually
        self.app_shared = AppShared()

        # Instantiate ListTile
        assert self.app_shared.user_perference
        self.dirtile = DirectoryTile(
            dir_name=dir_name,
            directory_id=directory_id,
            created_at=created_at,
            starred=directory_id
            in self.app_shared.user_perference.favourites.get("directories", []),
            on_click=self.listtile_click,
        )

        __menu_items = [
            {
                "icon": ft.Icons.DELETE,
                "content": _("Delete"),
                "on_click": self.delete_button_click,
            },
            {
                "icon": ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED,
                "content": _("Rename"),
                "on_click": self.rename_button_click,
            },
            {
                "icon": ft.Icons.DRIVE_FILE_MOVE_OUTLINED,
                "content": _("Move"),
                "on_click": self.move_button_click,
                "require": {"move"},
            },
            {
                "icon": ft.Icons.LOCK_PERSON_OUTLINED,
                "content": _("Authorize"),
                "on_click": self.authorize_button_click,
            },
            {
                "icon": ft.Icons.LIST_ALT,
                "content": _("View Access Entries"),
                "on_click": self.view_access_entries_button_click,
                "require": {"view_access_entries"},
            },
            {
                "icon": ft.Icons.SETTINGS_OUTLINED,
                "content": _("Set Permissions"),
                "on_click": self.set_access_rules_button_click,
                "require": {"set_access_rules"},
            },
            {
                "icon": ft.Icons.INFO_OUTLINED,
                "content": _("Properties"),
                "on_click": self.open_directory_info_click,
            },
        ]

        # if not self.app_shared.is_mobile:
        #     __menu_items.extend(
        #         [
        #             {},
        #             {
        #                 "icon": (
        #                     ft.Icons.STAR_OUTLINED
        #                     if self.dirtile.starred
        #                     else ft.Icons.STAR_BORDER_OUTLINED
        #                 ),
        #                 "content": (
        #                     _("Star") if not self.dirtile.starred else _("Unstar")
        #                 ),
        #                 "on_click": self.dirtile.on_star_click,
        #             },
        #         ]
        #     )

        super().__init__(
            content=self.dirtile,
            on_enter=self.dirtile_on_enter,
            on_exit=self.dirtile_on_exit,
            menu_items=__menu_items,
            ref=ref,
        )

    async def dirtile_on_enter(self, event: ft.Event[ft.GestureDetector]):
        self.dirtile.star_button.visible = True
        self.dirtile.update()

    async def dirtile_on_exit(self, event: ft.Event[ft.GestureDetector]):
        if not self.dirtile.starred:
            self.dirtile.star_button.visible = False
            self.dirtile.update()

    async def listtile_click(self, event: ft.Event[ft.ListTile]):
        self.page.run_task(self.controller.action_open_directory)

    async def delete_button_click(self, event: ft.Event[ft.ListTile]):
        self.page.run_task(self.controller.action_delete_directory)

    async def rename_button_click(self, event: ft.Event[ft.ListTile]):
        self.page.run_task(self.controller.action_rename_directory)

    async def move_button_click(self, event: ft.Event[ft.ListTile]):
        self.page.run_task(self.controller.action_move_directory)

    async def authorize_button_click(self, event: ft.Event[ft.ListTile]):
        self.page.run_task(self.controller.action_authorize)

    async def view_access_entries_button_click(self, event: ft.Event[ft.ListTile]):
        self.page.run_task(self.controller.action_view_access_entries)

    async def set_access_rules_button_click(self, event: ft.Event[ft.ListTile]):
        self.page.run_task(self.controller.action_set_access_rules)

    async def open_directory_info_click(self, event: ft.Event[ft.ListTile]):
        self.page.run_task(self.controller.action_open_directory_info)
