"""
CFMS Client - Main application entry point.

This module initializes the Flet application, configures localization,
and sets up the UI components and page settings.
"""

import os
import warnings

import flet as ft
import flet_permission_handler as fph

from include.classes.config import AppConfig
from include.util.locale import set_translation

# Window configuration constants
DEFAULT_WINDOW_WIDTH = 1024
DEFAULT_WINDOW_HEIGHT = 768


async def main(page: ft.Page):
    """
    Main application entry point.

    Initializes the application by:
    1. Loading user language preferences
    2. Setting up translation system
    3. Importing UI models
    4. Configuring page settings and theme
    5. Setting up event handlers
    6. Navigating to the connect screen

    Args:
        page: Flet page instance
    """
    # Load language preference and set environment variable
    try:
        preferred_language = AppConfig().preferences.get("settings", {}).get(
            "language", "zh_CN"
        )

        # Set environment variable for gettext to use
        os.environ["LANGUAGE"] = preferred_language

        # Set translation singleton
        set_translation(preferred_language)

    except Exception as e:
        # If config fails, use default
        warnings.warn(
            f"Warning: Failed to load language preferences: {e}", RuntimeWarning
        )
        os.environ["LANGUAGE"] = "zh_CN"

    # Import UI Components

    # These imports are placed here to ensure that the locale
    # is set before any UI components are loaded
    from include.ui.controls.dialogs.dev import DevRequestDialog
    from include.ui.models.connect import ConnectToServerModel
    from include.ui.models.login import LoginModel
    from include.ui.models.about import AboutModel
    from include.ui.models.settings.overview import SettingsModel
    from include.ui.models.settings.connection import ConnectionSettingsModel
    from include.ui.models.settings.safety import SafetySettingsModel
    from include.ui.models.settings.language import LanguageSettingsModel
    from include.ui.models.home import HomeModel
    from include.ui.models.manage import ManageModel
    from include.ui.models.debugging import DebuggingViewModel

    # Configure page settings
    page.title = "CFMS Client"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = DEFAULT_WINDOW_WIDTH
    page.window.height = DEFAULT_WINDOW_HEIGHT
    page.window.resizable = False
    page.padding = 0
    page.spacing = 0
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = ft.Colors.TRANSPARENT

    # Configure fonts
    page.fonts = {
        "Source Han Serif SC Regular": "/fonts/SourceHanSerifSC/SourceHanSerifSC-Regular.otf",
    }

    # Configure theme
    page.theme = ft.Theme(
        scrollbar_theme=ft.ScrollbarTheme(thickness=0.0),
        snackbar_theme=ft.SnackBarTheme(
            show_close_icon=True,
            behavior=ft.SnackBarBehavior.FLOATING,
        ),
        font_family="Source Han Serif SC Regular",
    )
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.decoration = ft.BoxDecoration(
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=["#10162c", "#0c2749", "#0f0f23", "#1a1a2e"],
            tile_mode=ft.GradientTileMode.MIRROR,
        )
    )

    # Disable browser context menu in web mode
    if page.web:
        await page.browser_context_menu.disable()

    def on_keyboard(e: ft.KeyboardEvent):
        """
        Handle keyboard shortcuts.

        Ctrl+W: Toggle semantics debugger
        Ctrl+Q: Open developer request dialog
        """
        if e.key == "W" and e.ctrl:
            page.show_semantics_debugger = not page.show_semantics_debugger
            page.update()
        elif e.key == "Q" and e.ctrl:
            page.show_dialog(DevRequestDialog())

    # Register event handlers
    page.on_keyboard_event = on_keyboard

    # Register services
    ph_service = fph.PermissionHandler()
    page.services.append(ph_service)

    AppConfig().ph_service = ph_service

    # Navigate to initial screen
    await page.push_route("/connect")


if __name__ == "__main__":
    ft.run(main)
