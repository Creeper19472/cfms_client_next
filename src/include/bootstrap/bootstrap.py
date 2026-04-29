"""Application bootstrap helpers: logging setup and service registration.

This module centralises runtime initialization so `main.py` stays lean
and easier to test.
"""
from __future__ import annotations

import importlib
import inspect
import json
import logging
from pathlib import Path
from typing import Optional

import flet as ft

from include.constants import LOGFILE_PATH
from include.classes.shared import AppShared
from include.classes.services.manager import ServiceManager


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

    services_file = Path(__file__).parent / "services.json"

    def _import_class(path: str):
        module_name, _, cls_name = path.rpartition(".")
        module = importlib.import_module(module_name)
        return getattr(module, cls_name)

    def _instantiate_service(cls, provided_kwargs: dict):
        sig = inspect.signature(cls.__init__)
        inst_kwargs = dict(provided_kwargs or {})
        # inject common context objects when constructor accepts them
        if 'page' in sig.parameters and 'page' not in inst_kwargs:
            inst_kwargs['page'] = page
        if 'app_shared' in sig.parameters and 'app_shared' not in inst_kwargs:
            inst_kwargs['app_shared'] = app_shared
        return cls(**inst_kwargs)

    if not services_file.exists():
        logging.warning('services.json not found at %s; no services registered', services_file)
    else:
        try:
            with services_file.open('r', encoding='utf-8') as fh:
                entries = json.load(fh)
            for ent in entries:
                class_path = ent.get('class')
                if not class_path:
                    logging.warning('Skipping service entry without "class": %s', ent)
                    continue
                kwargs = ent.get('kwargs', {}) or {}
                try:
                    cls = _import_class(class_path)
                    instance = _instantiate_service(cls, kwargs)
                    service_manager.register(instance)
                    # if the service supports handlers and looks like server-stream, try to add lockdown handler
                    if hasattr(instance, 'add_handler') and 'server_stream' in class_path:
                        try:
                            mod = importlib.import_module('include.backend.event_handlers.lockdown')
                            handler = getattr(mod, 'lockdown_handler', None)
                            if handler is not None:
                                instance.add_handler('lockdown', handler)
                        except Exception:
                            logging.exception('Failed to add lockdown handler dynamically')
                except Exception:
                    logging.exception('Failed to instantiate/register service %s; continuing', class_path)
        except Exception:
            logging.exception('Failed to load services.json; no services registered')

    await service_manager.start_all()
    return service_manager


def register_page_close_handler(page: ft.Page, service_manager: ServiceManager) -> None:
    async def _on_page_close(e):
        logging.info("Page closing, stopping all services...")
        await service_manager.stop_all()

    page.on_close = _on_page_close
