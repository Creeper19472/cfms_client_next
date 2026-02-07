import hashlib
import os

import flet as ft

from include.classes.shared import AppShared
from include.constants import FLET_APP_STORAGE_DATA
from include.controllers.login import LoginFormController
from include.ui.util.notifications import send_error
from include.util.locale import get_translation
import include.ui.constants as const

t = get_translation()
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
        
        # Create avatar preview container (right side)
        self.avatar_preview = AvatarPreviewContainer()
        
        # Create login form (left side)
        self.login_form = LoginForm(avatar_preview=self.avatar_preview)
        
        # Create data loading view (hidden initially)
        self.data_loading_view = DataLoadingView(visible=False)
        
        # Main content row with form on left and avatar preview on right
        self.content_row = ft.Row(
            controls=[
                ft.Container(
                    content=self.login_form,
                    width=400,
                ),
                self.avatar_preview,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
        
        self.controls = [
            self.welcome_text,
            self.content_row,
            self.data_loading_view,
        ]


class AvatarPreviewContainer(ft.Container):
    """Container that shows cached avatar preview based on username input."""
    
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.expand = True
        self.alignment = ft.alignment.center
        
        # Large circular avatar for preview
        self.preview_avatar = ft.CircleAvatar(
            radius=100,
            content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=120, color=ft.Colors.WHITE38),
        )
        
        self.content = self.preview_avatar
    
    def update_preview(self, username: str):
        """Update avatar preview based on username."""
        if not username or not username.strip():
            # No username, show default icon
            self.preview_avatar.foreground_image_src = None
            self.preview_avatar.content = ft.Icon(
                ft.Icons.ACCOUNT_CIRCLE, size=120, color=ft.Colors.WHITE38
            )
            self.update()
            return
        
        # Try to find cached avatar for this username
        app_shared = AppShared()
        if app_shared.server_address:
            server_hash = hashlib.sha256(
                app_shared.server_address.encode()
            ).hexdigest()[:16]
            avatar_cache_path = os.path.join(
                FLET_APP_STORAGE_DATA, "avatars", server_hash, f"{username}.png"
            )
            
            if os.path.exists(avatar_cache_path):
                # Show cached avatar
                self.preview_avatar.foreground_image_src = avatar_cache_path
                self.preview_avatar.content = None
            else:
                # No cached avatar, show first letter of username
                self.preview_avatar.foreground_image_src = None
                self.preview_avatar.content = ft.Text(
                    username[0].upper(),
                    size=80,
                    weight=ft.FontWeight.BOLD,
                )
        else:
            # No server address, show first letter
            self.preview_avatar.foreground_image_src = None
            self.preview_avatar.content = ft.Text(
                username[0].upper(),
                size=80,
                weight=ft.FontWeight.BOLD,
            )
        
        self.update()


class DataLoadingView(ft.Container):
    """View shown while loading user data after successful login."""
    
    def __init__(self, ref: ft.Ref | None = None, visible=False):
        super().__init__(ref=ref, visible=visible)
        self.alignment = ft.alignment.center
        
        self.progress_ring = ft.ProgressRing()
        self.status_text = ft.Text(
            _("Loading user data..."),
            size=16,
            text_align=ft.TextAlign.CENTER,
        )
        
        # List of loading steps (extensible for future)
        self.steps_column = ft.Column(
            controls=[],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
        )
        
        self.content = ft.Column(
            controls=[
                self.progress_ring,
                self.status_text,
                self.steps_column,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        )
    
    def add_step(self, step_text: str):
        """Add a loading step to the display."""
        self.steps_column.controls.append(
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=16),
                    ft.Text(step_text, size=12),
                ],
                spacing=5,
            )
        )
        self.update()
    
    def clear_steps(self):
        """Clear all loading steps."""
        self.steps_column.controls.clear()
        self.update()


class LoginForm(ft.Container):
    def __init__(
        self,
        avatar_preview: "AvatarPreviewContainer | None" = None,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.parent: LoginView
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
            icon=ft.Icons.LOGIN_OUTLINED,
            on_click=self.request_login,
            tooltip=_("Login"),
        )
        self.disconnect_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
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
        self.parent.welcome_text.value = (
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
    
    def username_changed(self, e: ft.ControlEvent):
        """Update avatar preview when username changes."""
        if self.avatar_preview:
            username = self.username_field.value or ""
            self.avatar_preview.update_preview(username)

    async def disconnect_button_click(self, event: ft.Event[ft.IconButton]):
        assert isinstance(self.page, ft.Page)
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
