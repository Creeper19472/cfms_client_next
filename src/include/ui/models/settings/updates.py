"""Update channel settings model (declarative)."""

from flet_model import route
from flet_material_symbols import Symbols

from include.classes.version import ChannelType
from include.constants import DEFAULT_UPDATE_CHANNEL
from include.ui.frameworks.settings import (
    DeclarativeSettingsPage,
    SettingsField,
    settings_page,
)
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


@settings_page
@route("updates_settings")
class UpdatesSettingsModel(DeclarativeSettingsPage):
    """Settings page for update-channel selection."""

    # Overview metadata
    settings_name = _("Updates")
    settings_description = _("Configure update channel preferences")
    settings_icon = Symbols.BROWSER_UPDATED
    settings_route_suffix = "updates_settings"

    # ---------------------------------------------------------------------------
    # Declarative fields
    # ---------------------------------------------------------------------------

    update_channel: SettingsField[str] = SettingsField(
        label=_("Update Channel"),
        key="update_channel",
        hint_text=_("Select the update channel to check for updates"),
        default=DEFAULT_UPDATE_CHANNEL.value,
        options=[
            (ChannelType.STABLE.value, _("Stable - Most stable releases")),
            (ChannelType.BETA.value, _("Beta - Pre-release testing versions")),
            (ChannelType.ALPHA.value, _("Alpha - Cutting edge, frequent updates")),
        ],
        option_descriptions={
            ChannelType.STABLE.value: _(
                "You will receive only stable, thoroughly tested releases."
            ),
            ChannelType.BETA.value: _(
                "You will receive pre-release versions with new features "
                "that are generally stable."
            ),
            ChannelType.ALPHA.value: _(
                "You will receive the latest development versions with "
                "cutting-edge features. Expect frequent updates."
            ),
        },
        expand=True,
    )
