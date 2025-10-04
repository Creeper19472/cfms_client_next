import flet as ft
import gettext

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class WhatsNewDialog(ft.AlertDialog):
    def __init__(
        self,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = False
        self.title = ft.Text(_("What's new"))

        self.changelog_column = ft.Column([ft.Markdown("")])
