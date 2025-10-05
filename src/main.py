"""
Copyright 2025 Creeper19472

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import flet as ft
from include.ui.models.connect import ConnectToServerModel
from include.ui.models.login import LoginModel
from include.ui.models.about import AboutModel
from include.ui.models.settings import SettingsModel
from include.ui.models.home import HomeModel
from include.ui.models.manage import ManageModel

# import logging
# logging.basicConfig(level=logging.DEBUG)

async def main(page: ft.Page):
    # Page settings
    page.title = "CFMS Client"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1024
    page.window.height = 768
    page.window.resizable = False
    page.padding = 0
    page.spacing = 0
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = ft.Colors.TRANSPARENT

    page.fonts = {
        "Source Han Serif SC Regular": "/fonts/SourceHanSerifSC/SourceHanSerifSC-Regular.otf",
        # "Deng": "/fonts/Deng.ttf",
        # "Deng Bold": "/fonts/Dengb.ttf",
        # "Deng Light": "/fonts/Dengl.ttf"
    }

    page.theme = ft.Theme(
        scrollbar_theme=ft.ScrollbarTheme(thickness=0.0),
        # dialog_theme=ft.DialogTheme(title_text_style=ft.TextStyle(size=22, font_family="Deng Bold")),
        # text_button_theme=ft.TextButtonTheme(text_style=ft.TextStyle(font_family="Deng")),
        # elevated_button_theme=ft.ElevatedButtonTheme(text_style=ft.TextStyle(font_family="Deng")),
        font_family="Source Han Serif SC Regular",
    )
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.decoration = ft.BoxDecoration(
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=["#10162c", "#0c2749", "#0f0f23", "#1a1a2e"],
            tile_mode=ft.GradientTileMode.MIRROR,
        )
    )

    await page.push_route("/connect")


if __name__ == "__main__":
    ft.run(main)
