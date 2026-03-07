"""Language settings model (declarative)."""

from flet_model import route
from flet_material_symbols import Symbols

from include.ui.frameworks.settings import (
    DeclarativeSettingsPage,
    SettingsField,
    settings_page,
)
from include.util.locale import get_translation, set_translation

t = get_translation()
_ = t.gettext


@settings_page
@route("language_settings")
class LanguageSettingsModel(DeclarativeSettingsPage):
    """Settings page for language / locale selection."""

    # Overview metadata
    settings_name = _("Language")
    settings_description = _("Select your preferred language")
    settings_icon = Symbols.TRANSLATE
    settings_route_suffix = "language_settings"

    # ---------------------------------------------------------------------------
    # Declarative fields
    # ---------------------------------------------------------------------------

    language: SettingsField[str] = SettingsField(
        label=_("Language"),
        key="language",
        hint_text=_("Select your preferred language"),
        options=[
            ("zh_CN", "中文 (Chinese Simplified)"),
            ("en", "English"),
        ],
        default="zh_CN",
        description=_(
            "Select your preferred language for the application interface. "
            "You may need to restart the application for changes to take full effect."
        ),
        expand=True,
    )

    # ---------------------------------------------------------------------------
    # Custom save hook: apply the new translation immediately
    # ---------------------------------------------------------------------------

    async def _on_save(self) -> str | None:
        selected_language = self.language
        if selected_language:
            set_translation(selected_language)
            self._router.clear_cache()
        return _(
            "Language setting saved. Please restart the application for changes to take effect."
        )
