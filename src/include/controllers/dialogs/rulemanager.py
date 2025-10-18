import json
from typing import TYPE_CHECKING, Any
import gettext
from include.classes.config import AppConfig
from include.constants import LOCALE_PATH
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.rulemanager import (
        RuleManager,
    )

t = gettext.translation("client", LOCALE_PATH, fallback=True)
_ = t.gettext


class RuleManagerController:
    def __init__(self, view: "RuleManager"):
        self.view = view
        self.app_config = AppConfig()

    async def update_rule(self):
        match self.view.object_type:
            case "document":
                action = "get_document_access_rules"
                data = {"document_id": self.view.object_id}
            case "directory":
                action = "get_directory_access_rules"
                data = {"directory_id": self.view.object_id}
            case _:
                raise ValueError(f"Invaild object type '{self.view.object_type}'")

        self.view.content_textfield.visible = False
        self.view.lock_edit()

        info_resp = await do_request(
            self.app_config.get_not_none_attribute("conn"),
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
            fetched_access_rules = info_resp["data"]
            self.view.content_textfield.value = json.dumps(
                fetched_access_rules, indent=4
            )
            self.view.unlock_edit()

        self.view.content_textfield.visible = True
        self.view.update()

    async def action_submit_rule(self, data: dict[str, Any]):
        match self.view.object_type:
            case "document":
                action = "set_document_rules"
                data["document_id"] = self.view.object_id

            case "directory":
                action = "set_directory_rules"
                data["directory_id"] = self.view.object_id
            case _:
                raise ValueError(f"Invaild object type '{self.view.object_type}'")

        submit_resp = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action,
            data,
            username=self.app_config.username,
            token=self.app_config.token,
        )

        if submit_resp["code"] != 200:
            self.view.send_error(_("Modification failed: {message}").format(message=submit_resp['message']))

        self.view.close()
