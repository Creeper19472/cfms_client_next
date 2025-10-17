import asyncio
import json
from typing import TYPE_CHECKING, Any, Callable, List
from include.classes.client import LockableClientConnection
from include.ui.controls.dialogs.base import AlertDialog
from include.util.requests import do_request
from include.ui.util.notifications import send_error
import flet as ft

if TYPE_CHECKING:
    from include.ui.controls.rightmenu.explorer import (
        DocumentRightMenuDialog,
        DirectoryRightMenuDialog,
    )


class RuleManager(AlertDialog):
    def __init__(
        self,
        parent_dialog: "DocumentRightMenuDialog|DirectoryRightMenuDialog",
        object_id: str,
        object_type: str,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.parent_dialog = parent_dialog

        self.progress_ring = ft.ProgressRing(visible=False)
        self.content_textfield = ft.TextField(
            label="规则内容",
            multiline=True,
            min_lines=16,
            # max_lines=16,
            expand=True,
            expand_loose=True,
        )
        self.content_info = ft.Markdown(
            "有关规则格式的说明，请参见 [CFMS 服务端文档]"
            "(https://cfms-server-doc.readthedocs.io/zh-cn/latest/"
            "groups_and_rights.html#match-rules)。",
            selectable=False,
            on_tap_link=self.on_link_tapped,
        )
        self.submit_button = ft.TextButton("提交", on_click=self.submit_button_click)

        self.title = "规则管理器"
        self.content = ft.Container(
            content=ft.Tabs(
                ft.Column(
                    [
                        ft.TabBar(
                            [
                                ft.Tab(
                                    "可视化",
                                ),
                                ft.Tab(
                                    "源代码",
                                ),
                            ]
                        ),
                        ft.TabBarView(
                            [
                                ft.Container(VisualRuleEditor(self)),
                                ft.Container(
                                    ft.Column(
                                        controls=[
                                            self.content_textfield,
                                            self.content_info,
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                    padding=ft.Padding(
                                        top=20, left=10, right=10, bottom=0
                                    ),
                                ),
                            ],
                            expand=True,
                        ),
                    ]
                ),
                length=2,
                animation_duration=ft.Duration(milliseconds=450),
            ),
            width=720,
            height=540,
        )
        self.actions = [
            self.progress_ring,
            self.submit_button,
            ft.TextButton("取消", on_click=lambda event: self.close()),
        ]

        # self.scrollable = True

        self.object_id = object_id
        self.object_type = object_type

    async def on_link_tapped(self, e: ft.Event[ft.Markdown]):
        assert type(self.page) == ft.Page
        assert type(e.data) == str
        await self.page.launch_url(e.data)

    def did_mount(self):
        super().did_mount()

        async def run():
            async for _ in self.update_rule():
                pass

        asyncio.create_task(run())

    def will_unmount(self): ...

    def lock_edit(self):
        self.content_textfield.disabled = True
        self.progress_ring.visible = True
        self.submit_button.visible = False

    def unlock_edit(self):
        self.content_textfield.disabled = False
        self.progress_ring.visible = False
        self.submit_button.visible = True

    async def update_rule(self):
        match self.object_type:
            case "document":
                action = "get_document_access_rules"
                data = {"document_id": self.object_id}
            case "directory":
                action = "get_directory_access_rules"
                data = {"directory_id": self.object_id}
            case _:
                raise ValueError(f"Invaild object type '{self.object_type}'")
        assert self.page

        self.content_textfield.visible = False
        yield self.lock_edit()

        assert type(self.page) == ft.Page
        conn = self.page.session.store.get("conn")
        assert type(conn) == LockableClientConnection

        info_resp = await do_request(
            conn,
            action,
            data,
            username=self.page.session.store.get("username"),
            token=self.page.session.store.get("token"),
        )
        if info_resp["code"] != 200:
            self.content_textfield.value = (
                f"Failed to fetch current rules: {info_resp['message']}"
            )
        else:
            self.fetched_access_rules = info_resp["data"]
            self.content_textfield.value = json.dumps(
                self.fetched_access_rules, indent=4
            )
            yield self.unlock_edit()

        self.content_textfield.visible = True
        self.update()

    async def submit_button_click(self, event: ft.Event[ft.TextButton]):
        assert self.page
        self.lock_edit()

        try:
            data = {
                "access_rules": (
                    json.loads(self.content_textfield.value)
                    if self.content_textfield.value
                    else {}
                ),
            }
        except json.decoder.JSONDecodeError:
            send_error(self.page, "提交的规则不是有效的JSON")
            self.close()
            return

        match self.object_type:
            case "document":
                action = "set_document_rules"
                data["document_id"] = self.object_id

            case "directory":
                action = "set_directory_rules"
                data["directory_id"] = self.object_id
            case _:
                raise ValueError(f"Invaild object type '{self.object_type}'")

        assert type(self.page) == ft.Page
        conn = self.page.session.store.get("conn")
        assert type(conn) == LockableClientConnection

        submit_resp = await do_request(
            conn,
            action,
            data,
            username=self.page.session.store.get("username"),
            token=self.page.session.store.get("token"),
        )

        if submit_resp["code"] != 200:
            send_error(self.page, f"修改失败：{submit_resp["message"]}")

        self.close()


class VisualRuleEditor(ft.Column):
    def __init__(self, manager: RuleManager):
        super().__init__()
        self.manager = manager

        self.actions = ft.ListView()
        self.current_edit_column = ft.Column([ft.Placeholder()])
        self.controls = [ft.Row([self.actions, self.current_edit_column])]
