import flet as ft
from flet_model import Model, route
from include.ui.controls.login import LoginView


@route("login")
class LoginModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment = ft.CrossAxisAlignment.CENTER
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.controls = [LoginView()]