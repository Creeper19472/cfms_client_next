from typing import TYPE_CHECKING, Union, cast

import flet as ft

from include.classes.shared import AppShared
from include.classes.services.favorites_validation import FavoritesValidationService
from include.ui.controls.components.explorer.tile import DirectoryTile, FileTile
from include.ui.util.notifications import send_error
from include.ui.util.path import get_document


if TYPE_CHECKING:
    from include.ui.models.home import HomeModel

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class HomeNavigationBar(ft.NavigationBar):
    def __init__(
        self,
        parent_view: "HomeModel",
        views: list[ft.Control] = [],
        initial_selected_index: int = 2,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        self.parent_view = parent_view
        self.app_shared = AppShared()

        self.last_selected_index = initial_selected_index  # Setting default to initially selected page works better
        self.views = views
        self._is_click_navigating = False

        nav_destinations = [
            ft.NavigationBarDestination(icon=ft.Icons.FOLDER, label=_("Files")),
            ft.NavigationBarDestination(
                icon=ft.Icons.ARROW_CIRCLE_DOWN, label=_("Tasks")
            ),
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label=_("Home")),
            ft.NavigationBarDestination(icon=ft.Icons.MORE_HORIZ, label=_("More")),
            ft.NavigationBarDestination(
                icon=ft.Icons.CLOUD_CIRCLE, label=_("Manage"), visible=False
            ),
        ]

        super().__init__(
            nav_destinations,
            selected_index=initial_selected_index,
            on_change=self.on_change_item,
            ref=ref,
            visible=visible,
        )

    async def on_change_item(self, e: ft.Event[ft.NavigationBar]):
        if e.control.selected_index == 4:
            assert type(self.page) == ft.Page
            await self.page.push_route("/home/manage")
            self.selected_index = self.last_selected_index
            self.update()
            return

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

    def build(self):
        if {
            "manage_system",
            "view_audit_logs",
            "list_users",
            "list_groups",
            "apply_lockdown",
            "bypass_lockdown",
        } & set(self.app_shared.user_permissions):
            self.destinations[4].visible = True


class WelcomeInfoCard(ft.Card):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.content = ft.Container(
            content=ft.Column(
                [
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ACCESS_TIME_FILLED),
                        title=ft.Text(
                            _(
                                "Welcome to Confidential Document Management System (CFMS)"
                            )
                        ),
                        subtitle=ft.Text(
                            _(
                                "The sunset glow and the lone wild duck fly together, autumn water shares the same color with the vast sky."
                            )
                        ),
                    ),
                ],
            ),
            padding=10,
        )


