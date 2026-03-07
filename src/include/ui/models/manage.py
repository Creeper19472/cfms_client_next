from typing import cast

import flet as ft
from flet_model import Model, Router, route
from flet_material_symbols import Symbols

from include.classes.shared import AppShared
from include.ui.controls.views.admin.account import ManageAccountsView
from include.ui.controls.views.admin.audit import AuditLogView
from include.ui.controls.views.admin.group import ManageGroupsView
from include.ui.util.route import get_parent_route
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

INITIAL_VIEW_INDEX = 0


class ManagementNavigationBar(ft.NavigationBar):
    def __init__(
        self,
        parent_view: "ManageModel",
        views: list[ft.Control] = [],
        initial_selected_index: int = 0,
    ):
        self.parent_view = parent_view

        # Setting default to initially selected page works better
        self.last_selected_index = initial_selected_index
        self.views = views
        self._is_click_navigating = False

        nav_destinations = [
            ft.NavigationBarDestination(
                icon=Symbols.SUPERVISOR_ACCOUNT, label=_("Accounts")
            ),
            ft.NavigationBarDestination(
                icon=Symbols.ADMIN_PANEL_SETTINGS,
                label=_("Groups"),
            ),
            # ft.NavigationBarDestination(
            #     icon=Symbols.SETTINGS_APPLICATIONS, label="Settings"
            # ),
            ft.NavigationBarDestination(icon=Symbols.ARTICLE, label=_("Logs")),
        ]

        super().__init__(
            nav_destinations,
            selected_index=initial_selected_index,
            on_change=self.on_change_item,
        )

    async def on_change_item(self, e: ft.Event[ft.NavigationBar]):
        self._is_click_navigating = True
        try:
            await self.parent_view.pageview.go_to_page(
                e.control.selected_index,
                animation_curve=ft.AnimationCurve.FAST_OUT_SLOWIN,
                animation_duration=ft.Duration(milliseconds=400),
            )
        finally:
            self._is_click_navigating = False

        self.last_selected_index = self.selected_index


@route("manage")
class ManageModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = ft.Padding(20, 0, 20, 20)
    spacing = 10

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)

        self.app_shared = AppShared()

        self.appbar = ft.AppBar(
            title=ft.Text(_("Management")),
            leading=ft.IconButton(icon=Symbols.ARROW_BACK, on_click=self._go_back),
        )

        self.stored_views = [
            ManageAccountsView(self),
            ManageGroupsView(self),
            AuditLogView(self),
        ]
        self.pageview = ft.PageView(
            self.stored_views,
            expand=True,
            selected_index=INITIAL_VIEW_INDEX,
            on_change=self.on_pageview_change,
        )

        self.controls = [self.pageview]
        self.navigation_bar = ManagementNavigationBar(
            self, self.stored_views, initial_selected_index=INITIAL_VIEW_INDEX
        )

        # self.floating_action_button = ft.FloatingActionButton(
        #     icon=Symbols.LOCK, on_click=apply_lockdown
        # )
        # self.floating_action_button_location = ft.FloatingActionButtonLocation.END_FLOAT

        # self.page.session.set("refresh_user_list", refresh_user_list)

    async def _go_back(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(get_parent_route(self.page.route))

    async def on_pageview_change(self, event: ft.Event[ft.PageView]):
        assert self.navigation_bar
        assert type(event.data) == int

        # Only sync the navigation bar indicator for swipe gestures.
        # When the user clicks a NavigationBarDestination, on_change_item sets
        # _is_click_navigating=True before calling go_to_page(), which causes
        # all intermediate on_change events to be skipped. This prevents the
        # navigation bar indicator from flickering through intermediate positions.
        if cast(ManagementNavigationBar, self.navigation_bar)._is_click_navigating:
            return

        self.navigation_bar.selected_index = event.data

    def did_mount(self) -> None:
        pass
        # self.floating_action_button.visible = "apply_lockdown" in self.app_shared.user_permissions
