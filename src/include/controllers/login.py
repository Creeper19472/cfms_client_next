from typing import TYPE_CHECKING
import gettext
from include.classes.client import LockableClientConnection
from include.classes.config import AppConfig
from include.ui.controls.dialogs.manage.accounts import PasswdUserDialog
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.views.login import LoginForm

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class LoginFormController:
    def __init__(self, view: "LoginForm"):
        self.view = view
        self.app_config = AppConfig()

    async def action_login(self):
        await self._action_login()
        self.view.enable_interactions()

    async def _action_login(self):
        username = self.view.username_field.value
        password = self.view.password_field.value

        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            "login",
            {
                "username": username,
                "password": password,
            },
        )

        if (code := response["code"]) == 200:
            # backports for session store: use app_config instead
            self.view.page.session.store.set("username", username)
            self.view.page.session.store.set(
                "nickname", response["data"].get("nickname")
            )
            self.view.page.session.store.set("token", response["data"]["token"])
            self.view.page.session.store.set("exp", response["data"].get("exp"))
            self.view.page.session.store.set(
                "user_permissions", response["data"]["permissions"]
            )
            self.view.page.session.store.set("user_groups", response["data"]["groups"])

            self.app_config.username = username
            self.app_config.nickname = response["data"].get("nickname")
            self.app_config.token = response["data"]["token"]
            self.app_config.token_exp = response["data"].get("exp")
            self.app_config.user_permissions = response["data"]["permissions"]
            self.app_config.user_groups = response["data"]["groups"]

            self.view.clear_fields()

            await self.view.page.push_route("/home")

        elif code == 403:
            self.view.page.session.store.set("username", username)
            self.view.page.show_dialog(PasswdUserDialog(_("在登录前必须修改密码。")))
            return

        else:
            self.view.send_error(_(f"登录失败：({code}) {response['message']}"))
