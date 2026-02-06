"""
Access Denied View Component

This module provides a UI component that displays when directory access is denied.
It replaces the normal file list with a clear "Access Denied" message.
"""

from typing import TYPE_CHECKING

import flet as ft

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileManagerView

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class AccessDeniedView(ft.Container):
    """
    View component shown when directory access is denied due to insufficient permissions (403).

    This component is embedded within the file browser and replaces the normal file list
    when the server denies access to a directory. It provides clear feedback and navigation
    options to help the user understand why access was denied.
    """

    def __init__(
        self,
        parent_manager: "FileManagerView",
        reason: str,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        """
        Initialize the access denied view.

        Args:
            parent_manager: Reference to the parent FileManagerView
            reason: The specific reason for access denial (from server message)
            ref: Optional Flet reference
            visible: Whether the view is initially visible
        """
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.parent_manager = parent_manager

        # Styling
        self.expand = True
        self.alignment = ft.Alignment.CENTER
        self.padding = ft.Padding(top=30, left=40, right=40)

        # Create icon
        self.icon = ft.Icon(
            ft.Icons.LOCK,
            size=80,
            color=ft.Colors.WHITE,
        )

        # Create title
        self.title_text = ft.Text(
            _("Access Denied"),
            size=28,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        # Create message
        self.message_text = ft.Text(
            _(
                "You don't have permission to access this directory. "
                "The reasons are as follows:"
            ),
            size=16,
            text_align=ft.TextAlign.CENTER,
        )

        # Create reason text (scrollable in case of long messages)
        self.reason_text = ft.Text(
            reason,
            size=14,
            text_align=ft.TextAlign.CENTER,
            color=ft.Colors.GREY_400,
        )
        self.reason_container = ft.Container(
            content=self.reason_text,
            padding=10,
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.GREY_700),
                bottom=ft.BorderSide(1, ft.Colors.GREY_700),
            ),
        )

        self.additional_info_text = ft.Text(
            _(
                "According to the server's protocol, you do not have "
                "permission to access the requested directory. There "
                "could be various reasons for this. If you have any "
                "questions about this situation, please contact your "
                "system administrator. This incident will be reported."
            ),
            size=14,
            text_align=ft.TextAlign.CENTER,
            color=ft.Colors.GREY_400,
            margin=ft.Margin(top=20),
        )

        # Create back button
        self.back_button = ft.Button(
            content=_("Go Back"),
            icon=ft.Icons.ARROW_BACK,
            on_click=self.back_button_click,
        )

        # # Create refresh button
        # self.refresh_button = ft.OutlinedButton(
        #     content=_("Try Again"),
        #     icon=ft.Icons.REFRESH,
        #     on_click=self.refresh_button_click,
        # )

        # Build the content layout
        self.content = ft.Column(
            controls=[
                self.icon,
                ft.Container(height=20),  # Spacer
                self.title_text,
                ft.Container(height=10),  # Spacer
                self.message_text,
                ft.Container(height=20),  # Spacer
                self.reason_container,
                self.additional_info_text,
                ft.Container(height=30),  # Spacer
                ft.Row(
                    controls=[
                        self.back_button,
                        # self.refresh_button,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

    async def back_button_click(self, event: ft.Event[ft.Button]):
        """Navigate back to the previous directory."""
        from include.ui.util.path import get_directory

        # Get the parent directory ID
        parent_id = self.parent_manager.file_listview.current_parent_id

        # Hide this view and show loading
        self.visible = False

        # according to the current implementation, the parent directory ID will not be updated unless the
        # directory is successfully accessed, so we can just use the current directory ID to try to access it again
        await get_directory(
            self.parent_manager.current_directory_id, self.parent_manager.file_listview
        )
        # self.parent_manager.progress_ring.visible = True
        # self.update()
        # self.parent_manager.progress_ring.update()

        # # Navigate back using the path indicator
        # if parent_id is not None:
        #     await get_directory(parent_id, self.parent_manager.file_listview)
        #     self.parent_manager.indicator.back()
        # else:
        #     # If no parent, go to root
        #     await get_directory(
        #         self.parent_manager.root_directory_id,
        #         self.parent_manager.file_listview,
        #     )
        #     self.parent_manager.indicator.reset()

    async def refresh_button_click(self, event: ft.Event[ft.OutlinedButton]):
        """Try to access the directory again."""
        from include.ui.util.path import get_directory

        # Hide this view and show loading
        self.visible = False
        self.parent_manager.progress_ring.visible = True
        self.update()
        self.parent_manager.progress_ring.update()

        # Try to access the current directory again
        current_dir_id = self.parent_manager.current_directory_id
        await get_directory(current_dir_id, self.parent_manager.file_listview)

    def update_reason(self, reason: str):
        """
        Update the displayed reason for access denial.

        Args:
            reason: The new reason text to display
        """
        self.reason_text.value = reason
        self.update()
