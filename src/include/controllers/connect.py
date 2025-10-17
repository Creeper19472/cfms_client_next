import os
from typing import TYPE_CHECKING
import gettext
import flet_permission_handler as fph
from include.classes.config import AppConfig
from include.constants import PROTOCOL_VERSION
from include.util.connect import get_connection
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.views.connect import ConnectForm

t = gettext.translation("client", "ui/locale", fallback=True)
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
            if e.strerror:
                errmsg = _(f"建立连接失败，因为连接已重置: {e.strerror}")
            else:
                errmsg = _("建立连接失败，因为连接已重置。")
            self.view.send_error(errmsg)
            return
        except Exception as e:
            self.view.enable_interactions()
            self.view.send_error(_(f"建立连接失败：({e.__class__.__name__}) {str(e)}"))
            return

        server_info_response = await do_request(conn, "server_info")
        if (
            server_protocol_version := server_info_response["data"]["protocol_version"]
        ) > PROTOCOL_VERSION:
            await conn._wrapped_connection.close()
            self.view.enable_interactions()
            self.view.send_error(
                "您正在连接到一个使用更高版本协议的服务器"
                f"（协议版本 {server_protocol_version}），请更新客户端。",
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
                        "授权失败，您将无法正常下载文件。"
                        "请在设置中允许应用访问您的文件。"
                    ),
                )

        if self.view.page.platform.value == "windows" and os.environ.get(
            "FLET_APP_CONSOLE"
        ):
            os.startfile(os.getcwd())

        await self.view.page.push_route("/login")