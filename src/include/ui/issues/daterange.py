import flet as ft
from datetime import datetime


def main(page: ft.Page):
    range_picker = ft.DateRangePicker(start_value=datetime.now(), end_value=datetime.now())
    page.show_dialog(range_picker)


if __name__ == "__main__":
    ft.run(main)