"""Background service for periodic CA certificate store updates."""

from __future__ import annotations

import asyncio
import time
from typing import Optional

import flet as ft

from include.classes.services.base import BaseService
from include.constants import ROOT_PATH
from include.util.ca_update import (
    CACertUpdateResult,
    check_and_update_ca_certs,
    has_expired_certificates,
    load_last_check_time,
    save_last_check_time,
)

__all__ = ["CACertUpdateService"]

# Default: check once per day (86 400 seconds)
DEFAULT_INTERVAL = 86_400.0

# Mandatory check threshold: 90 days (≈ 3 months)
MANDATORY_CHECK_PERIOD = 90 * 24 * 3600.0

# Path to the bundled CA certificate directory
_CA_DIR = ROOT_PATH / "include" / "ca"


class CACertUpdateService(BaseService):
    """Periodically syncs the local CA certificate store with the remote repository.

    The remote repository is specified by
    :data:`include.constants.CA_CERT_API_URL`.  On each execution the service
    calls :func:`~include.util.ca_update.check_and_update_ca_certs` inside a
    thread-pool executor to avoid blocking the event loop.

    **Mandatory check conditions** — a check is forced immediately on startup
    (regardless of *check_on_start*) when any of the following is true:

    * No check has ever been recorded (first run ever).
    * The last check is older than :data:`MANDATORY_CHECK_PERIOD` (90 days).
    * At least one local CA certificate has expired.

    The :attr:`last_updated` timestamp (Unix time) and the result of the most
    recent run (:attr:`last_result`) are available for display in the UI.

    Concurrent calls to :meth:`update_now` (or simultaneous scheduled and
    manual runs) are serialised via an :class:`asyncio.Lock` so that only one
    update modifies the certificate store at a time.

    Attributes:
        page: Optional Flet page for UI notifications.
        check_on_start: Whether to run a routine update immediately on start.
            Mandatory checks bypass this flag.
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
        check_on_start: bool = True,
    ) -> None:
        super().__init__(name="ca_cert_update", enabled=enabled, interval=interval)
        self.page = page
        self.check_on_start = check_on_start
        self.last_updated: Optional[float] = None
        self.last_result: Optional[CACertUpdateResult] = None
        self._first_run = True
        self._update_lock: asyncio.Lock = asyncio.Lock()

    def set_page(self, page: ft.Page) -> None:
        """Attach (or replace) the Flet page used for notifications."""
        self.page = page

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    async def on_start(self) -> None:
        self.logger.info(
            "CA cert update service starting; interval=%.0fs, check_on_start=%s",
            self.interval,
            self.check_on_start,
        )
        # Restore the persisted last-check timestamp so mandatory conditions
        # are evaluated correctly even after an application restart.
        persisted = load_last_check_time(_CA_DIR)
        if persisted is not None:
            self.last_updated = persisted
            self.logger.debug(
                "Restored last CA cert check timestamp: %s",
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(persisted)),
            )
        self._first_run = True

    # ------------------------------------------------------------------
    # Periodic execution
    # ------------------------------------------------------------------

    async def execute(self) -> None:
        """Run a CA certificate store update.

        On the very first call (at service startup) the method evaluates
        *mandatory check conditions* before honouring :attr:`check_on_start`:

        * **Never checked / first ever run**: no ``.last_check`` file exists.
        * **Stale**: the last recorded check is older than
          :data:`MANDATORY_CHECK_PERIOD` (90 days).
        * **Expired certificate**: at least one local ``.pem``/``.crt`` file
          has a *Not After* date in the past.

        If any mandatory condition is met the update runs immediately.
        Otherwise the normal *check_on_start* flag decides whether to run.
        """
        if self._first_run:
            self._first_run = False
            mandatory, reason = self._is_mandatory_check_needed()
            if mandatory:
                self.logger.info("Mandatory CA cert check triggered: %s", reason)
                await self._run_update()
            elif self.check_on_start:
                await self._run_update()
            else:
                self.logger.info("Skipping startup CA cert check (check_on_start=False)")
            return

        # Subsequent interval-based runs always execute.
        await self._run_update()

    # ------------------------------------------------------------------
    # Mandatory check helpers
    # ------------------------------------------------------------------

    def _is_mandatory_check_needed(self) -> tuple[bool, str]:
        """Return ``(True, reason)`` when a mandatory check must run.

        Checks (in order):

        1. No previous check recorded (``last_updated`` is ``None``).
        2. Last check is older than :data:`MANDATORY_CHECK_PERIOD`.
        3. At least one local certificate has expired.
        """
        if self.last_updated is None:
            return True, "no previous check recorded"

        elapsed = time.time() - self.last_updated
        if elapsed >= MANDATORY_CHECK_PERIOD:
            days = elapsed / DEFAULT_INTERVAL
            return True, f"last check was {days:.0f} days ago (threshold: 90 days)"

        # Run the potentially expensive expiry scan only when the time-based
        # conditions are not already met.
        try:
            expired = has_expired_certificates(_CA_DIR)
        except Exception as exc:
            self.logger.warning("Could not check certificate expiry: %s", exc)
            expired = False

        if expired:
            return True, "one or more local CA certificates have expired"

        return False, ""

    # ------------------------------------------------------------------
    # Core update logic
    # ------------------------------------------------------------------

    async def _run_update(self) -> CACertUpdateResult:
        """Execute the update in a thread-pool executor and store the result.

        Acquires :attr:`_update_lock` so that only one update runs at a time.

        Returns
        -------
        CACertUpdateResult
            The result of the update run.
        """
        async with self._update_lock:
            self.logger.info("Checking CA certificate store for updates…")
            loop = asyncio.get_running_loop()
            try:
                result: CACertUpdateResult = await loop.run_in_executor(
                    None,
                    check_and_update_ca_certs,
                    _CA_DIR,
                )
            except Exception as exc:
                self.logger.error(
                    "Unexpected error during CA cert update: %s", exc, exc_info=True
                )
                result = CACertUpdateResult(errors=[str(exc)])

            self.last_updated = time.time()
            self.last_result = result

            # Persist the timestamp so mandatory conditions survive restarts.
            save_last_check_time(_CA_DIR, self.last_updated)

            self.logger.info("CA cert update finished: %s", result)
            return result

    # ------------------------------------------------------------------
    # Public API – manual trigger
    # ------------------------------------------------------------------

    async def update_now(self) -> CACertUpdateResult:
        """Manually trigger an immediate CA certificate store update.

        This method can be called from the UI to run an out-of-schedule
        update and returns the :class:`~include.util.ca_update.CACertUpdateResult`.
        If an update is already in progress the call will wait for it to
        finish before starting a new one.
        """
        self.logger.info("Manual CA cert update requested")
        return await self._run_update()


