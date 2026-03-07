"""Background service for periodic CA certificate store updates."""

import asyncio
import time
from typing import Callable, Optional

import flet as ft

from include.classes.services.base import BaseService
from include.constants import ROOT_PATH
from include.util.ca_update import (
    CACertUpdateResult,
    CACertUpdateStages,
    check_and_update_ca_certs,
    load_last_check_time,
    save_last_check_time,
)

__all__ = ["CACertUpdateService"]

# Periodic check interval: once every 90 days (≈ 3 months)
DEFAULT_INTERVAL = 90 * 24 * 3600.0

# Path to the bundled CA certificate directory
_CA_DIR = ROOT_PATH / "include" / "ca"


class CACertUpdateService(BaseService):
    """Periodically syncs the local CA certificate store with the remote repository.

    The remote repository is specified by
    :data:`include.constants.CA_CERT_API_URL`.  On each execution the service
    calls :func:`~include.util.ca_update.check_and_update_ca_certs` inside a
    thread-pool executor to avoid blocking the event loop.

    **Schedule** — :meth:`execute` is called by the base-class loop both on
    startup and every :attr:`~include.classes.services.base.BaseService.interval`
    seconds.  Each call checks the persisted ``last_updated`` timestamp and
    skips the actual work if a check was completed less than 90 days ago.
    This means the service runs silently at most once every 90 days regardless
    of how often the application is restarted.

    The :attr:`last_updated` timestamp (Unix time) and the result of the most
    recent run (:attr:`last_result`) are available for display in the UI.

    Concurrent calls to :meth:`update_now` (or simultaneous scheduled and
    manual runs) are serialised via an :class:`asyncio.Lock` so that only one
    update modifies the certificate store at a time.  The :attr:`is_updating`
    property exposes the lock state so the UI can prevent connections during
    a write.

    Attributes:
        page: Optional Flet page for UI notifications.
        last_updated: Unix timestamp of the most recent completed run, or
            ``None`` if no run has completed yet.
        last_result: :class:`~include.util.ca_update.CACertUpdateResult` from
            the most recent run, or ``None``.
    """

    def __init__(
        self,
        page: Optional[ft.Page] = None,
        enabled: bool = True,
        interval: float = DEFAULT_INTERVAL,
    ) -> None:
        super().__init__(name="ca_cert_update", enabled=enabled, interval=interval)
        self.page = page
        self.last_updated: Optional[float] = None
        self.last_result: Optional[CACertUpdateResult] = None
        self._update_lock: asyncio.Lock = asyncio.Lock()

    def set_page(self, page: ft.Page) -> None:
        """Attach (or replace) the Flet page used for notifications."""
        self.page = page

    @property
    def is_updating(self) -> bool:
        """Return ``True`` while a CA certificate store update is in progress.

        Exposed so the UI (e.g. the Connect button) can block connections
        while certificates are being written to disk (prevents dirty reads).
        """
        return self._update_lock.locked()

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    async def on_start(self) -> None:
        self.logger.info(
            "CA cert update service starting; interval=%.0f days",
            self.interval / 86_400,
        )
        # Restore the persisted last-check timestamp so the 90-day threshold
        # is evaluated correctly even after an application restart.
        persisted = load_last_check_time(_CA_DIR)
        if persisted is not None:
            self.last_updated = persisted
            self.logger.debug(
                "Restored last CA cert check timestamp: %s",
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(persisted)),
            )

    # ------------------------------------------------------------------
    # Periodic execution
    # ------------------------------------------------------------------

    async def execute(self) -> None:
        """Run a CA certificate store update if the 90-day threshold is met.

        Skips silently when a check was recorded less than
        :attr:`~include.classes.services.base.BaseService.interval` seconds
        ago (default 90 days), so the store is refreshed at most once per
        90-day window even if the application is restarted frequently.

        When ``last_updated`` is ``None`` (no check has ever been recorded
        in memory) the method re-reads the persisted timestamp from disk.
        This handles the first-launch case where the init wizard calls
        :func:`~include.util.ca_update.build_initial_manifest` *after* the
        service has already started (so ``on_start`` found no timestamp).
        If no timestamp is found on disk either, the run is skipped — the
        first-time setup wizard takes care of prompting the user.
        """
        if self.last_updated is None:
            persisted = load_last_check_time(_CA_DIR)
            if persisted is not None:
                self.last_updated = persisted
                self.logger.debug(
                    "CA cert check: re-read last-check timestamp from disk: %s",
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(persisted)),
                )
            else:
                self.logger.debug(
                    "CA cert check: no prior check recorded; "
                    "waiting for user-initiated update or next 90-day window."
                )
                return

        elapsed = time.time() - self.last_updated
        if elapsed < self.interval:
            self.logger.debug(
                "CA cert check: last check was %.1f days ago (threshold %.0f days); skipping.",
                elapsed / 86_400,
                self.interval / 86_400,
            )
            return

        self.logger.info(
            "CA cert periodic check: last check was %.1f days ago; running update.",
            elapsed / 86_400,
        )
        await self._run_update()

    # ------------------------------------------------------------------
    # Core update logic
    # ------------------------------------------------------------------

    async def _run_update(
        self,
        on_progress: Optional[Callable[[CACertUpdateStages, str], None]] = None,
    ) -> CACertUpdateResult:
        """Execute the update in a thread-pool executor and store the result.

        Acquires :attr:`_update_lock` so that only one update runs at a time.

        Parameters
        ----------
        on_progress:
            Optional two-argument callback ``(stage, detail)`` forwarded to
            :func:`~include.util.ca_update.check_and_update_ca_certs`.
            Called from the thread-pool thread — must be thread-safe.

        Returns
        -------
        CACertUpdateResult
            The result of the update run.
        """
        async with self._update_lock:
            self.logger.info("Checking CA certificate store for updates...")
            loop = asyncio.get_running_loop()
            try:
                result: CACertUpdateResult = await loop.run_in_executor(
                    None,
                    lambda: check_and_update_ca_certs(_CA_DIR, on_progress=on_progress),
                )
            except Exception as exc:
                self.logger.error(
                    "Unexpected error during CA cert update: %s", exc, exc_info=True
                )
                result = CACertUpdateResult(errors=[str(exc)])

            self.last_updated = time.time()
            self.last_result = result

            # Persist the timestamp so the 90-day threshold survives restarts.
            save_last_check_time(_CA_DIR, self.last_updated)

            self.logger.info("CA cert update finished: %s", result)
            return result

    # ------------------------------------------------------------------
    # Public API – manual trigger
    # ------------------------------------------------------------------

    async def update_now(
        self,
        on_progress: Optional[Callable[[CACertUpdateStages, str], None]] = None,
    ) -> CACertUpdateResult:
        """Manually trigger an immediate CA certificate store update.

        This method can be called from the UI to run an out-of-schedule
        update and returns the :class:`~include.util.ca_update.CACertUpdateResult`.
        If an update is already in progress the call will wait for it to
        finish before starting a new one.

        Parameters
        ----------
        on_progress:
            Optional two-argument callback ``(stage, detail)`` that receives
            progress notifications during the update.  *stage* is one of the
            ``CACertUpdateStages.*`` constants exported by
            :mod:`include.util.ca_update`; *detail* is an optional
            human-readable string (e.g. the filename being downloaded).
            The callback is invoked from a thread-pool thread and must be
            thread-safe.
        """
        self.logger.info("Manual CA cert update requested")
        return await self._run_update(on_progress=on_progress)
