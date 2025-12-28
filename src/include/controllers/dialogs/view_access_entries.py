"""Controller for the view access entries dialog."""

from typing import TYPE_CHECKING

from include.controllers.base import BaseController
from include.ui.util.notifications import send_error
from include.util.requests import do_request_2
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.dialogs.view_access_entries import ViewAccessEntriesDialog

t = get_translation()
_ = t.gettext


class ViewAccessEntriesDialogController(BaseController["ViewAccessEntriesDialog"]):
    """Controller for handling view access entries dialog actions."""

    def __init__(self, control: "ViewAccessEntriesDialog") -> None:
        super().__init__(control)

    async def action_fetch_access_entries(self):
        """Fetch access entries for the specified object."""
        try:
            # Prepare data for the request
            data = {
                "object_type": self.control.object_type,
                "object_identifier": self.control.object_id,
            }

            # Make the request
            response = await do_request_2(
                "view_access_entries",
                data,
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.code != 200:
                send_error(
                    self.control.page,
                    _("Failed to fetch access entries: ({code}) {message}").format(
                        code=response.code, message=response.message
                    ),
                )
                self.control.enable_interactions()
                return

            # Success - update the table with results
            entries = response.data.get("result", [])
            self.control.update_table(entries)

        except Exception as e:
            send_error(
                self.control.page,
                _("Failed to fetch access entries: {error}").format(error=str(e)),
            )

        self.control.enable_interactions()
