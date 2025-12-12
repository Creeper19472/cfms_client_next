from flet_model import Model, Router, route
import flet as ft

from include.ui.controls.components.homepage import HomeView, HomeNavigationBar
from include.ui.controls.dialogs.whatsnew import WhatsNewDialog, changelogs
from include.ui.controls.views.explorer import FileManagerView
from include.ui.controls.views.more import MoreView


@route("home")
class HomeModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)
        self.homeview = HomeView()
        self.controls = [
            ft.SafeArea(ft.Container()),
            FileManagerView(parent_model=self),
            ft.Container(),
            self.homeview,
            MoreView(self),
        ]
        self.navigation_bar = HomeNavigationBar(
            parent_view=self, views=self.controls[1:]
        )
        self.file_picker: ft.FilePicker

    def post_init(self) -> None:
        self.file_picker = ft.FilePicker()

        async def _popups_check():
            # check welcome
            # if not await self.page.shared_preferences.get("welcome_shown"):
            #     self.page.show_dialog(self.homeview.welcome_dialog)
            #     await self.page.shared_preferences.set("welcome_shown", True)

            # check whatsnew
            if await ft.SharedPreferences().get("whatsnew") != changelogs[0].version:
                self.page.show_dialog(WhatsNewDialog())

        self.page.run_task(_popups_check)

    #     self.page.session.store.set("load_directory", load_directory)
    #     self.page.session.store.set("current_directory_id", current_directory_id)
    #     self.page.session.store.set("initialization_complete", True)

    #     if self.page.session.store.get("server_info")[
    #         "lockdown"
    #     ] and "bypass_lockdown" not in self.page.session.store.get("user_permissions"):
    #         go_lockdown(self.page)
