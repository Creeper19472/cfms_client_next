from typing import TYPE_CHECKING, Any
import json

from include.classes.shared import AppShared
from include.controllers.base import Controller
from include.ui.util.notifications import send_error
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.components.rulemanager import RuleManager, VisualRuleEditor

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class RuleManagerController(Controller["RuleManager"]):
    def __init__(self, control: "RuleManager"):
        super().__init__(control)

    async def fetch_rule(self):
        match self.control.object_type:
            case "document":
                action = "get_document_access_rules"
                data = {"document_id": self.control.object_id}
            case "directory":
                action = "get_directory_access_rules"
                data = {"directory_id": self.control.object_id}
            case _:
                raise ValueError(f"Invalid object type '{self.control.object_type}'")

        self.control.source_editor.visible = False
        self.control.lock_edit()

        info_resp = await do_request(
            action,
            data,
            username=self.app_shared.username,
            token=self.app_shared.token,
        )
        if info_resp["code"] != 200:
            send_error(
                self.control.page,
                _("Failed to fetch rules: {message}").format(
                    message=info_resp["message"]
                ),
            )
            self.control.close()
            return
        else:
            self.control.cached_access_rules = info_resp["data"]["rules"]
            self.control.inherit_checkbox.value = info_resp["data"]["inherit"]
            self.control.source_editor.value = json.dumps(
                self.control.cached_access_rules, indent=4
            )
            self.control.unlock_edit()

        self.control.source_editor.visible = True
        self.control.update()

        self.control.visual_editor.set_rule_data(self.control.cached_access_rules)
        await self.control.visual_editor.current_edit_section.load_rules()

    async def action_submit_rule(self, data: dict[str, Any]):
        match self.control.object_type:
            case "document":
                action = "set_document_rules"
                data["document_id"] = self.control.object_id

            case "directory":
                action = "set_directory_rules"
                data["directory_id"] = self.control.object_id
            case _:
                raise ValueError(f"Invalid object type '{self.control.object_type}'")

        submit_resp = await do_request(
            action,
            data,
            username=self.app_shared.username,
            token=self.app_shared.token,
        )

        if submit_resp["code"] != 200:
            self.control.send_error(
                _("Modification failed: {message}").format(
                    message=submit_resp["message"]
                )
            )

        self.control.close()


class VisualRuleEditorController:
    def __init__(self, view: "VisualRuleEditor"):
        self.view = view
        self.app_shared = AppShared()
