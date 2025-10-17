from typing import TYPE_CHECKING
import gettext
from include.classes.config import AppConfig
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.dialogs.manage.accounts import PasswdUserDialog

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class PasswdDialogController:
    def __init__(self, dialog: "PasswdUserDialog"):
        self.dialog = dialog
        self.app_config = AppConfig()

    async def action_passwd_user(self):
        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            "set_passwd",
            data={
                "username": self.app_config.username,
                "old_passwd": self.dialog.old_passwd_field.value,
                "new_passwd": self.dialog.new_passwd_field.value,
            },  # 修改密码，无需 data 外提供 username 和 token
        )

        self.dialog.close()

        if response["code"] != 200:
            self.dialog.send_error(_(f"修改密码失败: {response['message']}"))
        else:
            assert self.dialog.page.platform
            if self.dialog.page.platform.value not in ["ios", "android"]:
                await self.dialog.page.window.close()
            else:
                self.dialog.send_error(_("您已登出，请手动重启应用"))
