import re

import flet as ft

from include.classes.shared import AppShared
from include.constants import (
    AUTO_CONNECT,
    DEFAULT_SERVER_ADDRESS,
    DEFAULT_WINDOW_TITLE,
    LOCK_SERVER_ADDRESS,
)
from include.controllers.connect import ConnectFormController
from include.ui import constants as const
from include.ui.util.notifications import send_error
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

# Regex patterns for validating wss:// server addresses
_WSS_PATTERN_V4 = r"^wss:\/\/[a-zA-Z0-9.-]+(:[0-9]+)?$"
_WSS_PATTERN_V6 = (
    r"^wss:\/\/\[(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}"
    r"|(?:[0-9a-fA-F]{1,4}:){6}:[0-9a-fA-F]{1,4}"
    r"|(?:[0-9a-fA-F]{1,4}:){5}(?::[0-9a-fA-F]{1,4}){1,2}"
    r"|(?:[0-9a-fA-F]{1,4}:){4}(?::[0-9a-fA-F]{1,4}){1,3}"
    r"|(?:[0-9a-fA-F]{1,4}:){3}(?::[0-9a-fA-F]{1,4}){1,4}"
    r"|(?:[0-9a-fA-F]{1,4}:){2}(?::[0-9a-fA-F]{1,4}){1,5}"
    r"|[0-9a-fA-F]{1,4}:(?::[0-9a-fA-F]{1,4}){1,6}"
    r"|:(?::[0-9a-fA-F]{1,4}){1,7})\](?::[0-9]{1,5})?$"
)
_WSS_PATTERN = _WSS_PATTERN_V4 + "|" + _WSS_PATTERN_V6


class ConnectForm(ft.Container):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page

        # Controller assignment
        self.controller = ConnectFormController(self)

        # Form style definitions
        self.width = const.FORM_WIDTH
        self.bgcolor = const.FIELD_BG
        self.border_radius = const.FORM_BORDER_RADIUS
        self.padding = 20

        # Form variable definitions
        self.app_shared = AppShared()

        # Form reference definitions

        # Form element definitions
        self.remote_address_textfield = ft.TextField(
            label=_("Server Address"),
            prefix="wss://",
            hint_text="e.g. localhost:5104",
            border_color=const.BORDER_COLOR,
            cursor_color=const.PRIMARY_COLOR,
            focused_border_color=const.PRIMARY_COLOR,
            bgcolor=const.FIELD_BG,
            color=const.TEXT_COLOR,
            hint_style=ft.TextStyle(color=const.PLACEHOLDER_COLOR),
            border_radius=8,
            value=DEFAULT_SERVER_ADDRESS,  # default (set by administrator)
            read_only=LOCK_SERVER_ADDRESS,  # lock editing if configured by administrator
            autofocus=True,
            on_submit=self.connect_button_click,  # Listen for the enter key event
            expand=True,
        )
        self.disable_ssl_enforcement_switch = ft.Switch(
            label=_("Disable SSL verification (Insecure)"),
            value=False,
            scale=1,
            label_text_style=ft.TextStyle(overflow=ft.TextOverflow.CLIP),  # no use?
        )

        self.connect_button = ft.Button(
            content=_("Connect"),
            bgcolor=const.PRIMARY_COLOR,
            color=const.TEXT_COLOR,
            on_click=self.connect_button_click,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=const.BUTTON_RADIUS),
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

    def did_mount(self):
        super().did_mount()
        self.page.title = DEFAULT_WINDOW_TITLE
        # make sure previous connection is closed, then auto-connect if configured
        assert isinstance(self.page, ft.Page)
        self.page.run_task(self._on_mount)

    async def _on_mount(self):
        await self.controller.close_previous_connection()
        if AUTO_CONNECT and DEFAULT_SERVER_ADDRESS:
            # Strip the protocol prefix in case the administrator included it
            raw_address = DEFAULT_SERVER_ADDRESS.removeprefix("wss://")
            server_address = "wss://" + raw_address
            if re.match(_WSS_PATTERN, server_address):
                self.disable_interactions()
                self.page.run_task(self.controller.action_connect, server_address)

    def will_unmount(self):
        super().will_unmount()
        self.enable_interactions()
        self.disable_ssl_enforcement_switch.value = False

    def send_error(self, message: str):
        send_error(self.page, message)

    def disable_interactions(self):
        self.connect_button.visible = False
        self.loading_animation.visible = True
        self.remote_address_textfield.disabled = True
        self.remote_address_textfield.error = None
        self.disable_ssl_enforcement_switch.disabled = True
        self.update()

    def enable_interactions(self):
        self.connect_button.visible = True
        self.loading_animation.visible = False
        self.remote_address_textfield.disabled = False
        self.remote_address_textfield.read_only = LOCK_SERVER_ADDRESS
        self.disable_ssl_enforcement_switch.disabled = False
        self.update()

    async def push_route(self, route: str):
        assert isinstance(self.page, ft.Page)
        await self.page.push_route(route)

    async def connect_button_click(
        self, event: ft.Event[ft.TextField] | ft.Event[ft.Button]
    ):
        assert type(self.page) == ft.Page
        yield self.disable_interactions()

        server_address = "wss://" + self.remote_address_textfield.value

        # Check if the server address matches the pattern
        if not server_address or not re.match(_WSS_PATTERN, server_address):
            self.remote_address_textfield.error = _("Invalid server address")
            self.enable_interactions()
            return  # Exit the function if the pattern is invalid

        self.page.run_task(self.controller.action_connect, server_address)
