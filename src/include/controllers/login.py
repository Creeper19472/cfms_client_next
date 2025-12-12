from typing import TYPE_CHECKING

from include.controllers.base import BaseController
from include.ui.controls.dialogs.admin.accounts import PasswdUserDialog
from include.util.requests import do_request
from include.util.user import load_user_preference

if TYPE_CHECKING:
    from include.ui.controls.views.login import LoginForm

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class LoginFormController(BaseController["LoginForm"]):
    def __init__(self, control: "LoginForm"):
        super().__init__(control)

    async def action_login(self):
        await self._action_login()
        self.control.enable_interactions()

    async def _action_login(self):
        username = self.control.username_field.value.strip()
        password = self.control.password_field.value

        response = await do_request(
            "login",
            {
                "username": username,
                "password": password,
            },
        )

        if (code := response["code"]) == 200:
            self.app_config.username = username
            self.app_config.nickname = response["data"].get("nickname")
            self.app_config.token = response["data"]["token"]
            self.app_config.token_exp = response["data"].get("exp")
            self.app_config.user_permissions = response["data"]["permissions"]
            self.app_config.user_groups = response["data"]["groups"]
            self.app_config.user_perference = load_user_preference(username)

            self.control.clear_fields()

            await self.control.page.push_route("/home")

        elif code == 403:
            self.control.page.show_dialog(
                PasswdUserDialog(
                    username, tip=_("Password must be changed before login.")
                )
            )
            return

        else:
            self.control.send_error(
                _("Login failed: ({code}) {message}").format(
                    code=code, message=response["message"]
                )
            )
