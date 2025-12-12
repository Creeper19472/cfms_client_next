from typing import TYPE_CHECKING
import flet as ft

if TYPE_CHECKING:
    from include.classes.changelog import ChangelogEntry
    
from include.ui.controls.dialogs.base import AlertDialog
from include.util.changelog_parser import get_changelogs_from_file
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

# Load changelogs from the CHANGELOG.md file
changelogs = get_changelogs_from_file()


class ChangelogEntryColumn(ft.Column):
    def __init__(
        self,
        entry: "ChangelogEntry",
        leave_blank: bool = False,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.entry = entry
        self.controls = [
            ft.Text(
                f"{self.entry.version}: {self.entry.title}",
                size=21,
                spans=[
                    ft.TextSpan(
                        _("  Released on {release_date}").format(
                            release_date=str(self.entry.date)
                        ),
                        style=ft.TextStyle(14),
                    )
                ],
            ),
            ft.Markdown(self.entry.content),
            ft.Text("\n", size=7, visible=leave_blank),
        ]
        self.expand = True
        self.expand_loose = True


class ChangelogHistoryDialog(AlertDialog):
    def __init__(
        self,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(_("Changelogs"))

        self.entry_columns = [
            ChangelogEntryColumn(each_entry, leave_blank=True)
            for each_entry in changelogs
        ]

        self.content = ft.Container(
            ft.Column(
                [
                    ft.Text(
                        _("Last updated on {last_updated}\n").format(
                            last_updated=str(changelogs[0].date)
                        )
                    ),
                    *self.entry_columns,
                ]
            ),
            width=720,
        )
        self.actions = [
            ft.TextButton(_("OK"), on_click=self.ok_button_click),
        ]

    async def ok_button_click(self, event: ft.Event[ft.TextButton]):
        self.open = False
        self.update()


class WhatsNewDialog(AlertDialog):
    def __init__(
        self,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.newest_changelog = changelogs[0]

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(
            _("What's new in {newest_version}").format(
                newest_version=self.newest_changelog.version
            )
        )

        self.content = ft.Container(
            ChangelogEntryColumn(self.newest_changelog),
            width=680,
        )
        self.actions = [
            ft.TextButton(_("View history"), on_click=self.view_history_button_click),
            ft.TextButton(_("Got it!"), on_click=self.ok_button_click),
        ]

    async def ok_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def view_history_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()
        assert isinstance(self.page, ft.Page)
        self.page.run_thread(self.page.show_dialog, dialog=ChangelogHistoryDialog())

    def did_mount(self):
        super().did_mount()
        assert type(self.page) == ft.Page
        self.page.run_task(
            ft.SharedPreferences().set, "whatsnew", self.newest_changelog.version
        )


if __name__ == "__main__":

    def main(page: ft.Page):
        page.show_dialog(WhatsNewDialog())

    ft.run(main)
