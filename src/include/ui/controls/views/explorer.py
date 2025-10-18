from typing import Optional
from typing import TYPE_CHECKING
import gettext
import flet as ft

from include.classes.client import LockableClientConnection
from include.classes.config import AppConfig
from include.constants import LOCALE_PATH
from include.controllers.explorer import FileExplorerController
from include.ui.controls.dialogs.explorer import (
    CreateDirectoryDialog,
    OpenDirectoryDialog,
)
from include.ui.util.notifications import send_error
from include.ui.util.file_controls import get_directory

if TYPE_CHECKING:
    from include.ui.models.home import HomeModel

t = gettext.translation("client", LOCALE_PATH, fallback=True)
_ = t.gettext


class FilePathIndicator(ft.Column):
    def __init__(
        self,
        path: Optional[str] = None,
        ref: ft.Ref | None = None,
    ):
        super().__init__(
            ref=ref,
        )
        self.text = ft.Text()
        self.controls = [self.text]
        self.text.value = path if path else "./"
        self.paths: list[str] = []

    def update_path(self):
        self.text.value = "/" + "/".join(self.paths)
        self.update()

    def go(self, path: str):
        self.paths.append(path)
        self.update_path()

    def back(self):
        if self.paths:
            self.paths.pop()
        self.update_path()

    def clear(self):
        self.paths = []
        self.update_path()


class FileListView(ft.ListView):
    def __init__(
        self,
        parent_manager: "FileManagerView",
        ref: ft.Ref | None = None,
        visible=False,
    ):
        super().__init__(ref=ref, visible=visible)
        self.parent: ft.Column
        self.parent_manager = parent_manager
        self.expand = True


class FileManagerView(ft.Container):
    def __init__(self, parent_model, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.parent_model: HomeModel = parent_model
        self.controller = FileExplorerController(self)
        self.app_config = AppConfig()

        self.margin = 10
        self.padding = 10
        self.alignment = ft.Alignment.TOP_CENTER
        self.expand = True

        # View variable definitions
        self.previous_directory_id: str | None = None
        self.current_directory_id: str | None = None
        self.conn: LockableClientConnection

        # Components
        self.indicator = FilePathIndicator("/")
        self.file_listview = FileListView(self)
        self.progress_ring = ft.ProgressRing(visible=False)

        self.content = ft.Column(
            controls=[
                ft.Text(_("File Management"), size=24, weight=ft.FontWeight.BOLD),
                self.indicator,
                ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    ft.Icons.ADD, on_click=self.on_upload_button_click
                                ),
                                ft.IconButton(
                                    ft.Icons.DRIVE_FOLDER_UPLOAD_OUTLINED,
                                    on_click=self.on_upload_directory_button_click,
                                ),
                                ft.IconButton(
                                    ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
                                    on_click=self.on_create_directory_button_click,
                                ),
                                ft.IconButton(
                                    ft.Icons.REFRESH,
                                    on_click=self.on_refresh_button_click,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=10,
                        ),
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    ft.Icons.FOLDER_OPEN_OUTLINED,
                                    on_click=self.on_open_folder_button_click,
                                )
                            ]
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(),
                self.progress_ring,
                # File list, initially hidden until loading is complete
                self.file_listview,
            ],
        )

    def build(self):
        self.conn = self.app_config.get_not_none_attribute("conn")

    def send_error(self, msg: str):
        send_error(self.page, msg)

    async def on_upload_button_click(self, event: ft.Event[ft.IconButton]):
        files = await self.parent_model.file_picker.pick_files(allow_multiple=True)
        if not files:
            return

        self.page.run_task(self.controller.action_upload, files)

    async def on_upload_directory_button_click(self, event: ft.Event[ft.IconButton]):
        root_path = await self.parent_model.file_picker.get_directory_path()
        if not root_path:
            return
        
        self.page.run_task(self.controller.action_directory_upload, root_path)

    async def on_create_directory_button_click(self, event: ft.Event[ft.IconButton]):
        create_directory_dialog = CreateDirectoryDialog(self)
        self.page.show_dialog(create_directory_dialog)

    async def on_refresh_button_click(self, event: ft.Event[ft.IconButton]):
        await get_directory(
            id=self.current_directory_id,
            view=self.file_listview,
        )

    async def on_open_folder_button_click(self, event: ft.Event[ft.IconButton]):
        self.page.show_dialog(OpenDirectoryDialog(self))
