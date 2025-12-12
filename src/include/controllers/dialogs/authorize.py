"""Controller for the authorization dialog."""

from typing import TYPE_CHECKING, Literal, Union

import flet as ft

from include.controllers.base import BaseController
from include.ui.util.notifications import send_error, send_success
from include.ui.util.path import get_directory
from include.util.requests import do_request_2
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.dialogs.authorize import AuthorizeDialog

t = get_translation()
_ = t.gettext


class AuthorizeDialogController(BaseController["AuthorizeDialog"]):
    """Controller for handling authorization dialog actions."""

    def __init__(self, control: "AuthorizeDialog") -> None:
        super().__init__(control)

    async def action_search_targets(
        self, search_term: str, target_type: Literal["user", "group"]
    ):
        """Search for users or groups based on the search term."""
        try:
            if target_type == "user":
                # Search for users
                response = await do_request_2(
                    "list_users",
                    {},
                    username=self.app_config.username,
                    token=self.app_config.token,
                )

                if response.code != 200:
                    send_error(
                        self.control.page,
                        _("Failed to fetch users: ({code}) {message}").format(
                            code=response.code, message=response.message
                        ),
                    )
                    self.control.enable_interactions()
                    return

                users_data = response.data.get("users", [])
                # Filter users based on search term
                filtered = [
                    user
                    for user in users_data
                    if search_term.lower() in user.get("username", "").lower()
                    or search_term.lower() in user.get("nickname", "").lower()
                ]

                # Update dropdown with results
                self.control.entity_dropdown.options = [
                    ft.dropdown.Option(
                        key=user["username"],
                        text=f"{user['username']} ({user.get('nickname', '')})",
                    )
                    for user in filtered
                ]

            else:  # target_type == "group"
                # Search for groups
                response = await do_request_2(
                    "list_groups",
                    {},
                    username=self.app_config.username,
                    token=self.app_config.token,
                )

                if response.code != 200:
                    send_error(
                        self.control.page,
                        _("Failed to fetch groups: ({code}) {message}").format(
                            code=response.code, message=response.message
                        ),
                    )
                    self.control.enable_interactions()
                    return

                groups_data = response.data.get("groups", [])
                # Filter groups based on search term
                filtered = [
                    group
                    for group in groups_data
                    if search_term.lower() in group.get("name", "").lower()
                ]

                # Update dropdown with results
                self.control.entity_dropdown.options = [
                    ft.dropdown.Option(
                        key=group["name"],
                        text=f"{group['name']} ({group.get('display_name') or group['name']})",
                    )
                    for group in filtered
                ]

            if not self.control.entity_dropdown.options:
                self.control.entity_search.error = _("No results found")
            else:
                self.control.entity_search.error = None
                self.control.entity_dropdown.disabled = False

        except Exception as e:
            send_error(
                self.control.page,
                _("Search failed: {error}").format(error=str(e)),
            )

        self.control.enable_interactions()

    async def action_authorize(
        self,
        entity_name: str,
        entity_type: Literal["user", "group"],
        start_time: Union[int, float],
        end_time: Union[int, float],
    ):
        """Grant authorization to the specified target."""
        try:
            # Prepare data for the request
            data = {
                "entity_identifier": entity_name,
                "entity_type": entity_type,
                "target_type": self.control.object_type,
                "target_identifier": self.control.object_id,
                "access_types": self.control.access_types_row.selected,
                "start_time": start_time,
                "end_time": end_time,
            }

            # Make the request
            response = await do_request_2(
                "grant_access",
                data,
                username=self.app_config.username,
                token=self.app_config.token,
            )

            if response.code != 200:
                send_error(
                    self.control.page,
                    _("Authorization failed: ({code}) {message}").format(
                        code=response.code, message=response.message
                    ),
                )
                self.control.enable_interactions()
                return

            # Success
            send_success(
                self.control.page,
                _("Access authorized successfully for {target}").format(
                    target=entity_name
                ),
            )

            # Refresh the file list
            await get_directory(
                self.control.parent_listview.parent_manager.current_directory_id,
                self.control.parent_listview,
            )

            # Close the dialog
            self.control.close()

        except Exception as e:
            send_error(
                self.control.page,
                _("Authorization failed: {error}").format(error=str(e)),
            )
            self.control.enable_interactions()
