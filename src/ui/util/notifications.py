import flet as ft

from include.ui import constants as const


def send_error(page: ft.Page | ft.BasePage, message: str):
    error_snack_bar = ft.SnackBar(
        content=ft.Text(message),
        duration=ft.Duration(seconds=4),
        bgcolor=const.ERROR_COLOR,
    )
    page.show_dialog(error_snack_bar)


def send_success(page: ft.Page | ft.BasePage, message: str):
    success_snack_bar = ft.SnackBar(
        content=ft.Text(message),
        duration=ft.Duration(seconds=4),
        bgcolor=const.SUCCESS_COLOR,
    )
    page.show_dialog(success_snack_bar)


def send_info(page: ft.Page | ft.BasePage, message: str):
    info_snack_bar = ft.SnackBar(
        content=ft.Text(message),
        duration=ft.Duration(seconds=4),
        bgcolor=ft.Colors.BLUE_200,
    )
    page.show_dialog(info_snack_bar)
