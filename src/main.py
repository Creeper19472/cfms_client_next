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

import os
import locale
import gettext
import flet as ft
from include.ui.controls.dialogs.dev import DevRequestDialog
from include.ui.models.connect import ConnectToServerModel
from include.ui.models.login import LoginModel
from include.ui.models.about import AboutModel
from include.ui.models.settings.overview import SettingsModel
from include.ui.models.settings.connection import ConnectionSettingsModel
from include.ui.models.settings.safety import SafetySettingsModel
from include.ui.models.settings.language import LanguageSettingsModel
from include.ui.models.home import HomeModel
from include.ui.models.manage import ManageModel
from include.classes.config import AppConfig

# import logging
# logging.basicConfig(level=logging.DEBUG)


async def main(page: ft.Page):
    # Load language preference and set environment variable
    try:
        app_config = AppConfig()
        preferred_language = app_config.preferences.get("settings", {}).get("language", "zh_CN")
        # Set environment variable for gettext to use
        os.environ["LANGUAGE"] = preferred_language
        # Also try to set locale
        try:
            if preferred_language == "zh_CN":
                locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
            elif preferred_language == "en":
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            pass  # Ignore locale setting errors
    except:
        # If config fails, use default
        os.environ["LANGUAGE"] = "zh_CN"
    
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
        snackbar_theme=ft.SnackBarTheme(
            show_close_icon=True,
            behavior=ft.SnackBarBehavior.FLOATING,
        ),
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

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "W" and e.ctrl:
            page.show_semantics_debugger = not page.show_semantics_debugger
            page.update()
        elif e.key == "Q" and e.ctrl:
            page.show_dialog(DevRequestDialog())

    # def on_state_change(e: ft.AppLifecycleStateChangeEvent):
    #     if e.data=='detach' and page.platform == ft.PagePlatform.ANDROID:
    #         os._exit(1)

    page.on_keyboard_event = on_keyboard
    # page.on_app_lifecycle_state_change = on_state_change

    await page.push_route("/connect")


if __name__ == "__main__":
    ft.run(main)
