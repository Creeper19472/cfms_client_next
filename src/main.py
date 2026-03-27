"""
CFMS Client - Main application entry point.

This module initializes the Flet application, configures localization,
and sets up the UI components and page settings.
"""

import os
import warnings

import flet as ft
import flet_permission_handler as fph

from include.constants import RUNTIME_PATH, ROOT_PATH
from include.classes.shared import AppShared
from app.bootstrap import configure_logging, setup_services, register_page_close_handler
from include.ui.controls.components.common.monitor import MonitorStack
from include.util.locale import set_translation
from include.util.ca_update import manifest_exists

DEFAULT_WINDOW_WIDTH = 1366
DEFAULT_WINDOW_HEIGHT = 768

# Configure logging via bootstrap helper (moved for testability)
configure_logging()


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
        preferred_language = (
            AppShared().preferences.get("settings", {}).get("language", "zh_CN")
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
    from include.ui.models.init import AppInitModel
    from include.ui.models.login import LoginModel
    from include.ui.models.about import AboutModel
    from include.ui.models.home import HomeModel
    from include.ui.models.manage import ManageModel
    from include.ui.models.debugging import DebuggingViewModel
    from include.ui.models.misc import DisclaimerModel, LockdownModel
    from include.ui.models.trash import TrashModel
    import include.ui.models.settings

    # Page settings

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
        "Google Sans Regular": "/fonts/GoogleSans/GoogleSans-Regular.ttf",
    }

    # Configure theme
    page.theme = ft.Theme(
        scrollbar_theme=ft.ScrollbarTheme(thickness=0.0),
        snackbar_theme=ft.SnackBarTheme(
            show_close_icon=True,
            behavior=ft.SnackBarBehavior.FLOATING,
        ),
        badge_theme=ft.BadgeTheme(
            text_style=ft.TextStyle(
                font_family="Google Sans Regular", size=10, weight=ft.FontWeight.BOLD
            )
        ),
        font_family="Source Han Serif SC Regular",
        icon_theme=ft.IconTheme(
            weight=400,
            fill=0,
            grade=0,
            optical_size=24,
        ),
        dialog_theme=ft.DialogTheme(
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
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
    # FIXME: browser context menu will be enabled again when refreshing the page
    if page.web:
        await ft.BrowserContextMenu().disable()

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
        elif e.key == "D" and e.ctrl:
            monitor.visible = not monitor.visible
            page.update()

    # Register event handlers
    page.on_keyboard_event = on_keyboard

    # Get app_shared
    app_shared = AppShared()

    # Set runtime platform info
    assert page.platform
    app_shared.is_mobile = page.platform.is_mobile()
    # `is_production` here indicates that the app is running from a packaged /
    # compiled runtime (where RUNTIME_PATH / PYTHONHOME is set), as opposed to
    # a development environment running from source.
    app_shared.is_production = bool(RUNTIME_PATH)
    page.window.resizable = not app_shared.is_production

    # Initialize and start services (moved to bootstrap for clarity)
    service_manager = await setup_services(page, app_shared)

    # Register cleanup handler for when the page closes
    # Register page close handler to stop services
    register_page_close_handler(page, service_manager)

    # Navigate to initial screen.
    # On first launch the CA cert manifest doesn't exist yet – show the
    # initialisation wizard.  On subsequent launches go straight to connect.
    _ca_dir = ROOT_PATH / "include" / "ca"
    if not manifest_exists(_ca_dir):
        await page.push_route("/init")
    else:
        await page.push_route("/connect")

    monitor_ref = ft.Ref[MonitorStack]()
    monitor = MonitorStack(ref=monitor_ref, visible=not AppShared().is_production)
    AppShared().monitor_ref = monitor_ref
    page.overlay.append(monitor)


if __name__ == "__main__":
    ft.run(main)
