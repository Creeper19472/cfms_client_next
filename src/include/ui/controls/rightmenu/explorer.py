from typing import TYPE_CHECKING
import flet as ft
import gettext
from include.classes.client import LockableClientConnection
from include.ui.controls.dialogs.base import AlertDialog
from include.ui.controls.dialogs.rightmenu.explorer import (
    GetDirectoryInfoDialog,
    GetDocumentInfoDialog,
    RenameDialog,
)
from include.ui.controls.rightmenu.base import RightMenuDialog
from include.ui.controls.rulemanager import RuleManager
from include.ui.util.notifications import send_error
from include.ui.util.path import get_directory
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileListView

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


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
            title=ft.Text(_(_("操作文档"))),
            menu_items=[
                {
                    "icon": ft.Icons.DELETE,
                    "title": _(_("删除")),
                    "subtitle": _(_("删除此文件")),
                    "on_click": self.delete_button_click,
                },
                # {
                #     "icon": ft.Icons.DRIVE_FILE_MOVE_OUTLINED,
                #     "title": _(_("移动")),
                #     "subtitle": _(_("将文件移动到其他位置")),
                #     "handler": move_document,
                # },
                {
                    "icon": ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED,
                    "title": "重命名",
                    "subtitle": _(_("重命名此文件")),
                    "on_click": self.rename_button_click,
                },
                {
                    "icon": ft.Icons.SETTINGS_OUTLINED,
                    "title": _(_("设置权限")),
                    "subtitle": _(_("对此文件的访问规则进行变更")),
                    "on_click": self.set_access_rules_button_click,
                    "ref": self.access_settings_ref,
                },
                {
                    "icon": ft.Icons.INFO_OUTLINED,
                    "title": _(_("属性")),
                    "subtitle": _(_("查看该文件的详细信息")),
                    "on_click": self.open_document_info_click,
                },
            ],
            ref=ref,
            visible=visible,
        )

    def build(self):
        assert type(self.page) == ft.Page
        self.user_permissions = self.page.session.store.get("user_permissions")
        assert type(self.user_permissions) == list
        assert self.access_settings_ref.current
        self.access_settings_ref.current.visible = (
            "set_access_rules" in self.user_permissions
        )

    def disable_interactions(self):
        self.menu_listview.disabled = True

    async def delete_button_click(self, event: ft.Event[ft.ListTile]):
        assert type(self.page) == ft.Page
        conn = self.page.session.store.get("conn")
        assert type(conn) == LockableClientConnection
        yield self.disable_interactions()

        response = await do_request(
            conn,
            action="delete_document",
            data={"document_id": self.document_id},
            username=self.page.session.store.get("username"),
            token=self.page.session.store.get("token"),
        )
        if (code := response["code"]) != 200:
            send_error(event.page, _(f"删除失败: ({code}) {response['message']}"))
        else:
            await get_directory(
                self.parent_listview.parent_manager.current_directory_id,
                self.parent_listview,
            )

        self.close()

    async def rename_button_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(RenameDialog(self, "document"))

    async def set_access_rules_button_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(RuleManager(self, self.document_id, "document"))

    async def open_document_info_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(GetDocumentInfoDialog(self))  # bug: not always showing


class DirectoryRightMenuDialog(AlertDialog):
    def __init__(
        self,
        directory_id: str,
        parent_listview: "FileListView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(_(_("操作目录")))

        self.directory_id = directory_id
        self.user_permissions = []
        self.parent_listview = parent_listview
        self.access_settings_ref = ft.Ref[ft.ListTile]()

        self.menu_listview = ft.ListView(
            controls=[
                ft.Column(
                    [
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.DELETE),
                            title=ft.Text(_("删除")),
                            subtitle=ft.Text(f_(_("删除此目录"))),
                            on_click=self.delete_button_click,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(
                                ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED
                            ),
                            title=ft.Text(_("重命名")),
                            subtitle=ft.Text(f_(_("重命名此目录"))),
                            on_click=self.rename_button_click,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.SETTINGS_OUTLINED),
                            title=ft.Text(_("设置权限")),
                            subtitle=ft.Text(f_(_("对此目录的访问规则进行变更"))),
                            on_click=self.set_access_rules_button_click,
                            ref=self.access_settings_ref,  # pyright: ignore[reportArgumentType]
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.INFO_OUTLINED),
                            title=ft.Text(_("属性")),
                            subtitle=ft.Text(f_(_("查看此目录的详细信息"))),
                            on_click=self.open_directory_info_click,
                        ),
                    ],
                )
            ]
        )
        self.content = ft.Container(self.menu_listview, width=480)

    def build(self):
        assert type(self.page) == ft.Page
        self.user_permissions = self.page.session.store.get("user_permissions")
        assert type(self.user_permissions) == list
        assert self.access_settings_ref.current
        self.access_settings_ref.current.visible = (
            "set_access_rules" in self.user_permissions
        )

    def disable_interactions(self):
        self.menu_listview.disabled = True

    async def delete_button_click(self, event: ft.Event[ft.ListTile]):
        assert type(self.page) == ft.Page
        conn = self.page.session.store.get("conn")
        assert type(conn) == LockableClientConnection
        yield self.disable_interactions()

        response = await do_request(
            conn,
            action="delete_directory",
            data={"folder_id": self.directory_id},
            username=self.page.session.store.get("username"),
            token=self.page.session.store.get("token"),
        )
        if (code := response["code"]) != 200:
            send_error(event.page, _(f"删除失败: ({code}) {response['message']}"))
        else:
            await get_directory(
                self.parent_listview.parent_manager.current_directory_id,
                self.parent_listview,
            )

        self.close()

    async def rename_button_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(RenameDialog(self, "directory"))

    async def set_access_rules_button_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(RuleManager(self, self.directory_id, "directory"))

    async def open_directory_info_click(self, event: ft.Event[ft.ListTile]):
        self.close()
        self.page.show_dialog(GetDirectoryInfoDialog(self))
