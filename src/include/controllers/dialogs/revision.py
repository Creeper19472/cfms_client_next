"""Controller for the revision dialog."""

from typing import TYPE_CHECKING

from include.controllers.base import BaseController
from include.ui.controls.dialogs.wait import wait
from include.util.requests import do_request_2
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.dialogs.revision import RevisionDialog

t = get_translation()
_ = t.gettext


class RevisionDialogController(BaseController["RevisionDialog"]):
    """Controller for handling revision operations."""

    def __init__(self, control: "RevisionDialog"):
        super().__init__(control)

    async def action_load_revisions(self):
        """Load and display revisions for the document."""
        self.control.show_loading()

        try:
            # Request revisions from the server
            response = await do_request_2(
                action="list_revisions",
                data={"document_id": self.control.document_id},
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.code == 200:
                revisions = response.data.get("revisions", [])
                self.control.display_revisions(revisions)
            else:
                self.control.show_error(
                    _("Failed to load revisions: ({code}) {message}").format(
                        code=response.code,
                        message=response.message,
                    )
                )
        except Exception as e:
            self.control.show_error(
                _("Failed to load revisions: {error}").format(error=str(e))
            )

    async def action_view_revision(self, revision_id: int, is_current: bool):
        """View/download a specific revision."""
        try:
            # Request the revision data
            response = await do_request_2(
                action="get_revision",
                data={"id": revision_id},
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.code == 200:
                task_data = response.data.get("task_data")
                if task_data:
                    # Download the revision file using the download manager
                    from include.classes.services.download import DownloadManagerService
                    from include.constants import FLET_APP_STORAGE_DATA
                    from include.ui.util.notifications import send_info
                    from typing import cast
                    
                    task_id = task_data["task_id"]
                    
                    if not is_current:
                        filename = f"rev{revision_id}_{self.control.filename}"
                    else:
                        filename = self.control.filename

                    file_path = f"{FLET_APP_STORAGE_DATA}/downloads/{filename}"
                    supports_resume = task_data.get("supports_resume", False)
                    
                    # Get the download manager service
                    download_service = None
                    if self.app_shared.service_manager:
                        download_service = cast(
                            DownloadManagerService,
                            self.app_shared.service_manager.get_service("download_manager"),
                        )
                    
                    if download_service:
                        download_service.add_task(
                            task_id=task_id,
                            file_id=str(revision_id),
                            filename=filename,
                            file_path=file_path,
                            supports_resume=supports_resume,
                        )
                        send_info(
                            self.control.page,
                            _("Download added: {filename}").format(filename=filename),
                        )
                    else:
                        self.control.send_error(_("Download manager service not available"))
                else:
                    self.control.send_error(
                        _("Failed to get revision data: No task data returned")
                    )
            else:
                self.control.send_error(
                    _("Failed to view revision: ({code}) {message}").format(
                        code=response.code,
                        message=response.message,
                    )
                )
        except Exception as e:
            self.control.send_error(
                _("Failed to view revision: {error}").format(error=str(e))
            )

    @wait("set_current_revision")
    async def action_set_current_revision(self, revision_id: int):
        """Set a revision as the current revision."""
        try:
            response = await do_request_2(
                action="set_current_revision",
                data={
                    "document_id": self.control.document_id,
                    "revision_id": revision_id,
                },
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.code == 200:
                # Reload revisions to show updated status
                await self.action_load_revisions()
                
                # Optionally refresh the file listview to show the updated document
                from include.ui.util.path import get_directory
                await get_directory(
                    id=self.control.parent_listview.parent_manager.current_directory_id,
                    view=self.control.parent_listview,
                )
            else:
                self.control.send_error(
                    _("Failed to set current revision: ({code}) {message}").format(
                        code=response.code,
                        message=response.message,
                    )
                )
        except Exception as e:
            self.control.send_error(
                _("Failed to set current revision: {error}").format(error=str(e))
            )

    @wait("delete_revision")
    async def action_delete_revision(self, revision_id: int):
        """Delete a specific revision."""
        try:
            response = await do_request_2(
                action="delete_revision",
                data={"id": revision_id},
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.code == 200:
                # Reload revisions to show updated list
                await self.action_load_revisions()
            else:
                self.control.send_error(
                    _("Failed to delete revision: ({code}) {message}").format(
                        code=response.code,
                        message=response.message,
                    )
                )
        except Exception as e:
            self.control.send_error(
                _("Failed to delete revision: {error}").format(error=str(e))
            )
