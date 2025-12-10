"""Authorization dialog for granting temporary access to files and directories."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal

import flet as ft

from include.controllers.dialogs.authorize import AuthorizeDialogController
from include.ui.controls.dialogs.base import AlertDialog
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

        # User/Group search field
        self.target_search = ft.TextField(
            label=_("Username or Group Name"),
            hint_text=_("Enter username or group name"),
            on_submit=self.search_target,
            expand=True,
        )

        # Search button
        self.search_button = ft.IconButton(
            icon=ft.Icons.SEARCH,
            tooltip=_("Search"),
            on_click=self.search_target,
        )

        # Search results dropdown
        self.target_dropdown = ft.Dropdown(
            label=_("Select Target"),
            hint_text=_("Search to see available options"),
            expand=True,
            disabled=True,
        )

        # Target type selector
        self.target_type = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="user", label=_("User")),
                    ft.Radio(value="group", label=_("Group")),
                ],
            ),
            value="user",
            on_change=self.on_target_type_change,
        )

        # Date and time pickers for start time
        self.start_date_button = ft.ElevatedButton(
            text=_("Start Date"),
            icon=ft.Icons.CALENDAR_TODAY,
            on_click=lambda _: self.page.open(self.start_date_picker),
        )
        self.start_date_text = ft.Text(
            datetime.now().strftime("%Y-%m-%d"), size=14
        )
        self.start_date_picker = ft.DatePicker(
            on_change=self.on_start_date_change,
        )

        self.start_time_button = ft.ElevatedButton(
            text=_("Start Time"),
            icon=ft.Icons.ACCESS_TIME,
            on_click=lambda _: self.page.open(self.start_time_picker),
        )
        self.start_time_text = ft.Text(
            datetime.now().strftime("%H:%M"), size=14
        )
        self.start_time_picker = ft.TimePicker(
            on_change=self.on_start_time_change,
        )

        # Date and time pickers for end time
        self.end_date_button = ft.ElevatedButton(
            text=_("End Date"),
            icon=ft.Icons.CALENDAR_TODAY,
            on_click=lambda _: self.page.open(self.end_date_picker),
        )
        end_date = datetime.now() + timedelta(days=7)
        self.end_date_text = ft.Text(
            end_date.strftime("%Y-%m-%d"), size=14
        )
        self.end_date_picker = ft.DatePicker(
            on_change=self.on_end_date_change,
        )

        self.end_time_button = ft.ElevatedButton(
            text=_("End Time"),
            icon=ft.Icons.ACCESS_TIME,
            on_click=lambda _: self.page.open(self.end_time_picker),
        )
        self.end_time_text = ft.Text(
            end_date.strftime("%H:%M"), size=14
        )
        self.end_time_picker = ft.TimePicker(
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
                self.target_type,
                ft.Row(
                    [self.target_search, self.search_button],
                    spacing=5,
                ),
                self.target_dropdown,
                ft.Divider(),
                # Time range section
                ft.Text(_("Authorization Period"), weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(_("Start:"), size=12),
                                self.start_date_button,
                                self.start_date_text,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                        ft.Column(
                            [
                                ft.Text(_("Time:"), size=12),
                                self.start_time_button,
                                self.start_time_text,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                    ],
                    spacing=20,
                ),
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(_("End:"), size=12),
                                self.end_date_button,
                                self.end_date_text,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                        ft.Column(
                            [
                                ft.Text(_("Time:"), size=12),
                                self.end_time_button,
                                self.end_time_text,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                    ],
                    spacing=20,
                ),
            ],
            width=500,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

        self.actions = [self.progress_ring, self.submit_button, self.cancel_button]

    def did_mount(self):
        """Called when dialog is mounted to the page."""
        super().did_mount()
        # Add date/time pickers to page overlays
        self.page.overlay.extend([
            self.start_date_picker,
            self.start_time_picker,
            self.end_date_picker,
            self.end_time_picker,
        ])
        self.page.update()

    def will_unmount(self):
        """Called when dialog is about to be unmounted."""
        # Remove date/time pickers from page overlays
        for picker in [
            self.start_date_picker,
            self.start_time_picker,
            self.end_date_picker,
            self.end_time_picker,
        ]:
            if picker in self.page.overlay:
                self.page.overlay.remove(picker)

    def disable_interactions(self):
        """Disable all interactive elements during processing."""
        self.target_search.disabled = True
        self.search_button.disabled = True
        self.target_dropdown.disabled = True
        self.target_type.disabled = True
        self.start_date_button.disabled = True
        self.start_time_button.disabled = True
        self.end_date_button.disabled = True
        self.end_time_button.disabled = True
        self.cancel_button.disabled = True
        self.submit_button.visible = False
        self.progress_ring.visible = True
        self.target_search.error = None
        self.modal = True
        self.update()

    def enable_interactions(self):
        """Re-enable all interactive elements after processing."""
        self.target_search.disabled = False
        self.search_button.disabled = False
        if self.target_dropdown.options:
            self.target_dropdown.disabled = False
        self.target_type.disabled = False
        self.start_date_button.disabled = False
        self.start_time_button.disabled = False
        self.end_date_button.disabled = False
        self.end_time_button.disabled = False
        self.cancel_button.disabled = False
        self.submit_button.visible = True
        self.progress_ring.visible = False
        self.modal = False
        self.update()

    async def search_target(self, event):
        """Search for users or groups based on the search term."""
        if not self.target_search.value:
            self.target_search.error = _("Please enter a search term")
            self.update()
            return

        yield self.disable_interactions()

        # Run the search in a background task
        self.page.run_task(
            self.controller.action_search_targets,
            self.target_search.value,
            self.target_type.value,
        )

    async def on_target_type_change(self, event: ft.Event[ft.RadioGroup]):
        """Handle target type change."""
        # Clear previous search results
        self.target_dropdown.options = []
        self.target_dropdown.value = None
        self.target_dropdown.disabled = True
        self.update()

    async def on_start_date_change(self, event: ft.Event[ft.DatePicker]):
        """Handle start date selection."""
        if event.control.value:
            self.start_date_text.value = event.control.value.strftime("%Y-%m-%d")
            self.update()

    async def on_start_time_change(self, event: ft.Event[ft.TimePicker]):
        """Handle start time selection."""
        if event.control.value:
            time_str = event.control.value
            self.start_time_text.value = time_str
            self.update()

    async def on_end_date_change(self, event: ft.Event[ft.DatePicker]):
        """Handle end date selection."""
        if event.control.value:
            self.end_date_text.value = event.control.value.strftime("%Y-%m-%d")
            self.update()

    async def on_end_time_change(self, event: ft.Event[ft.TimePicker]):
        """Handle end time selection."""
        if event.control.value:
            time_str = event.control.value
            self.end_time_text.value = time_str
            self.update()

    async def ok_button_click(self, event: ft.Event[ft.TextButton]):
        """Handle submit button click."""
        # Validate target selection
        if not self.target_dropdown.value:
            self.target_search.error = _("Please select a target")
            self.update()
            return

        yield self.disable_interactions()

        # Construct datetime strings
        start_datetime = f"{self.start_date_text.value} {self.start_time_text.value}"
        end_datetime = f"{self.end_date_text.value} {self.end_time_text.value}"

        # Run authorization in background task
        self.page.run_task(
            self.controller.action_authorize,
            self.target_dropdown.value,
            self.target_type.value,
            start_datetime,
            end_datetime,
        )

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        """Handle cancel button click."""
        self.close()
