__all__ = ["lockdown_handler"]

from typing import Optional
import flet as ft

from include.classes.shared import AppShared
from include.ui.util.route import get_parent_route


async def lockdown_handler(event: str, data: dict, page: Optional[ft.Page] = None):
    if page is None:
        return

    if data["status"]:
        if 1: # Placeholder for future conditions (e.g. specific lockdown reasons)
            AppShared().lockdown_mode = True
            await page.push_route(page.route + "/lockdown")
    else:
        if AppShared().lockdown_mode:
            AppShared().lockdown_mode = False
            await page.push_route(get_parent_route(page.route))
