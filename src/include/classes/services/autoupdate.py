"""Automatic update checking service."""

import asyncio
from typing import Optional

import flet as ft

from include import constants
from include.classes.shared import AppShared
from include.classes.services.base import BaseService
from include.classes.version import ChannelType
from include.constants import BUILD_VERSION
from include.util.upgrade.updater import (
    GithubRelease,
    get_latest_release,
    is_new_version,
)

__all__ = ["AutoUpdateService"]

# Constants for configuration
SNACKBAR_DURATION_MS = 7000  # Show snackbar for 7 seconds


class AutoUpdateService(BaseService):
    """
    Service that periodically checks for application updates.

    This service runs in the background and checks for new versions
    of the application from the GitHub releases. When a new version
    is detected, it can notify the user through a snackbar.

    Attributes:
        page: Flet page instance for UI notifications
        check_on_start: Whether to check for updates immediately on start
        notify_user: Whether to notify user when updates are found
        last_checked_version: Last version that was checked
    """

    def __init__(
        self,
        page: Optional[ft.Page] = None,
        enabled: bool = True,
        interval: float = 3600.0,  # Check every hour by default
        check_on_start: bool = True,
        notify_user: bool = True,
    ):
        """
        Initialize the auto-update service.

        Args:
            page: Flet page instance for UI updates
            enabled: Whether service is enabled
            interval: Check interval in seconds (default: 3600 = 1 hour)
            check_on_start: Whether to check immediately on start
            notify_user: Whether to show notifications for updates
        """
        super().__init__(name="autoupdate", enabled=enabled, interval=interval)
        self.page = page
        self.check_on_start = check_on_start
        self.notify_user = notify_user
        self.last_checked_version: Optional[str] = None
        self._first_run = True

    async def on_start(self):
        """Initialize service on start."""
        self.logger.info(
            f"Auto-update service starting with interval: {self.interval}s, "
            f"check_on_start: {self.check_on_start}, notify_user: {self.notify_user}"
        )
        self._first_run = True

    async def execute(self):
        """
        Execute update check.

        This method is called periodically based on the interval setting.
        It checks for new versions and optionally notifies the user.
        """

        if AppShared().is_production is False:
            self.logger.info("Skipping update check: not in production mode")
            return

        # Skip first execution if check_on_start is False
        if self._first_run and not self.check_on_start:
            self.logger.info("Skipping first update check as check_on_start is False")
            self._first_run = False
            return

        self._first_run = False

        self.logger.info("Checking for application updates...")

        try:
            channel_pref = (
                AppShared().preferences.get("settings", {}).get("update_channel")
            )
            preferred_channel = (
                ChannelType(channel_pref)
                if channel_pref
                else constants.DEFAULT_UPDATE_CHANNEL
            )

            # Run the blocking API call in an executor to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            latest_release: Optional[GithubRelease] = await loop.run_in_executor(
                None, get_latest_release, preferred_channel
            )

            if not latest_release:
                self.logger.warning("Could not retrieve latest release information")
                return

            self.logger.info(f"Latest version available: {latest_release.version}")

            # Check if this is a new version
            # Parameters: is_preview=False (stable releases), commit_count=0 (not used for stable)
            if is_new_version(False, 0, BUILD_VERSION, latest_release.version):
                self.logger.info(
                    f"New version detected: {latest_release.version} "
                    f"(current: {BUILD_VERSION})"
                )

                # Only notify if this is a different version than last checked
                if self.last_checked_version != latest_release.version:
                    self.last_checked_version = latest_release.version

                    if self.notify_user and self.page:
                        await self._notify_update_available(latest_release)
            else:
                self.logger.info(f"Already on latest version: {BUILD_VERSION}")

        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}", exc_info=True)

    async def _notify_update_available(self, release: GithubRelease):
        """
        Notify user that an update is available.

        Args:
            release: The new release information
        """
        try:
            if not self.page:
                self.logger.warning("Cannot notify user: page instance not set")
                return

            # Import here to avoid circular imports
            from include.util.locale import get_translation

            t = get_translation()
            _ = t.gettext

            async def navigate_to_about(e):
                """Navigate to about page with proper error handling."""
                try:
                    assert self.page is not None
                    await self.page.push_route(self.page.route + "/about")
                except Exception as nav_error:
                    self.logger.error(f"Error navigating to about page: {nav_error}")

            snackbar = ft.SnackBar(
                content=ft.Text(
                    _(
                        "New version {version} is available! Check the About page for details."
                    ).format(version=release.version)
                ),
                action=_("Go to About"),
                bgcolor=ft.Colors.BLUE_200,
                duration=ft.Duration(milliseconds=SNACKBAR_DURATION_MS),
                # When `action` exists, `persist` must be explicitly specified to enable automatic shutdown.
                persist=False,
                on_action=lambda e: asyncio.create_task(navigate_to_about(e)),
            )

            # Show snackbar on the UI thread
            self.page.show_dialog(snackbar)
            self.page.update()

            # If user is on the connect page, add indicator badge to FloatingUpgradeButton
            app_shared = AppShared()
            if app_shared.floating_upgrade_button is not None:
                app_shared.floating_upgrade_button.show_update_badge()
                self.logger.info("Update badge shown on FloatingUpgradeButton")

            self.logger.info(f"User notified of update: {release.version}")

        except Exception as e:
            self.logger.error(f"Error notifying user of update: {e}", exc_info=True)

    async def check_now(self) -> Optional[GithubRelease]:
        """
        Manually trigger an immediate update check.

        This bypasses the interval timer and checks for updates immediately.

        Returns:
            The latest release if a new version is available, None otherwise
        """
        self.logger.info("Manual update check requested")

        try:
            loop = asyncio.get_running_loop()
            latest_release: Optional[GithubRelease] = await loop.run_in_executor(
                None, get_latest_release
            )

            if not latest_release:
                return None

            if is_new_version(False, 0, BUILD_VERSION, latest_release.version):
                self.last_checked_version = latest_release.version
                return latest_release

            return None

        except Exception as e:
            self.logger.error(f"Error in manual update check: {e}", exc_info=True)
            return None
