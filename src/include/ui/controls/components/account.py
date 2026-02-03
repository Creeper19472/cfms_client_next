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

        self.user_avatar = ft.CircleAvatar(
            content=None,
        )
        self.username_text = ft.Text(color=ft.Colors.WHITE)
        self.quote_text = ft.Text()

        self.content = ft.Row(
            controls=[
                self.user_avatar,
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

        if (name := (AppShared().nickname or AppShared().username)) is not None:
            self.username_text.value = name
            self.user_avatar.content = ft.Text(name[0].upper())
        else:
            self.username_text.value = _("User")
            self.user_avatar.content = ft.Icon(ft.Icons.ACCOUNT_CIRCLE)

        self.quote_text.value = get_quote()
