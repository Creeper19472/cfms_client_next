import flet as ft
from flet_model import Model, route
from include.ui.controls.views.connect import ConnectForm
from include.ui.controls.buttons.upgrade import FloatingUpgradeButton
from include.constants import APP_VERSION
from include.ui.constants import PLACEHOLDER_COLOR


@route("connect")
class ConnectToServerModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment = ft.CrossAxisAlignment.CENTER
    padding = 20
    spacing = 10

    appbar = ft.AppBar(title=ft.Text("Connect to Server"), center_title=True)

    floating_action_button = FloatingUpgradeButton()
    floating_action_button_location = ft.FloatingActionButtonLocation.END_FLOAT

    def __init__(self, page: ft.Page):
        super().__init__(page)

        explanation_text = ft.Text(
            APP_VERSION,
            color=PLACEHOLDER_COLOR,
            size=12,
            text_align=ft.TextAlign.CENTER,
        )

        version_container = ft.Container(
            content=explanation_text,
            alignment=ft.Alignment.BOTTOM_CENTER,
        )

        self.controls = [ConnectForm(), version_container]
