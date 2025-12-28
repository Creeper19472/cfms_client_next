"""Authorization dialog for granting temporary access to files and directories."""

from datetime import datetime
from typing import TYPE_CHECKING, Literal, cast

import flet as ft

from include.classes.config import AppShared
from include.controllers.dialogs.authorize import AuthorizeDialogController
from include.ui.controls.dialogs.base import AlertDialog
from include.ui.util.notifications import send_error
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileListView

t = get_translation()
_ = t.gettext


class AuthorizeDialog(AlertDialog):
    """Dialog for authorizing access to files or directories."""

    def __init__(
        self,
        object_type: Literal["document", "directory"],
        object_id: str,
        parent_listview: "FileListView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = AuthorizeDialogController(self)
        self.object_type = object_type
        self.object_id = object_id
        self.parent_listview = parent_listview
        self.app_shared = AppShared()

        match self.object_type:
            case "document":
                self.object_display_name = _("File")
            case "directory":
                self.object_display_name = _("Directory")
            case _:
                raise ValueError(f"Invalid object type: {object_type}")

        self.modal = False
        self.title = ft.Text(
            _("Authorize Access to {display_name}").format(
                display_name=self.object_display_name
            )
        )

        # Progress indicator
        self.progress_ring = ft.ProgressRing(visible=False)

        # Check if user has permissions to list users/groups
        self.has_list_users = "list_users" in self.app_shared.user_permissions
        self.has_list_groups = "list_groups" in self.app_shared.user_permissions

        # User/Group search field
        # If user doesn't have list permissions, this becomes a direct input field
        self.entity_search = ft.TextField(
            label=_("Username or Group Name"),
            hint_text=_("Enter username or group name"),
            on_submit=None,  # Will be set based on entity type in _update_ui_for_permissions
            expand=True,
        )

        # Search button (only visible if user has list permissions)
        self.search_button = ft.IconButton(
            icon=ft.Icons.SEARCH,
            tooltip=_("Search"),
            on_click=self.search_entity,
            visible=False,  # Will be set based on entity type
        )

        # Search results dropdown (only visible if user has list permissions)
        self.entity_dropdown = ft.Dropdown(
            label=_("Select Entity"),
            hint_text=_("Search to see available options"),
            expand=True,
            disabled=True,
            width=500,
            visible=False,  # Will be set based on entity type
        )

        # Subject type selector
        self.entity_type = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="user", label=_("User")),
                    ft.Radio(value="group", label=_("Group")),
                ],
            ),
            value="user",
            on_change=self.on_target_type_change,
        )

        # Set initial visibility based on permissions
        self._update_ui_for_permissions()

        # Access type selector
        self.access_types_row = ft.SegmentedButton(
            selected_icon=ft.Icon(ft.Icons.CHECK_SHARP),
            selected=["read"],
            allow_empty_selection=False,
            allow_multiple_selection=True,
            segments=[
                ft.Segment(
                    value="read",
                    label=ft.Text(_("Read")),
                    icon=ft.Icon(ft.Icons.SCREEN_SEARCH_DESKTOP_OUTLINED),
                ),
                ft.Segment(
                    value="write",
                    label=ft.Text(_("Write")),
                    icon=ft.Icon(ft.Icons.EDIT_OUTLINED),
                ),
                ft.Segment(
                    value="move",
                    label=ft.Text(_("Move")),
                    icon=ft.Icon(ft.Icons.DRIVE_FILE_MOVE_OUTLINED),
                ),
                ft.Segment(
                    value="manage",
                    label=ft.Text(_("Manage")),
                    icon=ft.Icon(ft.Icons.MANAGE_HISTORY_ROUNDED),
                ),
            ],
        )

        now = datetime.now()

        # Date and time pickers for start time
        self.date_range_button = ft.Button(
            _("Date Range"),
            icon=ft.Icons.CALENDAR_TODAY,
            on_click=lambda _: self.page.show_dialog(self.date_range_picker),
        )
        self.start_date_text = ft.Text(now.strftime("%Y-%m-%d"), size=14)
        self.date_range_picker = ft.DateRangePicker(
            first_date=now,  # temp fix: see flet-dev:flet issue #5895
            start_value=now,
            end_value=now,
            on_change=self.on_date_range_change,
        )

        self.start_time_button = ft.Button(
            _("Start Time"),
            icon=ft.Icons.ACCESS_TIME,
            on_click=lambda _: self.page.show_dialog(self.start_time_picker),
        )
        self.start_time_text = ft.Text(now.strftime("%H:%M:%S"), size=14)
        self.start_time_picker = ft.TimePicker(
            now.time(),  # fix assertion errors
            on_change=self.on_start_time_change,
        )

        # Date and time pickers for end time
        self.end_date_text = ft.Text(now.strftime("%Y-%m-%d"), size=14)
        self.end_date_text.visible = not (
            self.end_date_text.value == self.start_date_text.value
        )

        self.end_time_button = ft.Button(
            _("End Time"),
            icon=ft.Icons.ACCESS_TIME,
            on_click=lambda _: self.page.show_dialog(self.end_time_picker),
        )
        self.end_time_text = ft.Text(
            now.strftime("%H:%M:%S"),
            size=14,
        )
        self.end_time_picker = ft.TimePicker(
            now.time(),
            on_change=self.on_end_time_change,
        )

        # Submit and cancel buttons
        self.submit_button = ft.TextButton(
            _("Authorize"),
            on_click=self.ok_button_click,
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

        # Build content layout
        self.content = ft.Column(
            controls=[
                # Target selection section
                ft.Text(_("Select Target"), weight=ft.FontWeight.BOLD),
                self.entity_type,
                ft.Row(
                    [self.entity_search, self.search_button],
                    spacing=5,
                ),
                self.entity_dropdown,
                self.access_types_row,
                ft.Divider(),
                # Time range section
                ft.Text(_("Authorization Period"), weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(_("Date Range:"), size=12),
                                self.date_range_button,
                                self.start_date_text,
                                self.end_date_text,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                        ft.Column(
                            [
                                ft.Text(_("Start Time:"), size=12),
                                self.start_time_button,
                                self.start_time_text,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                        ft.Column(
                            [
                                ft.Text(_("End Time:"), size=12),
                                self.end_time_button,
                                self.end_time_text,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                    ],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.CENTER,
                    run_alignment=ft.MainAxisAlignment.CENTER,
                    wrap=True,
                ),
            ],
            width=500,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

        self.actions = [self.progress_ring, self.submit_button, self.cancel_button]

    def _has_permission_for_current_type(self) -> bool:
        """Check if user has permission for the currently selected entity type."""
        current_type = self.entity_type.value
        return (
            (current_type == "user" and self.has_list_users) or
            (current_type == "group" and self.has_list_groups)
        )

    def _update_ui_for_permissions(self):
        """Update UI visibility based on user permissions and selected entity type."""
        has_permission = self._has_permission_for_current_type()
        
        # Update search button and dropdown visibility
        self.search_button.visible = has_permission
        self.entity_dropdown.visible = has_permission
        
        # Update search field submit handler
        self.entity_search.on_submit = self.search_entity if has_permission else None
        
        # Update hint text based on permission
        if has_permission:
            self.entity_search.hint_text = _("Enter username or group name to search")
        else:
            self.entity_search.hint_text = _("Enter username or group name")

    def did_mount(self):
        """Called when dialog is mounted to the page."""
        super().did_mount()
        # Add date/time pickers to page overlays
        self.page.overlay.extend(
            [
                self.date_range_picker,
                self.start_time_picker,
                self.end_time_picker,
            ]
        )
        self.page.update()

    def will_unmount(self):
        """Called when dialog is about to be unmounted."""
        # Remove date/time pickers from page overlays
        for picker in [
            self.date_range_picker,
            self.start_time_picker,
            self.end_time_picker,
        ]:
            if picker in self.page.overlay:
                self.page.overlay.remove(picker)

    def disable_interactions(self):
        """Disable all interactive elements during processing."""
        self.entity_search.disabled = True
        self.search_button.disabled = True
        self.entity_dropdown.disabled = True
        self.entity_type.disabled = True
        self.date_range_button.disabled = True
        self.start_time_button.disabled = True
        self.end_time_button.disabled = True
        self.cancel_button.disabled = True
        self.submit_button.visible = False
        self.progress_ring.visible = True
        self.entity_search.error = None
        self.modal = True
        self.update()

    def enable_interactions(self):
        """Re-enable all interactive elements after processing."""
        self.entity_search.disabled = False
        self.search_button.disabled = False
        if self.entity_dropdown.options:
            self.entity_dropdown.disabled = False
        self.entity_type.disabled = False
        self.date_range_button.disabled = False
        self.start_time_button.disabled = False
        self.end_time_button.disabled = False
        self.cancel_button.disabled = False
        self.submit_button.visible = True
        self.progress_ring.visible = False
        self.modal = False
        self.update()

    async def search_entity(self, event):
        """Search for users or groups based on the search term."""
        # Check if user has permission for current entity type
        if not self._has_permission_for_current_type():
            # User doesn't have permission to search, ignore this request
            return
        
        if not self.entity_search.value:
            self.entity_search.error = _("Please enter a search term")
            self.update()
            return

        yield self.disable_interactions()

        # Run the search in a background task
        self.page.run_task(
            self.controller.action_search_targets,
            self.entity_search.value,
            cast(Literal["user", "group"], self.entity_type.value),
        )

    async def on_target_type_change(self, event: ft.Event[ft.RadioGroup]):
        """Handle target type change."""
        # Clear previous search results
        self.entity_dropdown.options = []
        self.entity_dropdown.value = None
        self.entity_dropdown.disabled = True
        
        # Update UI based on permissions for the new type
        self._update_ui_for_permissions()
        
        self.update()

    async def on_date_range_change(self, event: ft.Event[ft.DateRangePicker]):
        """Handle date selection."""

        self.start_date_text.value = cast(
            ft.DateTimeValue, self.date_range_picker.start_value
        ).strftime("%Y-%m-%d")
        self.end_date_text.value = cast(
            ft.DateTimeValue, self.date_range_picker.end_value
        ).strftime("%Y-%m-%d")
        self.end_date_text.visible = not (
            self.end_date_text.value == self.start_date_text.value
        )

    async def on_start_time_change(self, event: ft.Event[ft.TimePicker]):
        """Handle start time selection."""
        if event.control.value:
            self.start_time_text.value = event.control.value.strftime("%H:%M:%S")

    async def on_end_time_change(self, event: ft.Event[ft.TimePicker]):
        """Handle end time selection."""
        if event.control.value:
            self.end_time_text.value = event.control.value.strftime("%H:%M:%S")

    async def ok_button_click(self, event: ft.Event[ft.TextButton]):
        """Handle submit button click."""
        # Determine which source to use for entity name
        current_type = cast(Literal["user", "group"], self.entity_type.value)
        has_permission = self._has_permission_for_current_type()
        
        # Validate target selection
        if has_permission:
            # When user has permission, they must select from dropdown
            if not self.entity_dropdown.value:
                self.entity_search.error = _("Please select a target")
                self.update()
                return
            entity_name = self.entity_dropdown.value
        else:
            # When user doesn't have permission, they must enter directly in text field
            if not self.entity_search.value or not self.entity_search.value.strip():
                self.entity_search.error = _("Please enter a username or group name")
                self.update()
                return
            entity_name = self.entity_search.value.strip()

        yield self.disable_interactions()

        assert self.date_range_picker.start_value is not None
        assert self.start_time_picker.value is not None
        assert self.date_range_picker.end_value is not None
        assert self.end_time_picker.value is not None

        start_timestamp = datetime.combine(
            cast(datetime, self.date_range_picker.start_value),
            self.start_time_picker.value,
        ).timestamp()
        end_timestamp = datetime.combine(
            cast(datetime, self.date_range_picker.end_value),
            self.end_time_picker.value,
        ).timestamp()

        # Validate that end time is after start time
        if end_timestamp <= start_timestamp:
            send_error(self.page, _("End time must be after start time"))
            yield self.enable_interactions()
            return

        # Run authorization in background task
        self.page.run_task(
            self.controller.action_authorize,
            entity_name,
            current_type,
            start_timestamp,
            end_timestamp,
        )

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        """Handle cancel button click."""
        self.close()
