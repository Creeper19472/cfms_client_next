"""Controller for the Trash/Recycle Bin view."""

from typing import TYPE_CHECKING

from include.controllers.base import Controller
from include.util.requests import do_request
from include.ui.util.notifications import send_error, send_success

from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.views.trash import TrashView

t = get_translation()
_ = t.gettext


class TrashViewController(Controller["TrashView"]):
    def __init__(self, control: "TrashView") -> None:
        super().__init__(control)

    async def load_deleted_items(self, folder_id: str) -> bool:
        """
        Load deleted items for the given folder_id.

        Args:
            folder_id: The folder to list deleted items from. Use "/" for root.

        Returns:
            True if successful, False otherwise.
        """
        self.control.show_loading()

        response = await do_request(
            action="list_deleted_items",
            data={"folder_id": folder_id},
            username=self.app_shared.username,
            token=self.app_shared.token,
        )

        code = response.get("code")
        if code != 200:
            self.control.hide_loading()
            if code == 403:
                send_error(
                    self.control.page,
                    _("Permission denied: cannot list deleted items."),
                )
            elif code == 404:
                send_error(
                    self.control.page,
                    _("Directory not found."),
                )
            else:
                send_error(
                    self.control.page,
                    _("Failed to list deleted items: ({code}) {message}").format(
                        code=code, message=response.get("message", "")
                    ),
                )
            return False

        data = response.get("data", {})
        folders = data.get("folders", [])
        documents = data.get("documents", [])

        self.control.update_items(folders, documents)
        return True

    async def action_restore_document(
        self,
        document_id: str,
        new_title: str | None = None,
        target_folder_id: str | None = None,
    ):
        """Restore a deleted document."""
        request_data: dict = {"document_id": document_id}
        if new_title is not None:
            request_data["new_title"] = new_title
        if target_folder_id is not None:
            request_data["target_folder_id"] = target_folder_id

        response = await do_request(
            action="restore_document",
            data=request_data,
            username=self.app_shared.username,
            token=self.app_shared.token,
        )

        code = response.get("code")
        if code == 200:
            send_success(
                self.control.page,
                _("Document restored successfully."),
            )
            # Reload the current folder's deleted items
            await self.load_deleted_items(self.control.current_folder_id)
        elif code == 403:
            send_error(
                self.control.page,
                _("Permission denied: cannot restore document."),
            )
        elif code == 404:
            send_error(
                self.control.page,
                _("Deleted document not found."),
            )
        elif code == 409:
            send_error(
                self.control.page,
                _("Cannot restore: a name conflict exists in the destination."),
            )
        else:
            send_error(
                self.control.page,
                _("Failed to restore document: ({code}) {message}").format(
                    code=code, message=response.get("message", "")
                ),
            )

    async def action_restore_directory(
        self,
        folder_id: str,
        new_name: str | None = None,
        target_parent_id: str | None = None,
    ):
        """Restore a deleted directory."""
        request_data: dict = {"folder_id": folder_id}
        if new_name is not None:
            request_data["new_name"] = new_name
        if target_parent_id is not None:
            request_data["target_parent_id"] = target_parent_id

        response = await do_request(
            action="restore_directory",
            data=request_data,
            username=self.app_shared.username,
            token=self.app_shared.token,
        )

        code = response.get("code")
        if code == 200:
            send_success(
                self.control.page,
                _("Directory restored successfully."),
            )
            # Reload the current folder's deleted items
            await self.load_deleted_items(self.control.current_folder_id)
        elif code == 403:
            send_error(
                self.control.page,
                _("Permission denied: cannot restore directory."),
            )
        elif code == 404:
            send_error(
                self.control.page,
                _("Deleted directory not found."),
            )
        elif code == 409:
            send_error(
                self.control.page,
                _("Cannot restore: a name conflict exists in the destination."),
            )
        else:
            send_error(
                self.control.page,
                _("Failed to restore directory: ({code}) {message}").format(
                    code=code, message=response.get("message", "")
                ),
            )

    async def action_purge_document(self, document_id: str):
        """Permanently delete a document."""
        response = await do_request(
            action="purge_document",
            data={"document_id": document_id},
            username=self.app_shared.username,
            token=self.app_shared.token,
        )

        code = response.get("code")
        if code == 200:
            send_success(
                self.control.page,
                _("Document permanently deleted."),
            )
            await self.load_deleted_items(self.control.current_folder_id)
        elif code == 403:
            send_error(
                self.control.page,
                _("Permission denied: cannot permanently delete document."),
            )
        elif code == 404:
            send_error(
                self.control.page,
                _("Deleted document not found."),
            )
        elif code == 400:
            send_error(
                self.control.page,
                _("Document must be marked as deleted before it can be purged."),
            )
        else:
            send_error(
                self.control.page,
                _("Failed to purge document: ({code}) {message}").format(
                    code=code, message=response.get("message", "")
                ),
            )

    async def action_purge_directory(self, folder_id: str):
        """Permanently delete a directory and all its contents."""
        response = await do_request(
            action="purge_directory",
            data={"folder_id": folder_id},
            username=self.app_shared.username,
            token=self.app_shared.token,
        )

        code = response.get("code")
        if code == 200:
            send_success(
                self.control.page,
                _("Directory permanently deleted."),
            )
            await self.load_deleted_items(self.control.current_folder_id)
        elif code == 403:
            send_error(
                self.control.page,
                _("Permission denied: cannot permanently delete directory."),
            )
        elif code == 404:
            send_error(
                self.control.page,
                _("Deleted directory not found."),
            )
        elif code == 400:
            send_error(
                self.control.page,
                _("Directory must be marked as deleted before it can be purged."),
            )
        else:
            send_error(
                self.control.page,
                _("Failed to purge directory: ({code}) {message}").format(
                    code=code, message=response.get("message", "")
                ),
            )
