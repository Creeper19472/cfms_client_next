"""Controller for the view access entries dialog."""

from typing import TYPE_CHECKING

from include.controllers.base import Controller
from include.ui.util.notifications import send_error, send_success
from include.util.requests import do_request_2
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.dialogs.view_access_entries import ViewAccessEntriesDialog

t = get_translation()
_ = t.gettext


class ViewAccessEntriesDialogController(Controller["ViewAccessEntriesDialog"]):
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

    async def action_revoke_access(self, entry_id: int):
        """Revoke an access entry by its ID."""
        try:
            # Prepare data for the request
            data = {
                "entry_id": entry_id,
            }

            # Make the request
            response = await do_request_2(
                "revoke_access",
                data,
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.code != 200:
                send_error(
                    self.control.page,
                    _("Failed to revoke access: ({code}) {message}").format(
                        code=response.code, message=response.message
                    ),
                )
                self.control.enable_interactions()
                return

            # Success - show success message and refresh the table
            send_success(
                self.control.page,
                _("Access entry revoked successfully"),
            )

            # Refresh the access entries list
            await self.action_fetch_access_entries()

        except Exception as e:
            send_error(
                self.control.page,
                _("Failed to revoke access: {error}").format(error=str(e)),
            )
            self.control.enable_interactions()
