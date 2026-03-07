import copy
from typing import TYPE_CHECKING

import flet as ft
from flet_material_symbols import Symbols

from include.ui.controls.dialogs.file_browser import FileBrowserDialog
from include.ui.util.notifications import send_error, send_success
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileListView

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class MoveDialog(FileBrowserDialog):
    """Dialog for moving documents and directories to a different location.

    This dialog extends FileBrowserDialog to provide move-specific functionality,
    including executing the actual move operation after directory selection.
    """

    def __init__(
        self,
        object_type: str,
        object_id: str,
        file_listview: "FileListView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        """Initialize move dialog.

        Args:
            object_type: Type of object to move ("document" or "directory")
            object_id: ID of the object to move
            file_listview: The file list view to refresh after move
            ref: Flet reference
            visible: Whether dialog is visible initially
        """
        self.object_type = object_type
        self.object_id = object_id
        self.file_listview = file_listview
        self.original_parent_id = copy.deepcopy(
            file_listview.parent_manager.current_directory_id
        )

        # Set display name based on object type
        match self.object_type:
            case "document":
                self.object_display_name = _("Document")
            case "directory":
                self.object_display_name = _("Directory")
            case _:
                raise ValueError(f"Invalid object_type: {self.object_type}")

        # Determine exclusions: if moving a directory, exclude it from the tree
        excluded_ids = [object_id] if object_type == "directory" else []

        # Initialize parent with directory browser configuration
        super().__init__(
            title=_("Move {display_name}").format(
                display_name=self.object_display_name
            ),
            on_select_callback=None,  # We'll override the select behavior
            initial_directory_id=file_listview.parent_manager.current_directory_id,
            mode="directories",  # Only show directories
            file_filter=None,
            excluded_directory_ids=excluded_ids,
            show_select_button=True,
            select_button_text=_("Move Here"),
            select_button_icon=Symbols.CHECK_CIRCLE,
            ref=ref,
            visible=visible,
        )

        # Override the select button click to perform move operation
        self.select_here_button.on_click = self.move_here_button_click

        # Update button visibility logic - only show Move Here if different from original
        self._update_move_button_visibility()

    def _update_move_button_visibility(self):
        """Update Move Here button visibility based on current location."""
        # Override parent's enable_interactions to update button visibility
        original_enable = super().enable_interactions

        def custom_enable():
            original_enable()
            # Show Move Here button only if current directory differs from original
            self.select_here_button.visible = (
                self.current_directory_id != self.original_parent_id
            )
            # Go to Root button: visible if not at root
            self.go_to_root_button.visible = self.current_directory_id not in (
                None,
                "/",
            )
            self.update()

        self.enable_interactions = custom_enable

    async def move_here_button_click(self, event: ft.Event[ft.Button]):
        """Execute the move operation to the current directory."""
        yield self.disable_interactions()

        try:
            if self.object_type == "document":
                action = "move_document"
                data = {
                    "document_id": self.object_id,
                    "target_folder_id": self.current_directory_id,
                }
            elif self.object_type == "directory":
                action = "move_directory"
                data = {
                    "folder_id": self.object_id,
                    "target_folder_id": self.current_directory_id,
                }
            else:
                raise ValueError(f"Invalid object_type: {self.object_type}")

            response = await do_request(
                action=action,
                data=data,
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if (code := response["code"]) != 200:
                send_error(
                    self.page,
                    _("Move failed: ({code}) {message}").format(
                        code=code, message=response["message"]
                    ),
                )
                self.enable_interactions()
            else:
                send_success(
                    self.page,
                    _("{display_name} moved successfully").format(
                        display_name=self.object_display_name
                    ),
                )
                # Refresh the file list view
                from include.ui.util.path import get_directory

                await get_directory(
                    self.file_listview.parent_manager.current_directory_id,
                    self.file_listview,
                )
                self.close()

        except Exception as e:
            send_error(
                self.page,
                _("Error moving {display_name}: {error}").format(
                    display_name=self.object_display_name.lower(), error=str(e)
                ),
            )
            self.enable_interactions()
