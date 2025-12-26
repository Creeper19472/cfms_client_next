from typing import TYPE_CHECKING, Optional, cast
import os

import flet as ft

from include.classes.config import AppShared
from include.classes.exceptions.request import RequestFailureError
from include.classes.exceptions.transmission import (
    FileHashMismatchError,
    FileSizeMismatchError,
)
from include.ui.util.notifications import send_error, send_info
from include.util.requests import do_request
from include.util.connect import get_connection
from include.util.transfer import receive_file_from_server
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
):
    from include.ui.util.file_controls import update_file_controls

    view.parent_manager.hide_content()

    response = await do_request(
        action="list_directory",
        data={"folder_id": id},
        username=_app_shared.username,
        token=_app_shared.token,
    )

    if (code := response["code"]) != 200:
        update_file_controls(view, [], [], view.parent_manager.current_directory_id)
        if _raise_on_error:
            view.parent_manager.progress_ring.visible = False
            view.parent_manager.progress_ring.update()
            view.visible = True
            view.update()
            if fallback != None:
                await get_directory(fallback, view)
            raise RequestFailureError("Get directory failed", response)
        send_error(
            view.page,
            _("Load failed: ({code}) {message}").format(
                code=code, message=response["message"]
            ),
        )
    else:
        if _set_new_root:
            view.parent_manager.root_directory_id = id

        view.parent_manager.current_directory_id = id

        view.current_directories_data = response["data"]["folders"]
        view.current_files_data = response["data"]["documents"]
        view.current_parent_id = response["data"]["parent_id"]

        await view.parent_manager.sort_bar.controller.apply_sorting()

        # update_file_controls(
        #     view,
        #     response["data"]["folders"],
        #     response["data"]["documents"],
        #     response["data"]["parent_id"],
        # )

    view.parent_manager.show_content()


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

    assert page.platform
    if page.platform.value in ["android"]:
        file_path = f"/storage/emulated/0/{filename if filename else task_id[0:17]}"
    else:
        file_path = f"./{filename if filename else task_id[0:17]}"

    # Get the download manager service
    download_service = None
    if _app_shared.service_manager:
        download_service = cast(
            DownloadManagerService,
            _app_shared.service_manager.get_service("download_manager"),
        )

    if download_service:
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
    else:
        # Fallback to direct download if service not available
        transfer_conn = await get_connection(
            _app_shared.get_not_none_attribute("server_address"),
            max_size=1024**2 * 4,
            disable_ssl_enforcement=_app_shared.disable_ssl_enforcement,
            proxy=_app_shared.preferences["settings"]["proxy_settings"],
            force_ipv4=_app_shared.preferences["settings"].get("force_ipv4", False),
        )

        # build progress bar

        progress_bar = ft.ProgressBar()
        progress_info = ft.Text(text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE)
        progress_column = ft.Column(
            controls=[progress_bar, progress_info],
            alignment=(
                ft.MainAxisAlignment.START
                if os.name == "nt"
                else ft.MainAxisAlignment.END
            ),
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        page.overlay.append(progress_column)
        page.update()

        try:
            async for stage, *data in receive_file_from_server(
                transfer_conn, task_id=task_id, file_path=file_path
            ):
                match stage:
                    case 0:
                        received_file_size, file_size = data
                        progress_bar.value = received_file_size / file_size
                        progress_info.value = (
                            f"{received_file_size / 1024 / 1024:.2f} MB"
                            f"/{file_size / 1024 / 1024:.2f} MB"
                        )
                    case 1:
                        decrypted_chunks, total_chunks = data
                        progress_bar.value = decrypted_chunks / total_chunks
                        progress_info.value = _(
                            "Decrypting chunk [{decrypted_chunks}/{total_chunks}]"
                        ).format(
                            decrypted_chunks=decrypted_chunks,
                            total_chunks=total_chunks,
                        )
                    case 2:
                        progress_bar.value = None
                        progress_info.value = _("Deleting temporary files")
                    case 3:
                        progress_bar.value = None
                        progress_info.value = _("Verifying file")

                progress_column.update()
        except FileHashMismatchError as exc:
            send_error(page, _("File hash mismatch: {exc}").format(exc=str(exc)))
        except FileSizeMismatchError as exc:
            send_error(page, _("File size mismatch: {exc}").format(exc=str(exc)))
        finally:
            page.overlay.remove(progress_column)
            page.update()
