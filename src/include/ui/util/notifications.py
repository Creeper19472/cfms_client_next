import flet as ft
from include.ui import constants as const


def send_error(page: ft.Page|ft.BasePage, message: str):
    error_snack_bar = ft.SnackBar(
        content=ft.Text(message),
        show_close_icon=True,
        duration=ft.Duration(seconds=4),
        behavior=ft.SnackBarBehavior.FLOATING,
        bgcolor=const.ERROR_COLOR,
    )
    page.show_dialog(error_snack_bar)