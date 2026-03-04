from typing import cast

from flet_model import Model, Router, route
import flet_permission_handler as fph
import flet as ft

from include.classes.preferences import UserPreference
from include.classes.shared import AppShared
from include.ui.controls.banners.settings import ExternalStorageWarningBanner
from include.ui.util.notifications import send_success
from include.ui.util.route import get_parent_route
from include.util.locale import get_translation
from include.util.userpref import save_user_preference

t = get_translation()
_ = t.gettext


@route("storage_settings")
class StorageSettingsModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)

        self.appbar = ft.AppBar(
            title=ft.Text(_("Storage")),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self._go_back),
            actions=[
                ft.IconButton(ft.Icons.SAVE_OUTLINED, on_click=self.save_button_click)
            ],
            actions_padding=10,
        )

        self.use_external_storage_switch = ft.Switch(
            label=_("Use external storage"), on_change=self.on_switch_change
        )
        self.external_storage_path_textfield = ft.TextField(
            label=_("External storage path"),
            expand=True,
            expand_loose=True,
            disabled=True,
        )
        self.external_storage_path_pick_button = ft.Button(
            _("Browse..."), on_click=self.pick_external_storage_path, disabled=True
        )
        self.note = ft.Text(
            _(
                "The application will only save files to the specified location if the "
                '"Use external storage" switch is enabled and an external storage path '
                "is set."
            ),
            size=12,
            color=ft.Colors.GREY,
        )

        self.controls = [
            self.use_external_storage_switch,
            ft.Row(
                [
                    self.external_storage_path_textfield,
                    self.external_storage_path_pick_button,
                ]
            ),
            self.note,
        ]

    def did_mount(self) -> None:
        super().did_mount()
        self.page.run_task(self.load_switch_status)

    async def _go_back(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(get_parent_route(self.page.route))

    async def pick_external_storage_path(self, event: ft.Event[ft.Button]):
        storage_path = await ft.FilePicker().get_directory_path()
        if storage_path:
            self.external_storage_path_textfield.value = storage_path
            self.update()

    async def save_button_click(self, event: ft.Event[ft.IconButton]):
        user_pref = cast(UserPreference, AppShared().user_perference)
        user_pref.use_external_storage = self.use_external_storage_switch.value
        user_pref.external_storage_path = self.external_storage_path_textfield.value
        save_user_preference(
            cast(str, AppShared().username),
            user_pref,
        )
        send_success(self.page, _("Settings Saved."))

    async def on_switch_change(self, event: ft.Event[ft.Switch]):
        ph = fph.PermissionHandler()
        if (
            self.use_external_storage_switch.value
            and await ph.get_status(fph.Permission.MANAGE_EXTERNAL_STORAGE)
            != fph.PermissionStatus.GRANTED
        ):
            self.page.show_dialog(ExternalStorageWarningBanner())

        await self.flush_switch()

    async def load_switch_status(self):
        user_pref = cast(UserPreference, AppShared().user_perference)
        self.use_external_storage_switch.value = user_pref.use_external_storage
        self.external_storage_path_textfield.value = user_pref.external_storage_path
        await self.flush_switch()

    async def flush_switch(self):
        is_enabled = self.use_external_storage_switch.value
        self.external_storage_path_textfield.disabled = not is_enabled
        self.external_storage_path_pick_button.disabled = not is_enabled
        self.update()
