from typing import TYPE_CHECKING

import flet as ft

from include.ui.controls.dialogs.contextmenu.explorer import (
    GetDirectoryInfoDialog,
    GetDocumentInfoDialog,
    RenameDialog,
)
from include.ui.controls.dialogs.authorize import AuthorizeDialog
from include.ui.controls.menus.base import RightMenuDialog
from include.ui.controls.components.rulemanager import RuleManager
from include.ui.util.notifications import send_error
from include.ui.util.path import get_directory
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileListView

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


# TODO: Replace current solution with ft.ContentMenu when flet supports it


class DocumentRightMenuDialog(RightMenuDialog):
    def __init__(
        self,
        document_id: str,
        parent_listview: "FileListView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        self.document_id = document_id
        self.user_permissions = []
        self.parent_listview = parent_listview
        self.access_settings_ref = ft.Ref[ft.ListTile]()

        super().__init__(
            title=ft.Text(_("Manage Documents")),
            menu_items=[
                {
                    "icon": ft.Icons.DELETE,
                    "title": _("Delete"),
                    "subtitle": _("Delete this file"),
                    "on_click": self.delete_button_click,
                },
                # {
                #     "icon": ft.Icons.DRIVE_FILE_MOVE_OUTLINED,
                #     "title": _("Move"),
                #     "subtitle": _("Move file to another location"),
                #     "handler": move_document,
                # },
                {
                    "icon": ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED,
                    "title": _("Rename"),
                    "subtitle": _("Rename this file"),
                    "on_click": self.rename_button_click,
                },
                {
                    "icon": ft.Icons.LOCK_PERSON_OUTLINED,
                    "title": _("Authorize"),
                    "subtitle": _("Grant temporary access to this file"),
                    "on_click": self.authorize_button_click,
                },
                {
                    "icon": ft.Icons.SETTINGS_OUTLINED,
                    "title": _("Set Permissions"),
                    "subtitle": _("Change access rules for this file"),
                    "on_click": self.set_access_rules_button_click,
                    "ref": self.access_settings_ref,
                    "require": {"set_access_rules"},
                },
                {
                    "icon": ft.Icons.INFO_OUTLINED,
                    "title": _("Properties"),
                    "subtitle": _("View file details"),
                    "on_click": self.open_document_info_click,
                },
            ],
            ref=ref,
            visible=visible,
        )

    def build(self):
        self.user_permissions = self.app_config.user_permissions
        assert self.access_settings_ref.current
        self.access_settings_ref.current.visible = (
            "set_access_rules" in self.user_permissions
        )

    def disable_interactions(self):
        self.menu_listview.disabled = True

    async def delete_button_click(self, event: ft.Event[ft.ListTile]):
        conn = self.app_config.get_not_none_attribute("conn")
        yield self.disable_interactions()

        response = await do_request(
            action="delete_document",
            data={"document_id": self.document_id},
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            send_error(
                event.page,
                _("Deletion failed: ({code}) {message}").format(
                    code=code, message=response["message"]
                ),
            )
        else:
            await get_directory(
                self.parent_listview.parent_manager.current_directory_id,
                self.parent_listview,
            )

        self.close()

    async def rename_button_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(RenameDialog("document", self.document_id, self.parent_listview))

    async def authorize_button_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(AuthorizeDialog("document", self.document_id, self.parent_listview))

    async def set_access_rules_button_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(RuleManager(self.document_id, "document"))

    async def open_document_info_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(GetDocumentInfoDialog(self.document_id))  # bug: not always showing


class DirectoryRightMenuDialog(RightMenuDialog):
    def __init__(
        self,
        directory_id: str,
        parent_listview: "FileListView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        self.directory_id = directory_id
        self.user_permissions = []
        self.parent_listview = parent_listview
        self.access_settings_ref = ft.Ref[ft.ListTile]()

        super().__init__(
            title=ft.Text(_("Manage Directories")),
            menu_items=[
                {
                    "icon": ft.Icons.DELETE,
                    "title": _("Delete"),
                    "subtitle": _("Delete this directory"),
                    "on_click": self.delete_button_click,
                },
                {
                    "icon": ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED,
                    "title": _("Rename"),
                    "subtitle": _("Rename this directory"),
                    "on_click": self.rename_button_click,
                },
                {
                    "icon": ft.Icons.LOCK_PERSON_OUTLINED,
                    "title": _("Authorize"),
                    "subtitle": _("Grant temporary access to this directory"),
                    "on_click": self.authorize_button_click,
                },
                {
                    "icon": ft.Icons.SETTINGS_OUTLINED,
                    "title": _("Set Permissions"),
                    "subtitle": _("Change access rules for this directory"),
                    "on_click": self.set_access_rules_button_click,
                    "ref": self.access_settings_ref,
                    "require": {"set_access_rules"},
                },
                {
                    "icon": ft.Icons.INFO_OUTLINED,
                    "title": _("Properties"),
                    "subtitle": _("View directory details"),
                    "on_click": self.open_directory_info_click,
                },
            ],
            ref=ref,
            visible=visible,
        )

    def build(self):
        self.user_permissions = self.app_config.user_permissions
        assert self.access_settings_ref.current
        self.access_settings_ref.current.visible = (
            "set_access_rules" in self.user_permissions
        )

    def disable_interactions(self):
        self.menu_listview.disabled = True

    async def delete_button_click(self, event: ft.Event[ft.ListTile]):
        conn = self.app_config.get_not_none_attribute("conn")
        yield self.disable_interactions()

        response = await do_request(
            action="delete_directory",
            data={"folder_id": self.directory_id},
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            send_error(
                event.page,
                _("Deletion failed: ({code}) {message}").format(
                    code=code, message=response["message"]
                ),
            )
        else:
            await get_directory(
                self.parent_listview.parent_manager.current_directory_id,
                self.parent_listview,
            )

        self.close()

    async def rename_button_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(RenameDialog("directory", self.directory_id, self.parent_listview))

    async def authorize_button_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(AuthorizeDialog("directory", self.directory_id, self.parent_listview))

    async def set_access_rules_button_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(RuleManager(self.directory_id, "directory"))

    async def open_directory_info_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(GetDirectoryInfoDialog(self.directory_id))
