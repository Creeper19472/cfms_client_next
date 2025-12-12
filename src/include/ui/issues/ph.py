import flet as ft
import flet_permission_handler as fph
import logging

logging.basicConfig(level=logging.DEBUG)

data = {}

async def process():
    p: fph.PermissionHandler = data["p"]
    print("Requesting permission for MANAGE_EXTERNAL_STORAGE")
    await p.request(
        fph.Permission.MANAGE_EXTERNAL_STORAGE
    )
    print("Done requesting permission")
    

async def handler():
    await process()

async def main(page: ft.Page):
    p = fph.PermissionHandler()
    # page.services.append(p)
    data["p"] = p
    await page.push_route("/issues/ph")
    page.run_task(handler)

if __name__ == "__main__":
    ft.run(main)