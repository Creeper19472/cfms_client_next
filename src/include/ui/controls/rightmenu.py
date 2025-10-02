from datetime import datetime
from typing import TYPE_CHECKING
import flet as ft
import gettext
from include.classes.client import LockableClientConnection
from include.ui.util.notifications import send_error
from include.ui.util.path import get_directory
from include.util.communication import build_request

if TYPE_CHECKING:
    from ui.controls.filemanager import FileListView
import asyncio

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class RenameDocumentDialog(ft.AlertDialog):
    def __init__(
        self,
        parent_dialog: "DocumentRightMenuDialog",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = False
        self.title = ft.Text(_("重命名文档"))

        self.parent_dialog = parent_dialog

        self.progress_ring = ft.ProgressRing(visible=False)

        self.document_textfield = ft.TextField(
            label=_("新文档名称"),
            on_submit=self.ok_button_click,
            expand=True,
        )
        self.textfield_empty_message = ft.Text(
            _("Document name cannot be empty"), color=ft.Colors.RED, visible=False
        )

        self.submit_button = ft.TextButton(
            _("提交"),
            on_click=self.ok_button_click,
        )
        self.cancel_button = ft.TextButton(_("取消"), on_click=self.cancel_button_click)

        self.content = ft.Column(
            controls=[self.document_textfield, self.textfield_empty_message],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.progress_ring, self.submit_button, self.cancel_button]

    def disable_interactions(self):
        self.document_textfield.disabled = True
        self.cancel_button.disabled = True
        self.submit_button.visible = False
        self.progress_ring.visible = True
        self.textfield_empty_message.visible = False
        self.document_textfield.border_color = None
        self.modal = False

    def enable_interactions(self):
        self.document_textfield.disabled = False
        self.cancel_button.disabled = False
        self.submit_button.visible = True
        self.progress_ring.visible = False
        self.modal = True

    async def ok_button_click(
        self, event: ft.Event[ft.TextButton] | ft.Event[ft.TextField]
    ):
        yield self.disable_interactions()

        if not (new_title := self.document_textfield.value):
            self.document_textfield.border_color = ft.Colors.RED
            self.textfield_empty_message.visible = True
            yield self.enable_interactions()
            return

        assert type(self.page) == ft.Page
        conn = self.page.session.store.get("conn")
        assert type(conn) == LockableClientConnection

        response = await build_request(
            conn,
            "rename_document",
            {
                "document_id": self.parent_dialog.document_id,
                "new_title": new_title,
            },
            "",
            self.page.session.store.get("username"),
            self.page.session.store.get("token"),
        )

        if (code := response["code"]) != 200:
            send_error(self.page, _(f"重命名失败: ({code}) {response['message']}"))
        else:
            await get_directory(
                self.parent_dialog.parent_listview.parent_manager.current_directory_id,
                self.parent_dialog.parent_listview,
            )

        self.open = False
        self.update()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.open = False
        self.update()


class GetDocumentInfoDialog(ft.AlertDialog):
    def __init__(
        self,
        parent_dialog: "DocumentRightMenuDialog",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = False
        self.title = ft.Row(
            controls=[
                ft.Text(_("文档详情")),
                ft.IconButton(
                    ft.Icons.REFRESH,
                    on_click=self.refresh_button_click,
                ),
            ]
        )

        self.parent_dialog = parent_dialog

        self.progress_ring = ft.ProgressRing(visible=False)
        self.cancel_button = ft.TextButton(_("取消"), on_click=self.cancel_button_click)

        self.info_listview = ft.ListView(visible=False)

        self.content = ft.Column(
            controls=[self.progress_ring, self.info_listview],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.cancel_button]

    def did_mount(self):
        async def run():
            async for _ in self.request_document_info():
                pass
        asyncio.create_task(run())

    def close(self):
        self.open = False
        self.update()

    def disable_interactions(self):
        self.progress_ring.visible = True
        self.info_listview.visible = False

    def enable_interactions(self):
        self.progress_ring.visible = False
        self.info_listview.visible = True

    async def request_document_info(self):

        yield self.disable_interactions()

        assert type(self.page) == ft.Page
        conn = self.page.session.store.get("conn")
        assert type(conn) == LockableClientConnection

        response = await build_request(
            conn,
            action="get_document_info",
            data={
                "document_id": self.parent_dialog.document_id,
            },
            username=self.page.session.store.get("username"),
            token=self.page.session.store.get("token"),
        )
        if (code := response["code"]) != 200:
            self.close()
            send_error(
                self.page,
                _(f"拉取文档信息失败: ({code}) {response['message']}"),
            )
        else:
            self.info_listview.controls = [
                ft.Text(
                    f"文档ID: {response['data']['document_id']}", selectable=True
                ),
                ft.Text(f"文档标题: {response['data']['title']}", selectable=True),
                ft.Text(f"文档大小: {response['data']['size']}"),
                ft.Text(
                    f"创建于: {datetime.fromtimestamp(response['data']['created_time']).strftime('%Y-%m-%d %H:%M:%S')}",
                ),
                ft.Text(
                    f"最后更改时间: {datetime.fromtimestamp(response['data']['last_modified']).strftime('%Y-%m-%d %H:%M:%S')}",
                ),
                ft.Text(
                    f"父级目录ID: {response['data']['parent_id']}", selectable=True
                ),
                ft.Text(
                    f"访问规则: {response['data']['access_rules'] if not response['data']['info_code'] else 'Unavailable'}",
                    selectable=True,
                ),
            ]
            self.enable_interactions()
            self.update()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    refresh_button_click = request_document_info


class DocumentRightMenuDialog(ft.AlertDialog):
    def __init__(
        self,
        document_id: str,
        # triggered_event: ft.TapEvent[ft.GestureDetector],
        # triggered_detector: ft.GestureDetector,
        parent_listview: "FileListView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(_("操作文档"))

        self.document_id = document_id
        # self.triggered_event = triggered_event
        # self.triggered_detector = triggered_detector
        self.parent_listview = parent_listview
        self.user_permissions = []

        self.menu_listview = ft.ListView(
            controls=[
                ft.Column(
                    [
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.DELETE),
                            title=ft.Text("删除"),
                            subtitle=ft.Text(f"删除此文件"),
                            on_click=self.delete_button_click,
                        ),
                        # ft.ListTile(
                        #     leading=ft.Icon(ft.Icons.DRIVE_FILE_MOVE_OUTLINED),
                        #     title=ft.Text("移动"),
                        #     subtitle=ft.Text(f"将文件移动到其他位置"),
                        #     on_click=move_document,
                        # ),
                        ft.ListTile(
                            leading=ft.Icon(
                                ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED
                            ),
                            title=ft.Text("重命名"),
                            subtitle=ft.Text(f"重命名此文件"),
                            on_click=self.rename_button_click,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.SETTINGS_OUTLINED),
                            title=ft.Text("设置权限"),
                            subtitle=ft.Text(f"对此文件的访问规则进行变更"),
                            on_click=self.set_access_rules_button_click,
                            visible="set_access_rules" in self.user_permissions,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.INFO_OUTLINED),
                            title=ft.Text("属性"),
                            subtitle=ft.Text(f"查看该文件的详细信息"),
                            on_click=self.open_document_info_click,
                        ),
                    ],
                )
            ]
        )
        self.content = ft.Container(self.menu_listview, width=480)

    def did_mount(self):
        assert type(self.page) == ft.Page
        self.user_permissions = self.page.session.store.get("user_permissions")

    def disable_interactions(self):
        self.menu_listview.disabled = True

    async def delete_button_click(self, event: ft.Event[ft.ListTile]):
        assert type(self.page) == ft.Page
        conn = self.page.session.store.get("conn")
        assert type(conn) == LockableClientConnection
        yield self.disable_interactions()

        response = await build_request(
            conn,
            action="delete_document",
            data={"document_id": self.document_id},
            username=self.page.session.store.get("username"),
            token=self.page.session.store.get("token"),
        )
        if (code := response["code"]) != 200:
            send_error(event.page, f"删除失败: ({code}) {response['message']}")
        else:
            await get_directory(
                self.parent_listview.parent_manager.current_directory_id,
                self.parent_listview,
            )

        self.open = False
        self.update()

    async def rename_button_click(self, event: ft.Event[ft.ListTile]):
        self.open = False
        self.update()
        self.page.show_dialog(RenameDocumentDialog(self))

    async def set_access_rules_button_click(self, event: ft.Event[ft.ListTile]): ...

    async def open_document_info_click(self, event: ft.Event[ft.ListTile]):
        self.open = False
        self.update()
        self.page.show_dialog(GetDocumentInfoDialog(self)) # bug: not always showing
