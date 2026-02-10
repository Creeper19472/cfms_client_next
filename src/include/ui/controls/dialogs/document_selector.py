"""Dialog for selecting documents for avatar.

This is now a wrapper around the unified FileBrowserDialog.
"""

from typing import TYPE_CHECKING

import flet as ft

from include.ui.controls.dialogs.file_browser import FileBrowserDialog
from include.util.locale import get_translation

if TYPE_CHECKING:
    pass

t = get_translation()
_ = t.gettext


def is_image_file(filename: str) -> bool:
    """Check if a filename represents an image file based on extension.

    Args:
        filename: The filename to check

    Returns:
        True if the file appears to be an image based on extension
    """
    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[-1].lower()
    return extension in ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg"]


class DocumentSelectorDialog(FileBrowserDialog):
    """Dialog for browsing and selecting image documents for avatar.

    This is a specialized wrapper around FileBrowserDialog configured for
    image document selection.
    """

    def __init__(
        self,
        on_select_callback,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        """Initialize document selector dialog.

        Args:
            on_select_callback: Callback function(document_id, document_name) when document is selected
            ref: Flet reference
            visible: Whether dialog is visible initially
        """

        # Wrap callback to match expected signature (removes item_type parameter)
        def wrapped_callback(item_id, item_name, item_type):
            if on_select_callback:
                on_select_callback(item_id, item_name)

        super().__init__(
            title=_("Select Image Document"),
            on_select_callback=wrapped_callback,
            initial_directory_id=None,
            mode="both",
            file_filter=is_image_file,  # Filter to image files only
            show_select_button=False,  # No directory selection needed
            ref=ref,
            visible=visible,
        )
