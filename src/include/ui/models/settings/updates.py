from flet_model import Model, Router, route
import flet as ft

from include.classes.shared import AppShared
from include.classes.version import ChannelType
from include.constants import DEFAULT_UPDATE_CHANNEL
from include.ui.util.notifications import send_success
from include.ui.util.route import get_parent_route
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


@route("updates_settings")
class UpdatesSettingsModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)

        self.appbar = ft.AppBar(
            title=ft.Text(_("Updates")),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self._go_back),
            actions=[
                ft.IconButton(ft.Icons.SAVE_OUTLINED, on_click=self.save_button_on_click)
            ],
            actions_padding=10,
        )
        self.app_shared = AppShared()

        self.channel_dropdown = ft.Dropdown(
            label=_("Update Channel"),
            hint_text=_("Select the update channel to check for updates"),
            options=[
                ft.dropdown.Option(
                    key=ChannelType.STABLE.value,
                    text=_("Stable - Most stable releases"),
                ),
                ft.dropdown.Option(
                    key=ChannelType.BETA.value,
                    text=_("Beta - Pre-release testing versions"),
                ),
                ft.dropdown.Option(
                    key=ChannelType.ALPHA.value,
                    text=_("Alpha - Cutting edge, frequent updates"),
                ),
            ],
            expand=True,
            expand_loose=True,
            border_color=ft.Colors.WHITE_54,
            on_select=self.channel_dropdown_on_select,
        )

        self.channel_description = ft.Text(
            "",
            size=14,
            color=ft.Colors.GREY,
            expand=True,
            expand_loose=True,
            margin=ft.Margin(top=-5),
        )

        self.controls = [
            self.channel_dropdown,
            self.channel_description,
        ]

    def did_mount(self) -> None:
        super().did_mount()
        self.page.run_task(self.load_settings)

    async def _go_back(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(get_parent_route(self.page.route))

    async def save_button_on_click(self, event: ft.Event[ft.IconButton]):
        # Save the selected channel to preferences
        selected_channel = self.channel_dropdown.value
        if selected_channel:
            self.app_shared.preferences["settings"]["update_channel"] = selected_channel
            self.app_shared.dump_preferences()
            send_success(self.page, _("Settings Saved."))

    async def channel_dropdown_on_select(self, event: ft.Event[ft.Dropdown]):
        # Update description when user changes selection
        if event.control.value:
            self.update_channel_description(event.control.value)
            self.update()

    async def load_settings(self):
        # Load the current channel setting
        current_channel = self.app_shared.preferences.get("settings", {}).get(
            "update_channel", DEFAULT_UPDATE_CHANNEL.value
        )
        self.channel_dropdown.value = current_channel
        self.update_channel_description(current_channel)
        self.update()

    def update_channel_description(self, channel: str):
        """Update the description text based on selected channel."""
        descriptions = {
            ChannelType.STABLE.value: _(
                "You will receive only stable, thoroughly tested releases."
            ),
            ChannelType.BETA.value: _(
                "You will receive pre-release versions with new features that are generally stable."
            ),
            ChannelType.ALPHA.value: _(
                "You will receive the latest development versions with cutting-edge features. Expect frequent updates."
            ),
        }
        self.channel_description.value = descriptions.get(
            channel, _("Select a channel to see its description")
        )
