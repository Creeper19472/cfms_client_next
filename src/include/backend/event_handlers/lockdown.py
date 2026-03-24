__all__ = ["lockdown_handler"]

from typing import Optional
import flet as ft

from include.classes.shared import AppShared
from include.ui.controls.banners.lockdown import LockdownBanner
from include.ui.util.route import get_parent_route


async def lockdown_handler(event: str, data: dict, page: Optional[ft.Page] = None):
    if page is None:
        return

    if not data["status"]:
        LockdownBanner().visible = False

    if not AppShared().username:  # only if logged in
        return

    if data["status"]:
        LockdownBanner().visible = True
        if "bypass_lockdown" not in AppShared().user_permissions:
            AppShared().app_lockdown = True
            await page.push_route(page.route + "/lockdown")
    else:
        if AppShared().app_lockdown:
            AppShared().app_lockdown = False
            await page.push_route(get_parent_route(page.route))
