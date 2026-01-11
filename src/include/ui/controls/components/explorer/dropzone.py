from typing import TYPE_CHECKING
import flet as ft

from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileManagerView

t = get_translation()
_ = t.gettext


async def trigger_file_upload(parent_view: "FileManagerView", event):
    """
    Common helper function to trigger file upload via file picker.
    
    Args:
        parent_view: The FileManagerView instance containing the file picker and upload controller
        event: The event that triggered the upload (unused but kept for handler compatibility)
    """
    files = await parent_view.parent_model.file_picker.pick_files(
        allow_multiple=True
    )
    if files:
        # Trigger upload task on the page
        parent_view.page.run_task(parent_view.controller.action_upload, files)


class FileUploadDropZone(ft.Container):
    """
    A visual drag-and-drop zone for file uploads.
    
    Note: This provides a visual interface that mimics drag-and-drop behavior.
    When clicked, it triggers the file picker for file selection.
    """
    
    def __init__(
        self,
        parent_view: "FileManagerView",
        ref: ft.Ref | None = None,
    ):
        super().__init__(ref=ref)
        self.parent_view = parent_view
        
        # Visual styling for the drop zone
        self.border = ft.border.all(2, ft.Colors.BLUE_400)
        self.border_radius = 10
        self.padding = 20
        self.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.BLUE_400)
        self.alignment = ft.alignment.center
        
        # Content
        self.content = ft.Column(
            controls=[
                ft.Icon(
                    ft.Icons.CLOUD_UPLOAD_OUTLINED,
                    size=48,
                    color=ft.Colors.BLUE_400,
                ),
                ft.Text(
                    _("Click to select files or drag and drop here"),
                    size=16,
                    color=ft.Colors.BLUE_400,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    _("Upload files to current directory"),
                    size=12,
                    color=ft.Colors.with_opacity(0.7, ft.Colors.BLUE_400),
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )
        
        # Make it clickable
        self.on_click = self.handle_click
        self.on_hover = self.handle_hover
    
    async def handle_click(self, event: ft.Event[ft.Container]):
        """Handle click to open file picker and trigger upload."""
        await trigger_file_upload(self.parent_view, event)
    
    async def handle_hover(self, event: ft.Event[ft.Container]):
        """Handle hover to provide visual feedback."""
        if event.data == "true":
            # Mouse entered
            self.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.BLUE_400)
            self.border = ft.border.all(2, ft.Colors.BLUE_600)
        else:
            # Mouse exited
            self.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.BLUE_400)
            self.border = ft.border.all(2, ft.Colors.BLUE_400)
        self.update()


class FileUploadDragTarget(ft.DragTarget):
    """
    An alternative drag-and-drop zone using Flet's DragTarget.
    
    Note: This is for internal Flet UI dragging only. It cannot accept
    files dropped from the operating system. It's included for demonstration
    of Flet's drag-and-drop capabilities within the app.
    """
    
    def __init__(
        self,
        parent_view: "FileManagerView",
        ref: ft.Ref | None = None,
    ):
        self.parent_view = parent_view
        
        # Create the drop zone content
        drop_zone_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.CLOUD_UPLOAD_OUTLINED,
                        size=48,
                        color=ft.Colors.BLUE_400,
                    ),
                    ft.Text(
                        _("Drop files here to upload"),
                        size=16,
                        color=ft.Colors.BLUE_400,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        _("(Click to select files)"),
                        size=12,
                        color=ft.Colors.with_opacity(0.7, ft.Colors.BLUE_400),
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            border=ft.border.all(2, ft.Colors.BLUE_400),
            border_radius=10,
            padding=20,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_400),
            alignment=ft.alignment.center,
            on_click=self.handle_click,
        )
        
        super().__init__(
            ref=ref,
            content=drop_zone_content,
            group="file_upload",
            on_will_accept=self.handle_will_accept,
            on_accept=self.handle_accept,
            on_leave=self.handle_leave,
        )
    
    async def handle_click(self, event: ft.Event[ft.Container]):
        """Handle click to open file picker and trigger upload."""
        await trigger_file_upload(self.parent_view, event)
    
    async def handle_will_accept(self, event: ft.Event[ft.DragTarget]):
        """Handle when a draggable enters the target."""
        # Change visual feedback
        self.content.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.BLUE_600)
        self.content.border = ft.border.all(2, ft.Colors.BLUE_600)
        self.update()
    
    async def handle_accept(self, event: ft.Event[ft.DragTarget]):
        """Handle when a draggable is dropped on the target."""
        # Reset visual feedback
        self.content.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.BLUE_400)
        self.content.border = ft.border.all(2, ft.Colors.BLUE_400)
        self.update()
        
        # Note: This won't receive OS file drops, only internal Flet Draggable components
        # For actual file uploads, users should click to open the file picker
    
    async def handle_leave(self, event: ft.Event[ft.DragTarget]):
        """Handle when a draggable leaves the target."""
        # Reset visual feedback
        self.content.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.BLUE_400)
        self.content.border = ft.border.all(2, ft.Colors.BLUE_400)
        self.update()
