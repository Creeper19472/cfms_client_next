from copy import deepcopy
from typing import TYPE_CHECKING, Any
import json

import flet as ft

from include.controllers.dialogs.rulemanager import (
    RuleManagerController,
    VisualRuleEditorController,
)
from include.ui.controls.components.visualmgr.editor import (
    VisualRuleEditorEditSection,
    VisualRuleEditorNavigationRail,
)
from include.ui.controls.dialogs.base import AlertDialog
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class RuleManager(AlertDialog):
    def __init__(
        self,
        object_id: str,
        object_type: str,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = RuleManagerController(self)

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
            _(
                "For rule format documentation, please refer to [CFMS Server Documentation]"
                "(https://cfms-server-doc.readthedocs.io/zh-cn/latest/access_control.html)."
            ),
            selectable=False,
            on_tap_link=self.on_link_tapped,
        )
        self.submit_button = ft.TextButton(
            _("Submit"), on_click=self.submit_button_click
        )

        self.title = _("Rule Manager")
        self.visual_editor = VisualRuleEditor(self)
        self.content = ft.Container(
            content=ft.Tabs(
                ft.Column(
                    [
                        ft.TabBar(
                            [
                                ft.Tab(
                                    _("Visualization"),
                                ),
                                ft.Tab(
                                    _("Source Code"),
                                ),
                            ]
                        ),
                        ft.TabBarView(
                            [
                                ft.Container(self.visual_editor),
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
                on_change=self.on_editor_change,
            ),
            width=720,
            height=540,
        )
        self.actions = [
            self.progress_ring,
            self.submit_button,
            ft.TextButton(_("Cancel"), on_click=lambda event: self.close()),
        ]

        self.cached_access_rules: dict[str, Any] = {}
        self.object_id = object_id
        self.object_type = object_type

    async def on_link_tapped(self, event: ft.Event[ft.Markdown]):
        assert type(self.page) == ft.Page
        assert type(event.data) == str
        await self.page.launch_url(event.data)

    async def on_editor_change(self, event: ft.Event[ft.Tabs]):
        if event.control.selected_index == 0:
            # Switch to visual editor
            self.content_textfield.error = None
            try:
                rules_data = (
                    json.loads(self.content_textfield.value)
                    if self.content_textfield.value
                    else {}
                )
            except json.decoder.JSONDecodeError:
                self.content_textfield.error = _("The submitted rule is not valid JSON")
                self.update()
                return

            # if edited text is valid JSON, update cache
            self.cached_access_rules = rules_data
            # set data for visual editor
            self.visual_editor.set_rule_data(self.cached_access_rules)
            await self.visual_editor.current_edit_section.load_rules()  # manually update

        elif event.control.selected_index == 1:
            # Switch to source code editor
            self.sync_editor_data()

    def did_mount(self):
        super().did_mount()
        self.page.run_task(self.controller.fetch_rule)

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

    def sync_editor_data(self):
        if self.visual_editor.modified:
            self.cached_access_rules = deepcopy(self.visual_editor.dict_data)
            self.content_textfield.value = json.dumps(
                self.cached_access_rules, indent=4
            )
            self.update()

    async def submit_button_click(self, event: ft.Event[ft.TextButton]):
        assert self.page
        self.lock_edit()
        self.sync_editor_data()

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
            self.unlock_edit()
            return

        self.page.run_task(self.controller.action_submit_rule, data)


class VisualRuleEditor(ft.Column):
    """
    The implementation class of visual rule editor.
    """

    def __init__(self, manager: RuleManager):
        super().__init__(expand=True, expand_loose=True)
        self.manager = manager
        self.controller = VisualRuleEditorController(self)

        self.cached_rule_data: dict[str, Any] = {}
        self.edited_rule_data: dict[str, Any] = {}

        self.current_edit_section: VisualRuleEditorEditSection = (
            VisualRuleEditorEditSection(self, "read")
        )
        self.current_edit_section_container = ft.Container(
            content=self.current_edit_section,
            align=ft.Alignment.TOP_CENTER,
            expand=True,
            expand_loose=True,
        )

        self.controls = [
            ft.Row(
                [
                    VisualRuleEditorNavigationRail(self),
                    self.current_edit_section_container,
                ],
                expand=True,
                expand_loose=True,
            ),
        ]

    def set_rule_data(self, data: dict[str, Any]):
        self.cached_rule_data = deepcopy(data)  # must be two different objects
        self.edited_rule_data = deepcopy(data)

    @property
    def dict_data(self) -> dict[str, Any]:
        self.edited_rule_data[self.current_edit_section.access_type] = (
            self.current_edit_section.dict_data
        )  # Ensure the current edit section's data is up to date
        return self.edited_rule_data

    @property
    def modified(self) -> bool:
        return self.dict_data != self.cached_rule_data
