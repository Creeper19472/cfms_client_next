"""Application bootstrap helpers: logging setup and service registration.

This module centralises runtime initialization so `main.py` stays lean
and easier to test.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import flet as ft

from include.constants import LOGFILE_PATH, ROOT_PATH
from include.classes.shared import AppShared
from include.classes.services.manager import ServiceManager
from include.classes.services.autoupdate import AutoUpdateService
from include.classes.services.ca_update import (
    CACertUpdateService,
    DEFAULT_INTERVAL as _CA_CHECK_INTERVAL,
)
from include.classes.services.download import DownloadManagerService
from include.classes.services.token_refresh import TokenRefreshService
from include.classes.services.favorites_validation import FavoritesValidationService
from include.classes.services.server_stream import ServerStreamHandleService
from include.backend.event_handlers.lockdown import lockdown_handler
from include.util.ca_update import manifest_exists


def configure_logging() -> None:
    """Configure root logger to write to the application logfile.

    This mirrors the previous in-module logging setup but is callable from
    tests or other runners.
    """
    _formatter = logging.Formatter("[%(asctime)s %(levelname)s] | %(name)s | %(message)s")

    log_path = Path(LOGFILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    _file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    _file_handler.setFormatter(_formatter)

    _root_logger = logging.getLogger()
    # Avoid adding duplicate handlers on repeated configure calls
    existing = [type(h) for h in _root_logger.handlers]
    if logging.FileHandler not in existing:
        _root_logger.addHandler(_file_handler)
    _root_logger.setLevel(logging.DEBUG)


async def setup_services(page: ft.Page, app_shared: Optional[AppShared] = None) -> ServiceManager:
    """Create ServiceManager, register core services and start them.

    Returns the created ServiceManager instance.
    """
    if app_shared is None:
        app_shared = AppShared()

    service_manager = ServiceManager()
    app_shared.service_manager = service_manager

    autoupdate_service = AutoUpdateService(
        page=page,
        enabled=True,
        interval=21600.0,
        check_on_start=True,
        notify_user=True,
    )
    service_manager.register(autoupdate_service)

    download_manager_service = DownloadManagerService(
        app_shared=app_shared,
        enabled=True,
        max_concurrent=3,
        enable_persistence=True,
    )
    service_manager.register(download_manager_service)

    token_refresh_service = TokenRefreshService(
        enabled=True,
        interval=60.0,
        refresh_threshold=300.0,
    )
    service_manager.register(token_refresh_service)

    favorites_validation_service = FavoritesValidationService(
        app_shared=app_shared,
        enabled=True,
        interval=300.0,
    )
    service_manager.register(favorites_validation_service)

    server_stream_service = ServerStreamHandleService(page=page, enabled=True)
    service_manager.register(server_stream_service)
    server_stream_service.add_handler("lockdown", lockdown_handler)

    ca_cert_update_service = CACertUpdateService(
        page=page,
        enabled=True,
        interval=_CA_CHECK_INTERVAL,
    )
    service_manager.register(ca_cert_update_service)

    await service_manager.start_all()
    return service_manager


def register_page_close_handler(page: ft.Page, service_manager: ServiceManager) -> None:
    async def _on_page_close(e):
        logging.info("Page closing, stopping all services...")
        await service_manager.stop_all()

    page.on_close = _on_page_close
