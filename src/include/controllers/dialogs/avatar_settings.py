"""Controller for avatar settings dialog."""

import logging
from typing import TYPE_CHECKING

from include.controllers.base import Controller
from include.util.avatar import set_user_avatar, download_avatar_file
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.dialogs.avatar_settings import AvatarSettingsDialog

t = get_translation()
_ = t.gettext

logger = logging.getLogger(__name__)


class AvatarSettingsDialogController(Controller["AvatarSettingsDialog"]):
    """Controller for handling avatar settings operations."""

    def __init__(self, control: "AvatarSettingsDialog"):
        super().__init__(control)

    async def action_set_avatar(self, document_id: str):
        """
        Set the user's avatar to the specified document ID.

        Args:
            document_id: The document ID of the image to use as avatar
        """
        try:
            username = self.app_shared.get_not_none_attribute("username")

            # Call the avatar API to set the avatar
            success = await set_user_avatar(username, document_id)

            if success:
                # Update AppShared with new avatar ID
                self.app_shared.avatar_id = document_id

                # Download the avatar file
                avatar_path = await download_avatar_file(document_id, username)

                if avatar_path:
                    # Update AppShared with avatar path
                    self.app_shared.avatar_path = avatar_path

                    # Refresh the AccountBadge to show new avatar
                    self.control.account_badge.update_avatar_display()
                    self.control.account_badge.update()

                    # Close the dialog
                    self.control.close()
                else:
                    # Avatar was set on server but download failed
                    self.control.show_error(
                        _("Avatar set successfully, but failed to download. Please try again.")
                    )
                    self.control.enable_interactions()
            else:
                # Failed to set avatar on server
                self.control.show_error(
                    _("Failed to set avatar. Please check the document ID and try again.")
                )
                self.control.enable_interactions()

        except Exception as e:
            # Log the full exception for debugging
            logger.exception("Error setting avatar: %s", e)

            # Show a generic error message to the user
            self.control.show_error(
                _("An error occurred while setting the avatar. Please try again.")
            )
            self.control.enable_interactions()
