import flet as ft
from flet_model import Model, route
from include.ui.controls.homepage import HomeView, HomeNavigationBar
from include.ui.controls.filemanager import FileManagerView
from include.ui.controls.more import MoreView


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
            MoreView(self)
        ]
        self.navigation_bar = HomeNavigationBar(parent_view=self, views=self.controls[1:])
        self.file_picker: ft.FilePicker

        self.page.session.store.set("navigation_bar", self.navigation_bar)

    def post_init(self) -> None:
        self.file_picker = ft.FilePicker()
        self.page._services.append(self.file_picker)

    #     self.page.session.store.set("load_directory", load_directory)
    #     self.page.session.store.set("current_directory_id", current_directory_id)
    #     self.page.session.store.set("initialization_complete", True)

    #     if self.page.session.store.get("server_info")[
    #         "lockdown"
    #     ] and "bypass_lockdown" not in self.page.session.store.get("user_permissions"):
    #         go_lockdown(self.page)
