import os

import flet as ft
from flet_material_symbols import Symbols

from include.classes.shared import AppShared
from include.constants import FLET_APP_STORAGE_DATA
from include.controllers.login import LoginFormController
from include.ui.util.notifications import send_error
from include.util.hash import get_server_hash, get_username_hash
from include.util.locale import get_translation
import include.ui.constants as const

t = get_translation()
_ = t.gettext


class LoginView(ft.Row):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.alignment = ft.MainAxisAlignment.CENTER
        self.vertical_alignment = ft.CrossAxisAlignment.STRETCH
        self.expand = True

        self.welcome_text = ft.Text(
            size=24,
            text_align=ft.TextAlign.CENTER,
            color=const.TEXT_COLOR,
            weight=ft.FontWeight.BOLD,
        )

        # Avatar preview positioned above the login form
        self.avatar_preview = AvatarPreviewContainer()

        # Create login form
        self.login_form = LoginForm(parent_view=self)
        self.login_form.avatar_preview = self.avatar_preview

        # Create data loading view (hidden initially)
        self.data_loading_view = DataLoadingView(visible=False)

        # Left side: Login area (avatar + form) with fixed width
        self.login_area = ft.Container(
            content=ft.Column(
                controls=[
                    self.welcome_text,
                    self.avatar_preview,
                    self.login_form,
                    self.data_loading_view,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.Alignment.CENTER,
            margin=10,
            expand=AppShared().is_mobile,
            expand_loose=AppShared().is_mobile,
        )

        if not AppShared().is_mobile:
            self.login_area.width = 450  # Fixed width for login area

        # Right side
        self.background_area = ft.Container(
            ft.Image("astronomy.jpg", fit=ft.BoxFit.COVER),
            expand=True,  # Takes remaining space
            margin=-10,
            bgcolor="#2E2E2E",  # ft.Colors.GREY_500,
            visible=not AppShared().is_mobile,
        )

        self.controls = [
            self.login_area,
            self.background_area,
        ]


class AvatarPreviewContainer(ft.Container):
    """Container that shows cached avatar preview based on username input."""

    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible, margin=ft.Margin(top=10))
        self.alignment = ft.Alignment.CENTER

        # Medium circular avatar for preview above login form
        self.preview_avatar = ft.CircleAvatar(
            radius=60,
            content=ft.Icon(Symbols.ACCOUNT_CIRCLE, size=80, color=ft.Colors.WHITE_38),
            # bgcolor=ft.Colors.TRANSPARENT,
        )

        self.content = self.preview_avatar

    def update_preview(self, username: str):
        """Update avatar preview based on username."""
        if not username or not username.strip():
            # No username, show default icon
            self.preview_avatar.foreground_image_src = None
            self.preview_avatar.content = ft.Icon(
                Symbols.ACCOUNT_CIRCLE, size=80, color=ft.Colors.WHITE_38
            )
            self.update()
            return

        # Try to find cached avatar for this username
        app_shared = AppShared()
        if app_shared.server_address and app_shared.server_address.strip():
            server_hash = get_server_hash(app_shared.server_address)
            username_hash = get_username_hash(username)
            avatar_cache_path = os.path.join(
                FLET_APP_STORAGE_DATA, "avatars", server_hash, username_hash
            )

            if os.path.exists(avatar_cache_path):
                # Show cached avatar
                self.preview_avatar.foreground_image_src = avatar_cache_path
                self.preview_avatar.content = None
                self.update()
                return

        # No cached avatar or no server address, show first letter of username
        self._set_letter_avatar(username)

    def _set_letter_avatar(self, username: str):
        """Set avatar to show the first letter of the username."""
        self.preview_avatar.foreground_image_src = None
        self.preview_avatar.content = ft.Text(
            username[0].upper(),
            size=50,
            weight=ft.FontWeight.BOLD,
        )
        self.update()


class DataLoadingView(ft.Container):
    """View shown while loading user data after successful login."""

    def __init__(self, ref: ft.Ref | None = None, visible=False):
        super().__init__(ref=ref, visible=visible, margin=ft.Margin(top=20))
        self.alignment = ft.Alignment.CENTER

        self.progress_ring = ft.ProgressRing()
        self.status_text = ft.Text(
            _("Loading user data"),
            size=16,
            text_align=ft.TextAlign.CENTER,
        )

        self.content = ft.Column(
            controls=[
                self.progress_ring,
                self.status_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        )

    def set_status(self, status_text: str):
        """Set the current loading status text."""
        self.status_text.value = status_text
        self.update()

    def clear_status(self):
        """Reset status text to default."""
        self.status_text.value = _("Loading user data")
        self.update()


class LoginForm(ft.Container):
    def __init__(
        self,
        parent_view: "LoginView",
        avatar_preview: "AvatarPreviewContainer | None" = None,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.parent_view = parent_view
        self.controller = LoginFormController(self)
        self.app_shared = AppShared()
        self.avatar_preview = avatar_preview

        # Form style definitions
        self.width = const.FORM_WIDTH
        self.bgcolor = const.FIELD_BG
        self.border_radius = const.FORM_BORDER_RADIUS
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
            on_change=self.username_changed,
            expand=True,
        )

        self.login_button = ft.IconButton(
            icon=Symbols.LOGIN,
            on_click=self.request_login,
            tooltip=_("Login"),
        )
        self.disconnect_button = ft.IconButton(
            icon=Symbols.CHEVRON_LEFT,
            on_click=self.disconnect_button_click,
            tooltip=_("Disconnect"),
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
        self.server_info = self.app_shared.server_info
        self.parent_view.welcome_text.value = (
            f"{self.server_info.get('server_name', 'CFMS Server')}"
        )

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

    def username_changed(self, e: ft.Event[ft.TextField]):
        """Update avatar preview when username changes."""
        if self.avatar_preview:
            username = self.username_field.value or ""
            self.avatar_preview.update_preview(username)

    async def disconnect_button_click(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route("/connect")

    async def request_login(self, e: ft.Event[ft.IconButton] | ft.Event[ft.TextField]):
        yield self.disable_interactions()

        # validate fields individually and set corresponding errors
        if not (self.username_field.value and self.username_field.value.strip()):
            self.username_field.error = _("Username cannot be empty")
        if not (self.password_field.value):
            self.password_field.error = _("Password cannot be empty")

        # if any error was set, re-enable interactions and return early
        if self.username_field.error or self.password_field.error:
            self.enable_interactions()
            return

        self.page.run_task(self.controller.action_login)
