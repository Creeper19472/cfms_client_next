__all__ = ["lockdown_handler"]

from typing import Optional
import flet as ft

from include.classes.shared import AppShared
from include.ui.controls.banners.lockdown import LockdownBanner
from include.ui.util.route import get_parent_route


async def lockdown_handler(event: str, data: dict, page: Optional[ft.Page] = None):
    if not page:
        return

    status = data.get("status")
    shared = AppShared()
    banner = LockdownBanner()

    if status and banner not in page.overlay:
        page.overlay.append(banner)
    elif not status and banner in page.overlay:
        page.overlay.remove(banner)
    page.update()

    if not shared.username:
        return

    if status and "bypass_lockdown" not in shared.user_permissions:
        shared.app_lockdown = True
        if not page.route.endswith("/lockdown"):
            await page.push_route(f"{page.route}/lockdown")
    elif not status and shared.app_lockdown:
        shared.app_lockdown = False
        if page.route.endswith("/lockdown"):
            await page.push_route(get_parent_route(page.route))
