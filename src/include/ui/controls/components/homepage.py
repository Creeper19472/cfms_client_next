from typing import TYPE_CHECKING

import flet as ft

from include.classes.config import AppShared
from include.classes.services.favorites_validation import FavoritesValidationService
from include.ui.controls.components.explorer.tile import DirectoryTile, FileTile
from include.ui.controls.views.explorer import FileManagerView
from include.ui.util.file_controls import get_directory
from include.ui.util.notifications import send_error, send_info
from include.ui.util.path import get_document


if TYPE_CHECKING:
    from include.ui.models.home import HomeModel

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class HomeNavigationBar(ft.NavigationBar):
    def __init__(self, parent_view: "HomeModel", views: list[ft.Control] = []):
        self.parent_view = parent_view
        self.app_shared = AppShared()

        self.last_selected_index = (
            2  # Setting default to initially selected page works better
        )
        self.views = views

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
            selected_index=2,
            on_change=self.on_change_item,
            # visible=False
        )

    async def on_change_item(self, e: ft.Event[ft.NavigationBar]):
        def show_view(index):
            for view in self.views:
                if self.views.index(view) == index:
                    view.visible = True
                    view.did_mount()
                else:
                    view.visible = False

        yield show_view(e.control.selected_index)

        if e.control.selected_index == 0:
            assert type(self.views[0]) == FileManagerView
            await get_directory(
                self.views[0].current_directory_id, self.views[0].file_listview
            )
        elif e.control.selected_index == 4:
            assert type(self.page) == ft.Page
            await self.page.push_route("/home/manage")
            self.selected_index = self.last_selected_index
            yield show_view(self.selected_index)
            self.update()
            return

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
        super().__init__(ref=ref, visible=visible, expand=True, expand_loose=True)
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
                ]
            ),
            # width=400,
            padding=10,
        )


class HomeFavoritesContainer(ft.Container):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible, margin=15)
        self.page: ft.Page
        self.app_shared = AppShared()

        self.listview = ft.ListView(controls=[])
        self.content = self.listview

    async def update_favorites(self):
        # add favorite files and directories
        assert self.app_shared.user_perference
        favorite_files = self.app_shared.user_perference.favourites.get("files", {})
        favorite_directories = self.app_shared.user_perference.favourites.get(
            "directories", {}
        )

        # clear existing controls
        self.listview.controls.clear()
        
        # Get validation service
        validation_service = None
        if self.app_shared.service_manager:
            validation_service = self.app_shared.service_manager.get_service("favorites_validation")
            
            # Register callback to update UI after validation completes
            # But only register once
            if validation_service and not hasattr(self, '_validation_callback_registered'):
                async def on_validation_complete():
                    # Re-render the favorites list with validation results
                    await self.update_favorites()
                    # Update the page to reflect changes
                    if hasattr(self, 'page') and self.page:
                        self.update()
                
                validation_service.register_on_validation_complete(on_validation_complete)
                self._validation_callback_registered = True
            
            # Trigger validation in background (non-blocking) on first view
            if validation_service and not validation_service._first_validation_done:
                validation_service.trigger_validation_async()

        async def on_filetile_click(event: ft.Event[ft.ListTile]):
            assert type(event.control) == FileTile
            
            # Check if file is marked as invalid
            if validation_service and not validation_service.is_file_valid(event.control.file_id):
                send_error(
                    self.page,
                    _("This document no longer exists on the server.")
                )
                return
            
            try:
                await get_document(
                    event.control.file_id,
                    filename=event.control.filename,
                    page=self.page,
                )
            except Exception as e:
                # If download fails, mark as invalid and notify user
                if validation_service:
                    validation_service.mark_file_invalid(event.control.file_id)
                
                # Check if it's a known error type with response dict
                if hasattr(e, 'response') and isinstance(e.response, dict):
                    send_error(
                        self.page,
                        _("Failed to download document: ({code}) {message}").format(
                            code=e.response.get("code", "Unknown"),
                            message=e.response.get("message", str(e))
                        )
                    )
                else:
                    send_error(
                        self.page,
                        _("Failed to download document: {error}").format(error=str(e))
                    )
                
                # Update the display to show item as invalid
                await self.update_favorites()
                self.update()

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
                directory.disabled = True
                directory.title = ft.Text(
                    favorite_directories[dir_id],
                    color=ft.Colors.GREY_500,
                    style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH),
                )
                directory.subtitle = ft.Text(
                    _("ID: {dir_id} (No longer exists)").format(dir_id=dir_id),
                    color=ft.Colors.RED_300,
                )
            
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
                file.disabled = True
                file.title = ft.Text(
                    favorite_files[file_id],
                    color=ft.Colors.GREY_500,
                    style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH),
                )
                file.subtitle = ft.Text(
                    _("ID: {file_id} (No longer exists)").format(file_id=file_id),
                    color=ft.Colors.RED_300,
                )
            
            self.listview.controls.append(file)

        if not self.listview.controls:
            self.listview.controls.append(
                ft.Text(_("You have not favorited any documents or folders yet."))
            )


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
        self.page.run_task(self.home_favorites_container.update_favorites)


class HomeView(ft.Container):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)

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
        self.page.run_task(self.home_tabs.home_favorites_container.update_favorites)
