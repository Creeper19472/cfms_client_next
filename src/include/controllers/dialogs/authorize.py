"""Controller for the authorization dialog."""

from typing import TYPE_CHECKING, Literal

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


class AuthorizeDialogController(BaseController):
    """Controller for handling authorization dialog actions."""

    def __init__(self, control: "AuthorizeDialog") -> None:
        super().__init__(control)
        self.control: AuthorizeDialog

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
                self.control.target_dropdown.options = [
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
                    if search_term.lower() in group.get("group_name", "").lower()
                ]

                # Update dropdown with results
                self.control.target_dropdown.options = [
                    ft.dropdown.Option(
                        key=group["group_name"],
                        text=group["group_name"],
                    )
                    for group in filtered
                ]

            if not self.control.target_dropdown.options:
                self.control.target_search.error = _("No results found")
            else:
                self.control.target_search.error = None
                self.control.target_dropdown.disabled = False

        except Exception as e:
            send_error(
                self.control.page,
                _("Search failed: {error}").format(error=str(e)),
            )

        self.control.enable_interactions()

    async def action_authorize(
        self,
        target_name: str,
        target_type: Literal["user", "group"],
        start_datetime: str,
        end_datetime: str,
    ):
        """Grant authorization to the specified target."""
        try:
            # Prepare data for the request
            data = {
                "target_name": target_name,
                "target_type": target_type,
                "start_time": start_datetime,
                "end_time": end_datetime,
            }

            # Add object-specific data
            if self.control.object_type == "document":
                data["document_id"] = self.control.object_id
                action = "grant_document_access"
            else:  # directory
                data["folder_id"] = self.control.object_id
                action = "grant_directory_access"

            # Make the request
            response = await do_request_2(
                action,
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
                    target=target_name
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
