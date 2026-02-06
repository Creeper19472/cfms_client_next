from typing import TYPE_CHECKING, Optional, cast

import flet as ft

from include.constants import FLET_APP_STORAGE_DATA
from include.classes.shared import AppShared
from include.classes.exceptions.request import RequestFailureError
from include.ui.util.notifications import send_error, send_info
from include.util.requests import do_request
from include.classes.services.download import DownloadManagerService

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileListView

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

_app_shared = AppShared()


async def get_directory(
    id: str | None,
    view: "FileListView",
    fallback: Optional[str] = None,
    _raise_on_error=False,
    _set_new_root=False,
) -> bool:
    from include.ui.util.file_controls import update_file_controls

    pm = view.parent_manager
    pm.hide_content()
    view.current_directories_data = []
    view.current_files_data = []

    response = await do_request(
        action="list_directory",
        data={"folder_id": id},
        username=_app_shared.username,
        token=_app_shared.token,
    )

    code = response["code"]
    if code != 200:
        update_file_controls(view, [], [], None)

        if _raise_on_error:
            pm.progress_ring.visible = False
            pm.progress_ring.update()
            view.visible = True
            view.update()
            if fallback is not None:
                await get_directory(fallback, view)
            raise RequestFailureError("Get directory failed", response)

        # Special handling for 403 (Access Denied)
        if code == 403:
            # Show access denied view instead of snackbar
            pm.show_access_denied_view(response["message"])
            return False

        # For other errors, show snackbar
        send_error(
            view.page,
            _("Load failed: ({code}) {message}").format(
                code=code, message=response["message"]
            ),
        )
        pm.show_content()
        return False

    if _set_new_root:
        pm.root_directory_id = id

    pm.current_directory_id = id
    view.current_directories_data = response["data"]["folders"]
    view.current_files_data = response["data"]["documents"]
    view.current_parent_id = response["data"]["parent_id"]

    await pm.sort_bar.controller.apply_sorting()
    pm.show_content()

    return True


async def get_document(id: str | None, filename: str, page: ft.Page):
    """
    Request a document download from the server.

    This function submits the download to the download manager service,
    which will handle the actual download in the background.

    Args:
        id: Document ID to download
        filename: Name of the file
        page: Flet page instance
    """
    response = await do_request(
        action="get_document",
        data={"document_id": id},
        username=_app_shared.username,
        token=_app_shared.token,
    )

    # Handle 403 (Access Denied) with dialog
    if response["code"] == 403:
        from include.ui.controls.dialogs.explorer import AccessDeniedDialog
        
        dialog = AccessDeniedDialog(
            reason=response["message"],
            operation=_("download"),
        )
        page.show_dialog(dialog)
        return

    if response["code"] == 404:
        raise FileNotFoundError("Document not found on server")

    task_data = response["data"]["task_data"]
    task_id = task_data["task_id"]
    task_start_time = task_data["start_time"]
    task_end_time = task_data["end_time"]

    # Check if server supports resume (placeholder logic)
    # This flag would typically be obtained from the server response
    # For now, check if task_data contains a 'supports_resume' key
    supports_resume = task_data.get("supports_resume", False)
    # Future: Server can set this based on its capabilities

    file_path = (
        f"{FLET_APP_STORAGE_DATA}/downloads/{filename if filename else task_id[0:17]}"
    )

    # Get the download manager service
    download_service = None
    if _app_shared.service_manager:
        download_service = cast(
            DownloadManagerService,
            _app_shared.service_manager.get_service("download_manager"),
        )

    if not download_service:
        raise RuntimeError("Download manager service not available")

    # Use download manager service
    download_service.add_task(
        task_id=task_id,
        file_id=id if id else "",
        filename=filename if filename else task_id[0:17],
        file_path=file_path,
        supports_resume=supports_resume,
    )

    # Show notification that download was added
    send_info(
        page,
        _("Download added: {filename}").format(
            filename=filename if filename else task_id[0:17]
        ),
    )
