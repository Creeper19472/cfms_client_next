import asyncio
import flet as ft
import gettext

from websockets import ClientConnection
from include.classes.client import LockableClientConnection
from include.classes.config import AppConfig
import include.ui.constants as const
from include.ui.util.notifications import send_error
from include.util.communication import build_request

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class LoginView(ft.Column):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.welcome_text = ft.Text(
            size=24,
            text_align=ft.TextAlign.CENTER,
            color=const.TEXT_COLOR,
            weight=ft.FontWeight.BOLD,
        )
        self.controls = [self.welcome_text, LoginForm()]


class LoginForm(ft.Container):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.parent: LoginView

        # Form style definitions
        self.width = const.FORM_WIDTH
        self.bgcolor = const.FIELD_BG
        self.border_radius = const.BUTTON_RADIUS
        self.padding = 20

        # Form variable definitions

        # Form reference definitions

        # Form element definitions

        self.password_field = ft.TextField(
            label=_("Password"),
            password=True,
            can_reveal_password=True,
            on_submit=self.request_login,
            expand=True,
        )
        self.username_field = ft.TextField(
            label=_("Username"),
            autofocus=True,
            on_submit=lambda e: e.page.run_task(  # type: ignore
                self.password_field.focus
            ),
            expand=True,
        )

        self.login_button = ft.Button(
            content=_("Login"),
            bgcolor=const.PRIMARY_COLOR,
            color=const.TEXT_COLOR,
            on_click=self.request_login,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=const.BUTTON_RADIUS)
            ),
        )
        self.loading_animation = ft.ProgressRing(visible=False)

        self.content = ft.Column(
            controls=[
                ft.Text(_("Login"), size=24),
                ft.Column(
                    controls=[
                        self.username_field,
                        self.password_field,
                        ft.Row(
                            controls=[
                                self.login_button,
                                self.loading_animation,
                            ]
                        ),
                    ]
                ),
            ],
            spacing=15,
        )

    def did_mount(self) -> None:
        assert type(self.page) == ft.Page
        self.server_info = self.page.session.store.get("server_info")
        assert type(self.server_info) == dict
        self.parent.welcome_text.value = (
            f"{self.server_info.get('server_name', 'CFMS Server')}"
        )
        # self.page.update()

    def disable_interactions(self):
        self.login_button.visible = False
        self.loading_animation.visible = True
        self.username_field.disabled = True
        self.password_field.disabled = True

    def enable_interactions(self):
        self.login_button.visible = True
        self.loading_animation.visible = False
        self.username_field.disabled = False
        self.password_field.disabled = False

    async def request_login(self, e: ft.Event[ft.Button] | ft.Event[ft.TextField]):
        assert type(self.page) == ft.Page
        yield self.disable_interactions()

        if self.username_field.value == "" or self.password_field.value == "":
            # empty fields show error
            yield self.enable_interactions()
            send_error(self.page, _("Username and Password cannot be empty"))
            return

        """
        Send request and handle response here
        use utils.build_request or utils.async_build_request to send your requests

        data = {"username": self.username_field.value, "password": self.password_field.value}
        login_resp = build_request(self.page, YOUR_FULL_LOGIN_URL, data, authenticated=False)
        token = json.loads(login_resp.text)

        #save the token to client storage (refresh and access tokens)
        for k in token:
            self.page.client_storage.set(k, token[k])
        """
        conn = self.page.session.store.get("conn")
        assert type(conn) == LockableClientConnection

        response = await build_request(
            conn,
            "login",
            {
                "username": self.username_field.value,
                "password": self.password_field.value,
            },
        )

        if (code := response["code"]) == 200:
            self.page.session.store.set("username", self.username_field.value)
            self.page.session.store.set("nickname", response["data"].get("nickname"))
            self.page.session.store.set("token", response["data"]["token"])
            self.page.session.store.set("exp", response["data"].get("exp"))
            self.page.session.store.set("user_permissions", response["data"]["permissions"])
            self.page.session.store.set("user_groups", response["data"]["groups"])

            app_config = AppConfig()
            app_config.username = self.username_field.value
            app_config.nickname = response["data"].get("nickname")
            app_config.token = response["data"]["token"]
            app_config.token_exp = response["data"].get("exp")
            app_config.user_permissions = response["data"]["permissions"]
            app_config.user_groups = response["data"]["groups"]

            self.username_field.value = ""
            self.password_field.value = ""
            yield self.enable_interactions()

            await self.page.push_route("/home")

        elif code == 403:
            self.page.session.store.set("username", self.username_field.value)
            # open_change_passwd_dialog(e, "在登录前必须修改密码。")
            yield self.enable_interactions()

        else:
            yield self.enable_interactions()
            send_error(self.page, f"登录失败：({code}) {response['message']}")
