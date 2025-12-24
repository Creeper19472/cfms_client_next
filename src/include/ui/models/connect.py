from flet_model import Model, Router, route
import flet as ft

from include.classes.config import AppShared
from include.constants import APP_VERSION
from include.ui.constants import PLACEHOLDER_COLOR
from include.ui.controls.buttons.upgrade import FloatingUpgradeButton
from include.ui.controls.views.connect import ConnectForm


@route("connect")
class ConnectToServerModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment = ft.CrossAxisAlignment.CENTER
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)

        self.appbar = ft.AppBar(
            title=ft.Text("Connect to Server"),
            center_title=True,
            actions=[
                ft.IconButton(
                    ft.Icons.SETTINGS_OUTLINED,
                    tooltip="Connection Settings",
                    on_click=self.conn_settings_button_click,
                ),
            ],
            actions_padding=10
        )

        self.floating_action_button = FloatingUpgradeButton()
        self.floating_action_button_location = ft.FloatingActionButtonLocation.END_FLOAT
        
        # Register the button with AppShared so AutoUpdateService can access it
        app_shared = AppShared()
        app_shared.floating_upgrade_button = self.floating_action_button

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

    def will_unmount(self) -> None:
        """Clear the button reference when leaving the connect page."""
        super().will_unmount()
        app_shared = AppShared()
        # Clear reference to prevent accessing unmounted button
        if app_shared.floating_upgrade_button is self.floating_action_button:
            app_shared.floating_upgrade_button = None

    async def conn_settings_button_click(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(self.page.route + "/conn_settings")
