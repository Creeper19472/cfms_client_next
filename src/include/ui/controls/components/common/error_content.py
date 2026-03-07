"""
Reusable Error Content Component

This module provides a reusable UI component for displaying error messages
with retry and navigation options. It supports both compact and full-screen modes.
"""

from typing import Callable

import flet as ft
from flet_material_symbols import Symbols

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class ErrorContent(ft.Column):
    """
    Reusable content component for displaying error messages with action buttons.

    This component can be used in both dialogs (compact mode) and full-screen views,
    providing a consistent error UI across the application while adapting to space constraints.
    """

    def __init__(
        self,
        error_code: int,
        error_message: str,
        show_retry_button: bool = True,
        show_back_button: bool = True,
        on_retry_click: Callable | None = None,
        on_back_click: Callable | None = None,
        compact_mode: bool = False,
        ref: ft.Ref | None = None,
    ):
        """
        Initialize the error content.

        Args:
            error_code: HTTP error code (e.g., 404, 500)
            error_message: The error message from server
            show_retry_button: Whether to show the "Retry" button
            show_back_button: Whether to show the "Go Back" button
            on_retry_click: Optional callback function when retry button is clicked
            on_back_click: Optional callback function when back button is clicked
            compact_mode: True for dialog mode (smaller), False for full-screen view
            ref: Optional Flet reference
        """
        super().__init__(ref=ref)

        # Store parameters
        self.error_code = error_code
        self.error_message_value = error_message
        self.on_retry_click = on_retry_click
        self.on_back_click = on_back_click
        self.compact_mode = compact_mode

        # Adjust sizing based on mode
        icon_size = 60 if compact_mode else 80
        title_size = 22 if compact_mode else 28
        message_size = 14 if compact_mode else 16
        detail_size = 13 if compact_mode else 14

        # Determine icon and title based on error code
        icon, title_text = self._get_icon_and_title(error_code)

        # Create icon
        self.icon = ft.Icon(
            icon,
            size=icon_size,
            color=ft.Colors.WHITE,
        )

        # Create title
        self.title_text = ft.Text(
            title_text,
            size=title_size,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        # Create message
        self.message_text = ft.Text(
            self._get_description(error_code),
            size=message_size,
            text_align=ft.TextAlign.CENTER,
        )

        # Create error details (scrollable in case of long messages)
        self.error_detail_text = ft.Text(
            self.error_message_value,
            size=detail_size,
            text_align=ft.TextAlign.CENTER,
            color=ft.Colors.GREY_400,
        )
        self.error_detail_container = ft.Container(
            content=self.error_detail_text,
            padding=10,
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.GREY_700),
                bottom=ft.BorderSide(1, ft.Colors.GREY_700),
            ),
        )

        # Create additional info
        additional_info = self._get_additional_info(error_code, compact_mode)

        self.additional_info_text = ft.Text(
            additional_info,
            size=detail_size,
            text_align=ft.TextAlign.CENTER,
            color=ft.Colors.GREY_400,
        )

        # Build controls list
        controls = [
            self.icon,
            ft.Container(height=15 if compact_mode else 20),  # Spacer
            self.title_text,
            ft.Container(height=8 if compact_mode else 10),  # Spacer
            self.message_text,
            ft.Container(height=15 if compact_mode else 20),  # Spacer
            self.error_detail_container,
            ft.Container(height=10 if compact_mode else 15),  # Spacer
            self.additional_info_text,
        ]

        # Create action buttons if requested
        button_row_controls = []

        if show_back_button and on_back_click:
            self.back_button = ft.Button(
                content=_("Go Back"),
                icon=Symbols.ARROW_BACK,
                on_click=on_back_click,
            )
            button_row_controls.append(self.back_button)

        if show_retry_button and on_retry_click:
            self.retry_button = ft.Button(
                content=_("Retry"),
                icon=Symbols.REFRESH,
                on_click=on_retry_click,
            )
            button_row_controls.append(self.retry_button)

        if button_row_controls:
            controls.extend(
                [
                    ft.Container(height=20 if compact_mode else 30),  # Spacer
                    ft.Row(
                        controls=button_row_controls,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                ]
            )

        # Set up column properties
        self.controls = controls
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO

    _ERROR_METADATA = {
        0: {
            "icon": Symbols.ERROR,
            "title": _("Connection Error"),
            "description": _(
                "Could not connect to the server or an unexpected error occurred."
            ),
        },
        404: {
            "icon": Symbols.SEARCH_OFF,
            "title": _("Not Found"),
            "description": _("The requested directory or file could not be found."),
        },
        500: {
            "icon": Symbols.ERROR_OUTLINE,
            "title": _("Server Error"),
            "description": _("The server encountered an internal error."),
        },
        502: {
            "icon": Symbols.ERROR_OUTLINE,
            "title": _("Server Error"),
            "description": _("The server received an invalid response from upstream."),
        },
        503: {
            "icon": Symbols.ERROR_OUTLINE,
            "title": _("Server Error"),
            "description": _("The server is temporarily unavailable."),
        },
        400: {
            "icon": Symbols.WARNING,
            "title": _("Bad Request"),
            "description": _("The request was invalid or malformed."),
        },
        401: {
            "icon": Symbols.LOCK_CLOCK,
            "title": _("Unauthorized"),
            "description": _("Your session may have expired. Please try again."),
        },
        408: {
            "icon": Symbols.TIMER_OFF,
            "title": _("Request Timeout"),
            "description": _("The request took too long to complete."),
        },
        "default": {
            "icon": Symbols.ERROR,
            "title": _("Error"),
            "description": _("An error occurred while processing your request."),
        },
    }

    def _get_error_metadata(self, error_code: int) -> dict:
        """Return metadata for the given error code, falling back to a default."""
        return self._ERROR_METADATA.get(error_code, self._ERROR_METADATA["default"])

    def _get_icon_and_title(self, error_code: int) -> tuple[ft.IconData, str]:
        """Get appropriate icon and title for error code."""
        meta = self._get_error_metadata(error_code)
        return meta["icon"], meta["title"]

    def _get_description(self, error_code: int) -> str:
        """Get user-friendly description for error code."""
        meta = self._get_error_metadata(error_code)
        return meta["description"]

    def _get_additional_info(self, error_code: int, compact_mode: bool) -> str:
        """Get additional information text based on error code and mode."""
        if compact_mode:
            if error_code == 0:
                return _("Check your connection and try again.")
            elif error_code in (500, 502, 503):
                return _(
                    "Please try again later or contact support if the problem persists."
                )
            elif error_code == 404:
                return _("The item may have been moved or deleted.")
            else:
                return _("Please try again or contact support if needed.")
        else:
            if error_code == 0:
                return _(
                    "A connection error or unexpected exception occurred. "
                    "Please check your network connection and try again. "
                    "If the problem persists, contact your system administrator."
                )
            elif error_code in (500, 502, 503):
                return _(
                    "The server is experiencing technical difficulties. "
                    "This is typically a temporary issue. Please wait a moment "
                    "and try again. If the problem persists, contact your system administrator."
                )
            elif error_code == 404:
                return _(
                    "The requested resource could not be found on the server. "
                    "It may have been moved, renamed, or deleted. Please verify "
                    "the path and try again."
                )
            else:
                return _(
                    "An unexpected error occurred. Please try again. "
                    "If the problem persists, contact your system administrator "
                    "for assistance."
                )

    def update_error(self, error_code: int, error_message: str):
        """
        Update the displayed error information.

        Args:
            error_code: The new error code
            error_message: The new error message
        """
        self.error_code = error_code
        self.error_message_value = error_message

        # Update icon and title
        icon, title_text = self._get_icon_and_title(error_code)
        self.icon.icon = icon
        self.title_text.value = title_text

        # Update message texts
        self.message_text.value = self._get_description(error_code)
        self.error_detail_text.value = error_message
        self.additional_info_text.value = self._get_additional_info(
            error_code, self.compact_mode
        )

        self.update()
