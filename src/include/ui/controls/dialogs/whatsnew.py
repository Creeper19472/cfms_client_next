import flet as ft
import gettext
from datetime import date
from include.classes.changelog import ChangelogEntry
from include.ui.controls.dialogs.base import AlertDialog

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


changelogs = [
    ChangelogEntry(
        "v0.2.16",
        "Bug fixes",
        "This version fixes a variety of issues.",
        date(2025, 10, 18),
    ),
    ChangelogEntry(
        "v0.2.15",
        "Improved Code Structures",
        "This version added Controllers to separate the UI and "
        "logic, improving code readability and maintainability.",
        date(2025, 10, 17),
    ),
    ChangelogEntry(
        "v0.2.14",
        "Add Connection Settings",
        "This version adds some new connection settings that "
        "allow you to adjust the configuration of the "
        "application using the proxy.",
        date(2025, 10, 11),
    ),
    ChangelogEntry(
        "v0.2.12",
        "Major Feature Reintroduction Complete",
        """
Starting with this version, all the basic functionality that 
was already implemented in the old code branch has been 
reintroduced.
        
In addition to some silent features that are still waiting to 
be reintroduced, the following known issues are still waiting 
to be resolved:
        
- Significant lag when loading large amounts of data due to 
flet-datatable2
- When different dialog boxes are switched, the latter dialog 
box may not be displayed
- Minor issues with the updater
        """,
        date(2025, 10, 10),
    ),
    ChangelogEntry(
        "v0.2.11",
        "Restoring Full Functionality of the Group Management Interface",
        """This version completes the functionality of the user 
        group management interface that was already available in 
        previous code branches. At the same time, the storage structure 
        of some codes has also been adjusted.""",
        date(2025, 10, 9),
    ),
    ChangelogEntry(
        "v0.2.10",
        "Re-introducing Group Management Interface & Improvements",
        """This version reintroduces some features of the user group 
        management interface and optimizes the updater logic so that 
        it will check the local cache before starting to download 
        the update package.""",
        date(2025, 10, 8),
    ),
    ChangelogEntry(
        "v0.2.9",
        "Re-introducing Features for Development & Bug Fixes",
        """This version reintroduces several debugging features and 
        resolves an issue where exiting the app with the back key on a 
        mobile device would cause a crash on the next initial launch.""",
        date(2025, 10, 7),
    ),
    ChangelogEntry(
        "v0.2.8",
        "Bug fixes",
        """This version fixes a typo in the code that caused the updater 
        to refuse to check for updates in production environments. At the 
        same time, new entrances to view historical release notes have 
        been added to the "What's New" dialog and the "About" page to view 
        past updates.""",
        date(2025, 10, 6),
    ),
    ChangelogEntry(
        "v0.2.7",
        "Bug fixes",
        "This version fixes several issues with the app's built-in "
        "auto-updater, and now updates can be performed and displayed "
        "normally.",
        date(2025, 10, 6),
    ),
    ChangelogEntry(
        "v0.2.6",
        "Bug fixes",
        "This version corrects the application's compilation settings, "
        "which is expected to enable it to run on Android API 24 and above.",
        date(2025, 10, 6),
    ),
    ChangelogEntry(
        "v0.2.4",
        "Bug fixes",
        "This release introduces upstream fixes to the flet-open-file "
        "package, which is expected to resolve compilation failures "
        "that have persisted for the past few releases and make the "
        "updater experience smoother on mobile devices.",
        date(2025, 10, 5),
    ),
    ChangelogEntry(
        "v0.2.3",
        "Re-introducing Management Interfaces",
        "Starting from this version, the functionality of the "
        "management interface will be gradually reintroduced.",
        date(2025, 10, 5),
    ),
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


class ChangelogEntryColumn(ft.Column):
    def __init__(
        self,
        entry: ChangelogEntry,
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
                        _(f"  Released on {str(self.entry.date)}"),
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
        self.title = ft.Text(_(f"Changelogs"))

        self.entry_columns = [
            ChangelogEntryColumn(each_entry, leave_blank=True)
            for each_entry in changelogs
        ]

        self.content = ft.Container(
            ft.Column(
                [
                    ft.Text(_(f"Last updated on {str(changelogs[0].date)}\n")),
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
        self.title = ft.Text(_(f"What's new in {self.newest_changelog.version}"))

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
            self.page.shared_preferences.set, "whatsnew", self.newest_changelog.version
        )


if __name__ == "__main__":

    def main(page: ft.Page):
        page.show_dialog(WhatsNewDialog())

    ft.run(main)
