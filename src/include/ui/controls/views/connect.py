import flet as ft
import flet_permission_handler as fph
import gettext, re, os
from include.classes.config import AppConfig
from include.constants import PROTOCOL_VERSION
from include.util.connect import get_connection
from include.util.communication import build_request
from include.ui import constants as const
from include.ui.util.notifications import send_error

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class ConnectForm(ft.Container):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)

        # Form style definitions
        self.width = const.FORM_WIDTH
        self.bgcolor = const.FIELD_BG
        self.border_radius = const.BUTTON_RADIUS
        self.padding = 20

        # Form variable definitions

        # Form reference definitions
        self.ph_ref = ft.Ref[fph.PermissionHandler]()

        # Form element definitions
        self.remote_address_textfield = ft.TextField(
            label=_("服务器地址"),
            prefix="wss://",
            hint_text="e.g. localhost:5104",
            border_color=const.BORDER_COLOR,
            cursor_color=const.PRIMARY_COLOR,
            focused_border_color=const.PRIMARY_COLOR,
            bgcolor=const.FIELD_BG,
            color=const.TEXT_COLOR,
            hint_style=ft.TextStyle(color=const.PLACEHOLDER_COLOR),
            border_radius=8,
            value=const.REMOTE_ADDRESS_PLACEHOLDER,  # default
            autofocus=True,
            on_submit=self.connect_button_click,  # Listen for the enter key event
            expand=True,
        )
        self.disable_ssl_enforcement_switch = ft.Switch(
            label=_("禁用SSL检查（不安全）"), value=False, scale=1
        )

        self.connect_button = ft.Button(
            content=_("连接"),
            bgcolor=const.PRIMARY_COLOR,
            color=const.TEXT_COLOR,
            on_click=self.connect_button_click,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=const.BUTTON_RADIUS)
            ),
        )
        self.loading_animation = ft.ProgressRing(visible=False)

        self.content = ft.Column(
            controls=[
                self.remote_address_textfield,
                self.disable_ssl_enforcement_switch,
                ft.Row(
                    controls=[
                        self.connect_button,
                        self.loading_animation,  # Add the loading animation next to the button
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
            ],
            spacing=15,
        )

    def build(self):
        # Add PermissionHandler service
        assert type(self.page) == ft.Page
        p = fph.PermissionHandler(
            ref=self.ph_ref  # pyright: ignore[reportArgumentType]
        )
        self.page._services.append(p)
        app_config = AppConfig()
        app_config.ph_service = p

    def disable_interactions(self):
        self.connect_button.visible = False
        self.loading_animation.visible = True
        self.remote_address_textfield.disabled = True
        self.disable_ssl_enforcement_switch.disabled = True

    def enable_interactions(self):
        self.connect_button.visible = True
        self.loading_animation.visible = False
        self.remote_address_textfield.disabled = False
        self.disable_ssl_enforcement_switch.disabled = False

    async def connect_button_click(
        self, event: ft.Event[ft.TextField] | ft.Event[ft.Button]
    ):
        assert type(self.page) == ft.Page
        yield self.disable_interactions()

        server_address = "wss://" + self.remote_address_textfield.value

        # Regular expression to match "wss://<valid server address>"
        wss_pattern_v4 = r"^wss:\/\/[a-zA-Z0-9.-]+(:[0-9]+)?$"
        wss_pattern_v6 = r"^wss:\/\/\[(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?::[0-9a-fA-F]{1,4}){1,6}|:(?::[0-9a-fA-F]{1,4}){1,7})\](?::[0-9]{1,5})?$"
        wss_pattern = wss_pattern_v4 + "|" + wss_pattern_v6

        # Check if the server address matches the pattern
        if not server_address or not re.match(wss_pattern, server_address):
            yield self.enable_interactions()
            send_error(self.page, _("无效的服务器地址"))
            return  # Exit the function if the pattern is invalid

        try:
            conn = await get_connection(
                server_address, self.disable_ssl_enforcement_switch.value
            )
        except Exception as e:
            yield self.enable_interactions()
            send_error(self.page, _(f"建立连接失败：{e}"))
            return

        server_info_response = await build_request(conn, "server_info")
        if (
            server_protocol_version := server_info_response["data"]["protocol_version"]
        ) > PROTOCOL_VERSION:
            await conn._wrapped_connection.close()
            yield self.enable_interactions()
            send_error(
                self.page,
                "您正在连接到一个使用更高版本协议的服务器"
                f"（协议版本 {server_protocol_version}），请更新客户端。",
            )
            await self.page.push_route("/connect/about")
            return

        # save connection ref
        self.page.session.store.set("conn", conn)

        # set session data
        self.page.session.store.set("server_info", server_info_response["data"])
        self.page.session.store.set("server_uri", server_address)

        app_config = AppConfig()
        app_config.server_address = server_address
        app_config.server_info = server_info_response["data"]
        app_config.conn = conn

        self.page.title = f"CFMS Client - {server_address}"
        yield

        assert self.ph_ref.current
        assert self.page.platform
        if (
            await self.ph_ref.current.request(fph.Permission.MANAGE_EXTERNAL_STORAGE)
            == fph.PermissionStatus.DENIED
        ):
            if self.page.platform.value not in ["ios", "android"]:
                self.page.run_task(self.page.window.close)
            else:
                send_error(
                    self.page,
                    _(
                        "授权失败，您将无法正常下载文件。"
                        "请在设置中允许应用访问您的文件。"
                    ),
                )

        if self.page.platform.value == "windows" and os.environ.get("FLET_APP_CONSOLE"):
            os.startfile(os.getcwd())

        await self.page.push_route("/login")
