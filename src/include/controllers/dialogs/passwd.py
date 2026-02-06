from typing import TYPE_CHECKING

from include.controllers.base import Controller
from include.ui.util.notifications import send_success
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.dialogs.admin.accounts import PasswdUserDialog

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class PasswdDialogController(Controller["PasswdUserDialog"]):
    def __init__(self, control: "PasswdUserDialog"):
        super().__init__(control)

    async def action_passwd_user(self):
        response = await do_request(
            "set_passwd",
            data={
                "username": self.control.username,
                "old_passwd": self.control.old_passwd_field.value,
                "new_passwd": self.control.new_passwd_field.value,
                "bypass_passwd_requirements": self.control.bypass_requirements_checkbox.value,
                "force_update_after_login": self.control.force_update_after_login_checkbox.value,
            },  # Change password, username and token not required outside data
            username=self.app_shared.username if self.control.passwd_other else None,
            token=self.app_shared.token if self.control.passwd_other else None,
        )

        self.control.close()

        if response["code"] != 200:
            self.control.send_error(
                _("Change password failed: {message}").format(
                    message=response["message"]
                )
            )
        elif not self.control.passwd_other:
            assert self.control.page.platform
            if self.control.page.platform.value not in ["ios", "android"]:
                await self.control.page.window.close()
            else:
                self.control.send_error(
                    _(
                        "You have been logged out, please restart the application manually"
                    )
                )
        else:
            send_success(
                self.control.page,
                _("Password for user '{username}' changed successfully.").format(
                    username=self.control.username
                ),
            )
