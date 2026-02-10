"""
Reusable Access Denied Content Component

This module provides a reusable UI component for displaying access denied messages
in different contexts (dialogs, views, etc.). It supports both compact and full-screen modes.
"""

from typing import Callable, Optional

import flet as ft

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class AccessDeniedContent(ft.Column):
    """
    Reusable content component for displaying access denied messages.

    This component can be used in both dialogs (compact mode) and full-screen views,
    providing a consistent UI across the application while adapting to space constraints.
    """

    def __init__(
        self,
        reason: str,
        show_back_button: bool = True,
        on_back_click: Optional[Callable] = None,
        compact_mode: bool = False,
        ref: ft.Ref | None = None,
    ):
        """
        Initialize the access denied content.

        Args:
            reason: The specific reason for access denial (from server message)
            show_back_button: Whether to show the "Go Back" button
            on_back_click: Optional callback function when back button is clicked
            compact_mode: True for dialog mode (smaller), False for full-screen view
            ref: Optional Flet reference
        """
        super().__init__(ref=ref)

        # Store parameters
        self.reason_value = reason
        self.on_back_click = on_back_click
        self.compact_mode = compact_mode

        # Adjust sizing based on mode
        icon_size = 60 if compact_mode else 80
        title_size = 22 if compact_mode else 28
        message_size = 14 if compact_mode else 16
        reason_size = 13 if compact_mode else 14

        # Create icon
        self.icon = ft.Icon(
            ft.Icons.LOCK,
            size=icon_size,
            color=ft.Colors.WHITE,
        )

        # Create title
        self.title_text = ft.Text(
            _("Access Denied"),
            size=title_size,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        # Create message
        self.message_text = ft.Text(
            _(
                "You don't have permission to access this directory. "
                "The reasons are as follows:"
            ),
            size=message_size,
            text_align=ft.TextAlign.CENTER,
        )

        # Create reason text (scrollable in case of long messages)
        self.reason_text = ft.Text(
            self.reason_value,
            size=reason_size,
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

        # Create additional info (shorter for compact mode)
        if compact_mode:
            additional_info = _(
                "Please contact your system administrator if you believe "
                "this is an error."
            )
        else:
            additional_info = _(
                "According to the server's protocol, you do not have "
                "permission to access the requested directory. There "
                "could be various reasons for this. If you have any "
                "questions about this situation, please contact your "
                "system administrator. This incident will be reported."
            )

        self.additional_info_text = ft.Text(
            additional_info,
            size=reason_size,
            text_align=ft.TextAlign.CENTER,
            color=ft.Colors.GREY_400,
        )

        # Create back button if requested
        controls = [
            self.icon,
            ft.Container(height=15 if compact_mode else 20),  # Spacer
            self.title_text,
            ft.Container(height=8 if compact_mode else 10),  # Spacer
            self.message_text,
            ft.Container(height=15 if compact_mode else 20),  # Spacer
            self.reason_container,
            ft.Container(height=10 if compact_mode else 15),  # Spacer
            self.additional_info_text,
        ]

        if show_back_button and on_back_click:
            self.back_button = ft.Button(
                content=_("Go Back"),
                icon=ft.Icons.ARROW_BACK,
                on_click=on_back_click,
            )
            controls.extend(
                [
                    ft.Container(height=20 if compact_mode else 30),  # Spacer
                    ft.Row(
                        controls=[self.back_button],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ]
            )

        # Set up column properties
        self.controls = controls
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO

    def update_reason(self, reason: str):
        """
        Update the displayed reason for access denial.

        Args:
            reason: The new reason text to display
        """
        self.reason_value = reason
        self.reason_text.value = reason
        self.update()
