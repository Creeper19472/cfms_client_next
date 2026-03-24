import flet as ft
from flet_material_symbols import Symbols
from include.classes.shared import AppShared
from include.ui.util.notifications import send_error
from include.util.locale import get_translation
from include.util.requests import do_request_2

t = get_translation()
_ = t.gettext


class LockdownSwitchButton(ft.FloatingActionButton):
    def __init__(self, visible=True):
        self.page: ft.Page
        self._lockdown_active: bool = False
        super().__init__(
            icon=ft.Icon(Symbols.SUPERVISED_USER_CIRCLE_OFF, fill=0),
            on_click=self.on_button_click,
            tooltip=_("Toggle Lockdown Mode"),
            visible=visible,
        )

    @property
    def lockdown_active(self) -> bool:
        return self._lockdown_active

    @lockdown_active.setter
    def lockdown_active(self, value: bool):
        self._lockdown_active = value
        self.icon = ft.Icon(
            Symbols.SUPERVISED_USER_CIRCLE_OFF, fill=int(self._lockdown_active)
        )
        self.update()

    async def on_button_click(self, event: ft.Event[ft.FloatingActionButton]):
        self.lockdown_active = not self.lockdown_active
        self.page.run_task(self.request_lockdown)

    async def request_lockdown(self):
        has_error = False
        try:
            response = await do_request_2(
                action="lockdown",
                data={"status": self.lockdown_active},
                username=AppShared().username,
                token=AppShared().token,
            )

            if response.code != 200:
                has_error = True
            send_error(
                self.page, _("Failed to toggle lockdown mode: ") + response.message
            )
        except Exception as e:
            has_error = True
            send_error(
                self.page,
                _(
                    "Failed to toggle lockdown mode: ({exc_class_name}) {str_err}"
                ).format(exc_class_name=e.__class__.__name__, str_err=str(e)),
            )
            return
        finally:
            if has_error:
                self.lockdown_active = not self.lockdown_active
