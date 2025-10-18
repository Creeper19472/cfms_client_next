import flet as ft
import json, gettext
from include.classes.config import AppConfig
from include.constants import LOCALE_PATH
from include.util.requests import do_request
from include.ui.util.notifications import send_error

t = gettext.translation("client", LOCALE_PATH, fallback=True)
_ = t.gettext


class DevRequestDialog(ft.AlertDialog):
    def __init__(
        self,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(
            ref=ref,
            visible=visible
        )
        self.app_config = AppConfig()
        self.req_name = ft.TextField(label=_("Request Name"), expand=True)
        self.req_data = ft.TextField(label=_("Request Data"), expand=True)
        self.result = ft.TextField(
            label=_("Result"), read_only=True, multiline=True, min_lines=5, expand=True
        )
        self.content = ft.Column(
            [
                self.req_name,
                self.req_data,
                self.result,
            ],
            width=720,
        )
        self.actions = [
            ft.TextButton(_("Submit"), on_click=self.on_submit_button_clicked),
            ft.TextButton(_("Cancel"), on_click=self.cancel_button_click),
        ]
        self.scrollable = True

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.open = False
        self.update()

    async def on_submit_button_clicked(self, event: ft.Event[ft.TextButton]):
        assert self.page
        request_name: str | None = self.req_name.value
        text_data: str | None = self.req_data.value

        if not request_name:
            send_error(self.page, _("Request name must be specified"))
            return

        if text_data:
            try:
                data_to_send = json.loads(text_data)
            except json.JSONDecodeError as e:
                send_error(self.page, str(e))
                return
        else:
            data_to_send = {}

        resp = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            request_name,
            data_to_send,
            username=self.app_config.username,
            token=self.app_config.token,
        )
        self.result.value = json.dumps(resp)
        self.update()
