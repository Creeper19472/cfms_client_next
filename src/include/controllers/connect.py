from typing import TYPE_CHECKING
import os

import flet_permission_handler as fph

from include.constants import PROTOCOL_VERSION
from include.controllers.base import BaseController
from include.util.connect import get_connection
from include.util.requests import _request

if TYPE_CHECKING:
    from include.ui.controls.views.connect import ConnectForm

from include.util.locale import get_translation
t = get_translation()
_ = t.gettext


class ConnectFormController(BaseController["ConnectForm"]):
    def __init__(self, control: "ConnectForm"):
        super().__init__(control)

    async def close_previous_connection(self):
        if self.app_shared.conn:
            await self.app_shared.conn.close()

    async def action_connect(self, server_address: str):
        try:
            conn = await get_connection(
                server_address,
                self.control.disable_ssl_enforcement_switch.value,
                proxy=self.app_shared.preferences["settings"]["proxy_settings"],
                force_ipv4=self.app_shared.preferences["settings"].get("force_ipv4", False),
            )
        except ConnectionResetError as e:
            self.control.enable_interactions()
            if (
                e.strerror
            ):  # We'll use str.format() until Python 3.14 is supported by upstream
                errmsg = _(
                    "Connection failed because the connection was reset: {strerror}"
                ).format(strerror=e.strerror)
            else:
                errmsg = _("Connection failed because the connection was reset.")
            self.control.send_error(errmsg)
            return
        except Exception as e:
            self.control.enable_interactions()
            self.control.send_error(
                _("Connection failed: ({exc_class_name}) {str_err}").format(
                    exc_class_name=e.__class__.__name__, str_err=str(e)
                )
            )
            return

        server_info_response = await _request(conn, "server_info")
        if (
            server_protocol_version := server_info_response["data"]["protocol_version"]
        ) > PROTOCOL_VERSION:
            await conn.close()
            self.control.enable_interactions()
            self.control.send_error(
                _("You are connecting to a server using a higher version protocol")
                + " "
                + _(
                    "(Protocol version {server_protocol_version}), please update the client."
                ).format(server_protocol_version=server_protocol_version),
            )
            await self.control.push_route("/connect/about")
            return

        self.app_shared.server_address = server_address
        self.app_shared.server_info = server_info_response["data"]
        self.app_shared.conn = conn
        self.app_shared.disable_ssl_enforcement = (
            self.control.disable_ssl_enforcement_switch.value
        )

        self.control.page.title = f"CFMS Client - {server_address}"
        self.control.update()

        # temp fix
        ph_service = fph.PermissionHandler()

        assert self.app_shared.ph_service
        assert self.control.page.platform
        if (
            await ph_service.request(
                fph.Permission.MANAGE_EXTERNAL_STORAGE
            )
            == fph.PermissionStatus.DENIED
        ):
            if self.control.page.platform.value not in ["ios", "android"]:
                self.control.page.run_task(self.control.page.window.close)
            else:
                self.control.send_error(
                    _(
                        "Authorization failed, you will not be able to download files normally."
                    )
                    + " "
                    + _("Please allow the app to access your files in settings.")
                )

        if self.control.page.platform.value == "windows" and os.environ.get(
            "FLET_APP_CONSOLE"
        ):
            os.startfile(os.getcwd())

        await self.control.page.push_route("/login")
