import asyncio
import flet as ft
from flet_model import Model, route
from include.ui.controls.homepage import HomeView, HomeNavigationBar
from include.ui.controls.views.explorer import FileManagerView
from include.ui.controls.views.more import MoreView
from include.ui.controls.dialogs.whatsnew import WhatsNewDialog, changelogs


@route("home")
class HomeModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    # # UI Components
    # appbar = ft.AppBar(
    #     title=ft.Text("Home"),
    #     center_title=True,
    #     # bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
    # )

    def __init__(self, page: ft.Page):
        super().__init__(page)
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

        self.page.session.store.set("navigation_bar", self.navigation_bar)

    def post_init(self) -> None:
        self.file_picker = ft.FilePicker()
        self.page._services.append(self.file_picker)

        async def _check_whatsnew():
            if await self.page.shared_preferences.get("whatsnew") != changelogs[0].version:
                self.page.show_dialog(WhatsNewDialog())

        self.page.run_task(_check_whatsnew)

    #     self.page.session.store.set("load_directory", load_directory)
    #     self.page.session.store.set("current_directory_id", current_directory_id)
    #     self.page.session.store.set("initialization_complete", True)

    #     if self.page.session.store.get("server_info")[
    #         "lockdown"
    #     ] and "bypass_lockdown" not in self.page.session.store.get("user_permissions"):
    #         go_lockdown(self.page)
