from typing import cast

from flet_model import Model, Router, route
import flet as ft

from include.ui.controls.buttons.lockdown import LockdownSwitchButton
from include.ui.controls.components.homepage import HomeView, HomeNavigationBar
from include.ui.controls.dialogs.whatsnew import WhatsNewDialog, changelogs
from include.ui.controls.views.explorer import FileManagerView
from include.ui.controls.views.more import MoreView
from include.ui.controls.views.tasks import TasksView
from include.classes.shared import AppShared
from include.util.requests import do_request_2

INITIAL_VIEW_INDEX = 2


@route("home")
class HomeModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)

        self.floating_action_button = LockdownSwitchButton(visible=False)
        self.floating_action_button_location = ft.FloatingActionButtonLocation.END_FLOAT

        self.stored_views = [
            FileManagerView(parent_model=self),
            TasksView(parent_model=self),
            HomeView(),
            MoreView(self),
        ]
        self.pageview = ft.PageView(
            self.stored_views,
            expand=True,
            selected_index=INITIAL_VIEW_INDEX,
            on_change=self.on_pageview_change,
        )

        self.controls = [
            self.pageview,
        ]
        if AppShared().is_mobile:
            self.controls.insert(0, ft.SafeArea(ft.Container()))

        self.navigation_bar = HomeNavigationBar(
            parent_view=self,
            views=self.stored_views,
            initial_selected_index=INITIAL_VIEW_INDEX,
        )
        self.file_picker: ft.FilePicker

    def post_init(self) -> None:
        self.file_picker = ft.FilePicker()
        self.page.services.append(self.file_picker)

        async def _popups_check():
            # check welcome
            # if not await self.page.shared_preferences.get("welcome_shown"):
            #     self.page.show_dialog(self.homeview.welcome_dialog)
            #     await self.page.shared_preferences.set("welcome_shown", True)

            # check whatsnew
            if await ft.SharedPreferences().get("whatsnew") != changelogs[0].version:
                self.page.show_dialog(WhatsNewDialog())

        async def lockdown_check():
            assert self.floating_action_button is not None

            response = await do_request_2("server_info")
            lockdown = response.data["lockdown"]

            if "apply_lockdown" in AppShared().user_permissions:
                self.floating_action_button.visible = True
                cast(
                    LockdownSwitchButton, self.floating_action_button
                ).lockdown_active = lockdown
                self.floating_action_button.update()

            if lockdown and "bypass_lockdown" not in AppShared().user_permissions:
                AppShared().app_lockdown = True
                await self.page.push_route(self.page.route + "/lockdown")

        self.page.run_task(_popups_check)
        self.page.run_task(lockdown_check)

    async def on_pageview_change(self, event: ft.Event[ft.PageView]):
        assert self.navigation_bar
        assert type(event.data) == int

        # Only sync the navigation bar indicator for swipe gestures.
        # When the user clicks a NavigationBarDestination, on_change_item sets
        # _is_click_navigating=True before calling go_to_page(), which causes
        # all intermediate on_change events to be skipped. This prevents the
        # navigation bar indicator from flickering through intermediate positions.
        if cast(HomeNavigationBar, self.navigation_bar)._is_click_navigating:
            return

        nav_bar = cast(HomeNavigationBar, self.navigation_bar)
        nav_bar.selected_index = event.data
        nav_bar.last_selected_index = event.data
