from flet_model import Model, Router, route
import flet as ft

from include.classes.shared import AppShared
from include.ui.controls.views.admin.account import ManageAccountsView
from include.ui.controls.views.admin.audit import AuditLogView
from include.ui.controls.views.admin.group import ManageGroupsView
from include.ui.util.route import get_parent_route
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class ManagementNavigationBar(ft.NavigationBar):
    def __init__(self, parent_view: "ManageModel", views: list[ft.Control] = []):
        self.parent_view = parent_view

        self.last_selected_index = 0  # Setting default to initially selected page works better
        self.views = views

        nav_destinations = [
            ft.NavigationBarDestination(
                icon=ft.Icons.SUPERVISOR_ACCOUNT_OUTLINED, label=_("Accounts")
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED,
                label=_("Groups"),
            ),
            # ft.NavigationBarDestination(
            #     icon=ft.Icons.SETTINGS_APPLICATIONS, label="Settings"
            # ),
            ft.NavigationBarDestination(icon=ft.Icons.ARTICLE, label=_("Logs")),
        ]

        super().__init__(
            nav_destinations,
            selected_index=0,
            on_change=self.on_change_item,
        )

    async def on_change_item(self, e: ft.Event[ft.NavigationBar]):
        def show_view(index):
            for i, view in enumerate(self.views):
                view.visible = i == index

        show_view(e.control.selected_index)
        self.last_selected_index = self.selected_index


@route("manage")
class ManageModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)

        self.app_shared = AppShared()

        self.appbar = ft.AppBar(
            title=ft.Text(_("Management")),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self._go_back),
        )

        self.controls = [
            ManageAccountsView(self),
            ManageGroupsView(self, visible=False),
            AuditLogView(self, visible=False),
        ]
        self.navigation_bar = ManagementNavigationBar(self, self.controls)

        # self.floating_action_button = ft.FloatingActionButton(
        #     icon=ft.Icons.LOCK, on_click=apply_lockdown
        # )
        # self.floating_action_button_location = ft.FloatingActionButtonLocation.END_FLOAT

        # self.page.session.set("refresh_user_list", refresh_user_list)

    async def _go_back(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(get_parent_route(self.page.route))

    def did_mount(self) -> None:
        pass
        # self.floating_action_button.visible = "apply_lockdown" in self.app_shared.user_permissions
