import json, gettext
from typing import TYPE_CHECKING
from include.constants import LOCALE_PATH
from include.controllers.dialogs.rulemanager import RuleManagerController
from include.ui.controls.dialogs.base import AlertDialog
import flet as ft

if TYPE_CHECKING:
    from include.ui.controls.rightmenu.explorer import (
        DocumentRightMenuDialog,
        DirectoryRightMenuDialog,
    )

t = gettext.translation("client", LOCALE_PATH, fallback=True)
_ = t.gettext


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
        self.page: ft.Page
        self.controller = RuleManagerController(self)
        self.parent_dialog = parent_dialog

        self.progress_ring = ft.ProgressRing(visible=False)
        self.content_textfield = ft.TextField(
            label=_("Rule Content"),
            multiline=True,
            min_lines=16,
            # max_lines=16,
            expand=True,
            expand_loose=True,
        )
        self.content_info = ft.Markdown(
            "For rule format documentation, please refer to [CFMS Server Documentation]"
            "(https://cfms-server-doc.readthedocs.io/zh-cn/latest/"
            "groups_and_rights.html#match-rules)。",
            selectable=False,
            on_tap_link=self.on_link_tapped,
        )
        self.submit_button = ft.TextButton(
            _("Submit"), on_click=self.submit_button_click
        )

        self.title = "Rule Manager"
        self.content = ft.Container(
            content=ft.Tabs(
                ft.Column(
                    [
                        ft.TabBar(
                            [
                                ft.Tab(
                                    "Visualization",
                                ),
                                ft.Tab(
                                    "Source Code",
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
            ft.TextButton(_("Cancel"), on_click=lambda event: self.close()),
        ]

        self.object_id = object_id
        self.object_type = object_type

    async def on_link_tapped(self, event: ft.Event[ft.Markdown]):
        assert type(self.page) == ft.Page
        assert type(event.data) == str
        await self.page.launch_url(event.data)

    def did_mount(self):
        super().did_mount()
        self.page.run_task(self.controller.update_rule)

    def will_unmount(self): ...

    def lock_edit(self):
        self.content_textfield.disabled = True
        self.progress_ring.visible = True
        self.submit_button.visible = False
        self.content_textfield.error = None
        self.update()

    def unlock_edit(self):
        self.content_textfield.disabled = False
        self.progress_ring.visible = False
        self.submit_button.visible = True
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
            self.content_textfield.error = _("The submitted rule is not valid JSON")
            return

        self.page.run_task(self.controller.action_submit_rule, data)


class VisualRuleEditor(ft.Column):
    def __init__(self, manager: RuleManager):
        super().__init__()
        self.manager = manager

        self.actions = ft.ListView()
        self.current_edit_column = ft.Column([ft.Placeholder()])
        self.controls = [ft.Row([self.actions, self.current_edit_column])]
