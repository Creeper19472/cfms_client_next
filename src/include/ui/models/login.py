from flet_model import Model, Router, route
import flet as ft

from include.ui.controls.views.login import LoginView


@route("login")
class LoginModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)
        self.controls = [LoginView()]
