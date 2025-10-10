import flet as ft
from flet_model import Model, route

from include.classes.config import AppConfig
from include.ui.controls.views.manage.account import ManageAccountsView
from include.ui.controls.views.manage.audit import AuditLogView
from include.ui.controls.views.manage.group import ManageGroupsView


class ManagementNavigationBar(ft.NavigationBar):
    def __init__(self, parent_view: "ManageModel", views: list[ft.Control] = []):
        self.parent_view = parent_view

        self.last_selected_index = 0  # 默认值设置成初次进入时默认选中的页面在效果上较好
        self.views = views

        nav_destinations = [
            ft.NavigationBarDestination(
                icon=ft.Icons.SUPERVISOR_ACCOUNT_OUTLINED, label="Accounts"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED,
                label="Groups",
            ),
            # ft.NavigationBarDestination(
            #     icon=ft.Icons.SETTINGS_APPLICATIONS, label="Settings"
            # ),
            ft.NavigationBarDestination(icon=ft.Icons.ARTICLE, label="Logs"),
        ]

        super().__init__(
            nav_destinations,
            selected_index=0,
            on_change=self.on_change_item,
        )

    async def on_change_item(self, e: ft.Event[ft.NavigationBar]):
        def show_view(index):
            for view in self.views:
                if self.views.index(view) == index:
                    view.visible = True
                else:
                    view.visible = False

        yield show_view(e.control.selected_index)
        self.last_selected_index = self.selected_index


@route("manage")
class ManageModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.app_config = AppConfig()

        self.appbar = ft.AppBar(
            title=ft.Text("Management"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self._go_back),
        )
        
        self.controls = [
            ManageAccountsView(self),
            ManageGroupsView(self, visible=False),
            AuditLogView(self, visible=False)
        ]
        self.navigation_bar = ManagementNavigationBar(self, self.controls)

        # self.floating_action_button = ft.FloatingActionButton(
        #     icon=ft.Icons.LOCK, on_click=apply_lockdown
        # )
        # self.floating_action_button_location = ft.FloatingActionButtonLocation.END_FLOAT

        # self.page.session.set("refresh_user_list", refresh_user_list)

    async def _go_back(self, event: ft.Event[ft.IconButton]):
        self.page.views.pop()
        if last_route := self.page.views[-1].route:
            await self.page.push_route(last_route)

    def did_mount(self) -> None:
        pass
        # self.floating_action_button.visible = "apply_lockdown" in self.app_config.user_permissions
