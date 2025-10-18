import flet as ft
import gettext

from include.constants import LOCALE_PATH
from include.controllers.login import LoginFormController
import include.ui.constants as const
from include.ui.util.notifications import send_error

t = gettext.translation("client", LOCALE_PATH, fallback=True)
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
        self.page: ft.Page
        self.parent: LoginView
        self.controller = LoginFormController(self)

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

        self.login_button = ft.IconButton(
            icon=ft.Icons.LOGIN_OUTLINED, on_click=self.request_login, tooltip="Login"
        )
        self.disconnect_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            on_click=self.disconnect_button_click,
            tooltip="Disconnect",
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
                                self.disconnect_button,
                                self.loading_animation,
                                self.login_button,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
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
        self.disconnect_button.disabled = True

        # clear previous errors
        self.username_field.error = None
        self.password_field.error = None
        self.update()

    def enable_interactions(self):
        self.login_button.visible = True
        self.loading_animation.visible = False
        self.username_field.disabled = False
        self.password_field.disabled = False
        self.disconnect_button.disabled = False
        self.update()

    def clear_fields(self):
        self.username_field.value = ""
        self.password_field.value = ""
        self.update()

    def send_error(self, message: str):
        send_error(self.page, message)

    async def disconnect_button_click(self, event: ft.Event[ft.IconButton]):
        assert isinstance(self.page, ft.Page)
        await self.page.push_route("/connect")

    async def request_login(self, e: ft.Event[ft.IconButton] | ft.Event[ft.TextField]):
        yield self.disable_interactions()

        # validate fields individually and set corresponding errors
        if not (self.username_field.value and self.username_field.value.strip()):
            self.username_field.error = _("Username cannot be empty")
        if not (self.password_field.value and self.password_field.value.strip()):
            self.password_field.error = _("Password cannot be empty")

        # if any error was set, re-enable interactions and return early
        if self.username_field.error or self.password_field.error:
            self.enable_interactions()
            return

        self.page.run_task(self.controller.action_login)

        
