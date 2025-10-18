import os
from typing import TYPE_CHECKING
import gettext
import flet_permission_handler as fph
from include.classes.config import AppConfig
from include.constants import LOCALE_PATH, PROTOCOL_VERSION
from include.util.connect import get_connection
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.views.connect import ConnectForm

t = gettext.translation("client", LOCALE_PATH, fallback=True)
_ = t.gettext


class ConnectFormController:
    def __init__(self, view: "ConnectForm"):
        self.view = view
        self.app_config = AppConfig()

    async def close_previous_connection(self):
        if self.app_config.conn:
            await self.app_config.conn.close()

    async def action_connect(self, server_address: str):
        try:
            conn = await get_connection(
                server_address,
                self.view.disable_ssl_enforcement_switch.value,
                proxy=self.app_config.preferences["settings"]["proxy_settings"],
            )
        except ConnectionResetError as e:
            self.view.enable_interactions()
            if (
                e.strerror
            ):  # We'll use str.format() until Python 3.14 is supported by upstream
                errmsg = _(
                    "Connection failed because the connection was reset: {strerror}"
                ).format(strerror=e.strerror)
            else:
                errmsg = _("Connection failed because the connection was reset.")
            self.view.send_error(errmsg)
            return
        except Exception as e:
            self.view.enable_interactions()
            self.view.send_error(
                _("Connection failed: ({exc_class_name}) {str_err}").format(
                    exc_class_name=e.__class__.__name__, str_err=str(e)
                )
            )
            return

        server_info_response = await do_request(conn, "server_info")
        if (
            server_protocol_version := server_info_response["data"]["protocol_version"]
        ) > PROTOCOL_VERSION:
            await conn._wrapped_connection.close()
            self.view.enable_interactions()
            self.view.send_error(
                _("You are connecting to a server using a higher version protocol")
                + " "
                + _(
                    "(Protocol version {server_protocol_version}), please update the client."
                ).format(server_protocol_version=server_protocol_version),
            )
            await self.view.push_route("/connect/about")
            return

        # save connection ref
        self.view.page.session.store.set("conn", conn)

        # set session data
        self.view.page.session.store.set("server_info", server_info_response["data"])
        self.view.page.session.store.set("server_uri", server_address)

        self.app_config.server_address = server_address
        self.app_config.server_info = server_info_response["data"]
        self.app_config.conn = conn

        self.view.page.title = f"CFMS Client - {server_address}"
        self.view.update()

        assert self.view.ph_ref.current
        assert self.view.page.platform
        if (
            await self.view.ph_ref.current.request(
                fph.Permission.MANAGE_EXTERNAL_STORAGE
            )
            == fph.PermissionStatus.DENIED
        ):
            if self.view.page.platform.value not in ["ios", "android"]:
                self.view.page.run_task(self.view.page.window.close)
            else:
                self.view.send_error(
                    _(
                        "Authorization failed, you will not be able to download files normally."
                    )
                    + " "
                    + _("Please allow the app to access your files in settings.")
                )

        if self.view.page.platform.value == "windows" and os.environ.get(
            "FLET_APP_CONSOLE"
        ):
            os.startfile(os.getcwd())

        await self.view.page.push_route("/login")
