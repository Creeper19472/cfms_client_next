from typing import TYPE_CHECKING, Any
import json

from include.classes.config import AppConfig
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.components.rulemanager import RuleManager, VisualRuleEditor

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class RuleManagerController:
    def __init__(self, view: "RuleManager"):
        self.view = view
        self.app_config = AppConfig()

    async def fetch_rule(self):
        match self.view.object_type:
            case "document":
                action = "get_document_access_rules"
                data = {"document_id": self.view.object_id}
            case "directory":
                action = "get_directory_access_rules"
                data = {"directory_id": self.view.object_id}
            case _:
                raise ValueError(f"Invalid object type '{self.view.object_type}'")

        self.view.content_textfield.visible = False
        self.view.lock_edit()

        info_resp = await do_request(
            action,
            data,
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if info_resp["code"] != 200:
            self.view.content_textfield.value = (
                f"Failed to fetch current rules: {info_resp['message']}"
            )
        else:
            self.view.cached_access_rules = info_resp["data"]
            self.view.content_textfield.value = json.dumps(
                self.view.cached_access_rules, indent=4
            )
            self.view.unlock_edit()

        self.view.content_textfield.visible = True
        self.view.update()

        self.view.visual_editor.set_rule_data(self.view.cached_access_rules)
        await self.view.visual_editor.current_edit_section.load_rules()

    async def action_submit_rule(self, data: dict[str, Any]):
        match self.view.object_type:
            case "document":
                action = "set_document_rules"
                data["document_id"] = self.view.object_id

            case "directory":
                action = "set_directory_rules"
                data["directory_id"] = self.view.object_id
            case _:
                raise ValueError(f"Invalid object type '{self.view.object_type}'")

        submit_resp = await do_request(
            action,
            data,
            username=self.app_config.username,
            token=self.app_config.token,
        )

        if submit_resp["code"] != 200:
            self.view.send_error(
                _("Modification failed: {message}").format(
                    message=submit_resp["message"]
                )
            )

        self.view.close()


class VisualRuleEditorController:
    def __init__(self, view: "VisualRuleEditor"):
        self.view = view
        self.app_config = AppConfig()
