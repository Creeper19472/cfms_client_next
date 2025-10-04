import flet as ft
import gettext
from datetime import date
from include.classes.changelog import ChangelogEntry

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


changelogs = [
    ChangelogEntry(
        "v0.2.2",
        "Introducing Whats'new Dialog",
        "From now on, a Whats'new dialog will be displayed when "
        "the app is upgraded from older versions or newly installed.",
        date(2025, 10, 4),
    ),
    ChangelogEntry(
        "v0.2.0",
        "Introducing The First Version of CFMS Client (NEXT)",
        "This version re-implemented widely-used functions to give "
        "more convenience to developers.",
        date(2025, 10, 4),
    ),
]


class WhatsNewDialog(ft.AlertDialog):
    def __init__(
        self,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.newest_changelog = changelogs[0]

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(_(f"What's new in {self.newest_changelog.version}"))

        self.content = ft.Container(ft.Column(
            [
                ft.Text(f"发行于 {str(self.newest_changelog.date)}\n"),
                ft.Text(self.newest_changelog.title, size=20),
                ft.Markdown(self.newest_changelog.content),
            ]
        ), width=680)
        self.actions = [ft.TextButton("Got it!", on_click=self.ok_button_click)]

    async def ok_button_click(self, event: ft.Event[ft.TextButton]):
        self.open = False
        self.update()

    def did_mount(self):
        super().did_mount()
        assert type(self.page) == ft.Page
        self.page.run_task(
            self.page.shared_preferences.set, "whatsnew", self.newest_changelog.version
        )


if __name__ == "__main__":

    def main(page: ft.Page):
        page.show_dialog(WhatsNewDialog())

    ft.run(main)