class HomeFavoritesContainer(ft.Container):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible, margin=15)
        self.page: ft.Page
        self.app_shared = AppShared()
        self.expand = True
        self.expand_loose = True

        self.listview = ft.ListView(controls=[], scroll=ft.ScrollMode.AUTO, expand=True)
        self.content = self.listview

    def _mark_item_invalid(
        self,
        control: Union[FileTile, DirectoryTile],
        item_id: str,
        item_name: str,
    ):
        """Helper method to mark a control as invalid with consistent styling."""
        cast(ft.Icon, control.leading).color = ft.Colors.GREY_500
        control.title = ft.Text(
            item_name,
            color=ft.Colors.GREY_500,
            style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH),
        )
        control.subtitle = ft.Text(
            _("ID: {id} (No longer exists)").format(id=item_id),
            color=ft.Colors.RED_300,
        )
        control.on_click = None

    async def update_favorites(self, from_validation_callback: bool = False):
        # add favorite files and directories
        assert self.app_shared.user_perference
        favorite_files = self.app_shared.user_perference.favourites.get("files", {})
        favorite_directories = self.app_shared.user_perference.favourites.get(
            "directories", {}
        )

        # Get validation service
        validation_service = None
        if self.app_shared.service_manager:
            validation_service = cast(
                FavoritesValidationService,
                self.app_shared.service_manager.get_service("favorites_validation"),
            )

        # If this is called from validation callback, only update the styling of existing controls
        # Don't clear and recreate everything
        if from_validation_callback and validation_service:
            # Update existing controls to mark invalid items
            for control in self.listview.controls:
                if isinstance(control, FileTile):
                    is_valid = validation_service.is_file_valid(control.file_id)
                    if not is_valid:
                        self._mark_item_invalid(
                            control, control.file_id, control.filename
                        )
                elif isinstance(control, DirectoryTile):
                    is_valid = validation_service.is_directory_valid(
                        control.directory_id
                    )
                    if not is_valid:
                        self._mark_item_invalid(
                            control, control.directory_id, control.dir_name
                        )

            # Update the UI
            self.update()
            return

        # Normal rendering: clear existing controls and recreate
        self.listview.controls.clear()

        # Register callback to update UI after validation completes
        # But only register once
        if validation_service and not hasattr(self, "_validation_callback_registered"):

            async def on_validation_complete():
                # Just update styling of existing controls, don't re-render
                self.page.run_task(self.update_favorites, from_validation_callback=True)

            validation_service.register_on_validation_complete(on_validation_complete)
            self._validation_callback_registered = True

        # Trigger validation in background (non-blocking) on first view
        # Only trigger if validation hasn't started yet and not in progress
        if (
            validation_service
            and not validation_service.first_validation_done
            and not validation_service.validation_in_progress
        ):
            validation_service.trigger_validation_async()

        async def on_filetile_click(event: ft.Event[ft.ListTile]):
            assert type(event.control) == FileTile

            # Check if file is marked as invalid
            if validation_service and not validation_service.is_file_valid(
                event.control.file_id
            ):
                send_error(
                    self.page, _("This document no longer exists on the server.")
                )
                return

            try:
                await get_document(
                    event.control.file_id,
                    filename=event.control.filename,
                    page=self.page,
                )

            except FileNotFoundError:
                if validation_service:
                    validation_service.mark_file_invalid(event.control.file_id)
                self.page.run_task(self.update_favorites, from_validation_callback=True)

            except Exception as e:
                # Safely access potential 'response' attribute without relying on Exception having it
                err_obj = cast(object, e)
                resp = getattr(err_obj, "response", None)
                if isinstance(resp, dict):
                    send_error(
                        self.page,
                        _("Failed to download document: ({code}) {message}").format(
                            code=resp.get("code", "Unknown"),
                            message=resp.get("message", str(e)),
                        ),
                    )
                else:
                    send_error(
                        self.page,
                        _("Failed to download document: {error}").format(error=str(e)),
                    )

                self.page.run_task(self.update_favorites, from_validation_callback=True)

        async def on_dirtile_click(event: ft.Event[ft.ListTile]):
            pass

        for dir_id in favorite_directories:
            # Check if directory is valid
            is_valid = True
            if validation_service:
                is_valid = validation_service.is_directory_valid(dir_id)

            directory = DirectoryTile(
                dir_name=favorite_directories[dir_id],
                directory_id=dir_id,
                starred=True,
                show_id=True,
                on_click=on_dirtile_click if is_valid else None,
            )

            # Apply visual styling for invalid items
            if not is_valid:
                self._mark_item_invalid(directory, dir_id, favorite_directories[dir_id])

            self.listview.controls.append(directory)

        for file_id in favorite_files:
            # Check if file is valid
            is_valid = True
            if validation_service:
                is_valid = validation_service.is_file_valid(file_id)

            file = FileTile(
                filename=favorite_files[file_id],
                file_id=file_id,
                starred=True,
                show_id=True,
                on_click=on_filetile_click if is_valid else None,
            )

            # Apply visual styling for invalid items
            if not is_valid:
                self._mark_item_invalid(file, file_id, favorite_files[file_id])

            self.listview.controls.append(file)

        if not self.listview.controls:
            self.listview.controls.append(
                ft.Text(_("You have not favorited any documents or folders yet."))
            )

        # Update the UI
        # Why here needs a `self.update()` is because this method is async and called via `run_task`,
        # not directly called by event hooks, so it won't auto-update UI after completion.
        self.update()


class HomeTabs(ft.Tabs):
    def __init__(
        self,
        ref: ft.Ref | None = None,
    ):
        self.tabbar_ref = ft.Ref[ft.TabBar]()
        self.tabbarview_ref = ft.Ref[ft.TabBarView]()
        self.home_favorites_container = HomeFavoritesContainer()

        _tabbar = ft.TabBar(
            tabs=[
                ft.Tab(label=_("Favorites")),
            ],
            ref=self.tabbar_ref,  # pyright: ignore[reportArgumentType]
        )
        _tabbarview = ft.TabBarView(
            expand=True,
            controls=[
                self.home_favorites_container,
            ],
            ref=self.tabbarview_ref,  # pyright: ignore[reportArgumentType]
        )

        super().__init__(
            selected_index=0,
            length=1,
            expand=True,
            content=ft.Column(controls=[_tabbar, _tabbarview], expand=True),
            ref=ref,
        )

    def did_mount(self):
        super().did_mount()
        # Schedule the async update_favorites as a task
        assert type(self.page) is ft.Page
        self.page.run_task(self.home_favorites_container.update_favorites)


class HomeView(ft.Container):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible, expand=True, expand_loose=True)

        self.margin = 10
        self.padding = 10

        self.welcome_info_card = WelcomeInfoCard()
        self.home_tabs = HomeTabs()

        self.content = ft.Column(
            controls=[
                self.welcome_info_card,
                self.home_tabs,
            ]
        )

        # Form variable definitions

        # Form reference definitions

        # Form element definitions

    def did_mount(self):
        super().did_mount()
        # Schedule the async update_favorites as a task
        assert type(self.page) is ft.Page
        self.page.run_task(self.home_tabs.home_favorites_container.update_favorites)
