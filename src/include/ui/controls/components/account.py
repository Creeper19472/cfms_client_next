import flet as ft

from include.classes.shared import AppShared
from include.ui.util.quotes import get_quote
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class AccountBadge(ft.Container):
    def __init__(
        self,
        visible: bool = True,
        ref: ft.Ref | None = None,
    ):
        super().__init__(visible=visible, ref=ref)
        self.page: ft.Page

        self.user_avatar = ft.CircleAvatar(
            content=None,
        )

        # Wrap avatar in a clickable container
        self.avatar_button = ft.GestureDetector(
            content=self.user_avatar,
            on_tap=self.on_avatar_click,
            mouse_cursor=ft.MouseCursor.CLICK,
            tooltip=_("Click to change avatar"),
        )

        self.username_text = ft.Text(color=ft.Colors.WHITE)
        self.quote_text = ft.Text()

        self.content = ft.Row(
            controls=[
                self.avatar_button,
                ft.Column(
                    controls=[
                        self.username_text,
                        self.quote_text,
                    ],
                    spacing=0,
                    expand=True,
                    expand_loose=True,
                ),
            ]
        )

    def did_mount(self):
        super().did_mount()
        self.update_avatar_display()
        self.quote_text.value = get_quote()

    def update_avatar_display(self):
        """Update the avatar display based on current AppShared state."""
        app_shared = AppShared()
        name = app_shared.nickname or app_shared.username

        # Create a new CircleAvatar instead of modifying the existing one
        if name is not None:
            self.username_text.value = name

            # Check if avatar_path exists and display it
            if app_shared.avatar_path:
                new_avatar = ft.CircleAvatar(
                    foreground_image_src=app_shared.avatar_path,
                    content=None,
                )
            else:
                # Fallback to letter-based avatar
                new_avatar = ft.CircleAvatar(
                    foreground_image_src=None,
                    content=ft.Text(name[0].upper()),
                )
        else:
            self.username_text.value = _("User")
            new_avatar = ft.CircleAvatar(
                foreground_image_src=None,
                content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE),
            )

        # Replace the old avatar with the new one
        self.user_avatar = new_avatar
        self.avatar_button.content = new_avatar

        self.update()

    async def on_avatar_click(self, event: ft.TapEvent):
        """Handle avatar click to open avatar settings dialog."""
        from include.ui.controls.dialogs.avatar_settings import AvatarSettingsDialog

        dialog = AvatarSettingsDialog(account_badge=self)
        self.page.show_dialog(dialog)
