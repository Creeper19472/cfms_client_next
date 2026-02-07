"""Dialog for selecting documents for avatar."""

import asyncio
from typing import TYPE_CHECKING, Optional

import flet as ft

from include.classes.shared import AppShared
from include.ui.controls.dialogs.base import AlertDialog
from include.util.locale import get_translation
from include.util.requests import do_request

if TYPE_CHECKING:
    pass

t = get_translation()
_ = t.gettext


class DocumentSelectorDialog(AlertDialog):
    """Dialog for browsing and selecting image documents for avatar.
    
    Allows users to browse directories and select image documents.
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
        super().__init__(ref=ref, visible=visible)
        
        self.on_select_callback = on_select_callback
        self.app_shared = AppShared()
        
        # Current navigation state
        self.current_directory_id: Optional[str] = None
        self.navigation_stack: list[tuple[Optional[str], str]] = []  # [(dir_id, dir_name)]
        
        self.modal = True
        self.scrollable = True
        self.title = ft.Text(_("Select Image Document"))
        
        # Progress indicator
        self.progress_ring = ft.ProgressRing(visible=True, width=32, height=32)
        
        # Current location indicator
        self.location_text = ft.Text(
            _("Current location: {path}").format(path="/"),
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_400,
        )
        
        # Items list view
        self.items_listview = ft.ListView(
            visible=False,
            expand=True,
            spacing=5,
            padding=10,
        )
        
        # Action buttons
        self.go_to_root_button = ft.TextButton(
            _("Go to Root"),
            icon=ft.Icons.HOME,
            on_click=self.go_to_root_button_click,
            visible=False,
        )
        
        self.cancel_button = ft.TextButton(
            _("Cancel"),
            on_click=self.cancel_button_click,
        )
        
        # Content layout
        self.content = ft.Column(
            controls=[
                self.location_text,
                ft.Divider(),
                self.progress_ring,
                self.items_listview,
            ],
            width=550,
            height=400,
            spacing=10,
        )
        
        self.actions = [
            self.go_to_root_button,
            self.cancel_button,
        ]
    
    def did_mount(self):
        """Called when dialog is mounted to the page. Loads initial directory."""
        super().did_mount()
        asyncio.create_task(self.load_directory(self.current_directory_id))
    
    def disable_interactions(self):
        """Disable user interactions during async operations."""
        self.go_to_root_button.disabled = True
        self.cancel_button.disabled = True
        self.items_listview.visible = False
        self.progress_ring.visible = True
        self.modal = True
        self.update()
    
    def enable_interactions(self):
        """Enable user interactions after async operations complete."""
        self.go_to_root_button.disabled = False
        self.cancel_button.disabled = False
        self.items_listview.visible = True
        self.progress_ring.visible = False
        self.modal = True  # Keep modal during selection
        self.update()
    
    def is_image_file(self, filename: str) -> bool:
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
    
    async def load_directory(self, directory_id: Optional[str]):
        """Load and display contents of a directory.
        
        Args:
            directory_id: ID of directory to load (None for root)
        """
        self.disable_interactions()
        
        try:
            # Request directory contents from server
            response = await do_request(
                action="list_directory",
                data={"folder_id": directory_id},
                username=self.app_shared.username,
                token=self.app_shared.token,
            )
            
            if response.get("code") != 200:
                # Show error in dialog
                self.items_listview.controls = [
                    ft.Text(
                        _("Failed to load directory: {message}").format(
                            message=response.get("message", "Unknown error")
                        ),
                        color=ft.Colors.ERROR,
                    )
                ]
                self.enable_interactions()
                return
            
            data = response.get("data", {})
            directories = data.get("folders", [])  # API returns "folders", not "directories"
            documents = data.get("documents", [])
            
            # Update current directory
            self.current_directory_id = directory_id
            
            # Update location text
            if directory_id is None:
                location = "/"
                self.go_to_root_button.visible = False
            else:
                # Build path from navigation stack
                path_parts = [name for _, name in self.navigation_stack]
                location = "/" + "/".join(path_parts) if path_parts else "/"
                self.go_to_root_button.visible = True
            
            self.location_text.value = _("Current location: {path}").format(path=location)
            
            # Clear and populate items list
            self.items_listview.controls.clear()
            
            # Add parent directory navigation if not at root
            if directory_id is not None and self.navigation_stack:
                parent_button = ft.ListTile(
                    leading=ft.Icon(ft.Icons.FOLDER_OPEN, color=ft.Colors.AMBER_700),
                    title=ft.Text(_(".. (Parent Directory)")),
                    on_click=self.go_to_parent_click,
                )
                self.items_listview.controls.append(parent_button)
            
            # Add subdirectories
            for directory in directories:
                dir_id = directory.get("id")
                dir_name = directory.get("name", "Unnamed")
                
                dir_tile = ft.ListTile(
                    leading=ft.Icon(ft.Icons.FOLDER, color=ft.Colors.BLUE_400),
                    title=ft.Text(dir_name),
                    on_click=lambda e, d_id=dir_id, d_name=dir_name: asyncio.create_task(
                        self.navigate_to_directory(d_id, d_name)
                    ),
                )
                self.items_listview.controls.append(dir_tile)
            
            # Add documents (only image files)
            for document in documents:
                doc_id = document.get("id")
                doc_title = document.get("title", "Unnamed")
                
                # Filter to only show image files based on file extension
                if self.is_image_file(doc_title):
                    doc_tile = ft.ListTile(
                        leading=ft.Icon(ft.Icons.IMAGE, color=ft.Colors.GREEN_400),
                        title=ft.Text(doc_title),
                        subtitle=ft.Text(f"ID: {doc_id}", size=11, color=ft.Colors.GREY_500),
                        on_click=lambda e, d_id=doc_id, d_name=doc_title: self.select_document(
                            d_id, d_name
                        ),
                    )
                    self.items_listview.controls.append(doc_tile)
            
            # Show message if no items
            if not self.items_listview.controls:
                self.items_listview.controls.append(
                    ft.Text(
                        _("No image documents found in this directory"),
                        color=ft.Colors.GREY_500,
                        italic=True,
                    )
                )
            
            self.enable_interactions()
            
        except Exception as e:
            # Show error
            self.items_listview.controls = [
                ft.Text(
                    _("Error loading directory: {error}").format(error=str(e)),
                    color=ft.Colors.ERROR,
                )
            ]
            self.enable_interactions()
    
    async def navigate_to_directory(self, directory_id: str, directory_name: str):
        """Navigate into a subdirectory.
        
        Args:
            directory_id: ID of directory to navigate to
            directory_name: Name of directory for breadcrumb
        """
        # Push current directory to stack
        self.navigation_stack.append((self.current_directory_id, directory_name))
        
        # Load new directory
        await self.load_directory(directory_id)
    
    async def go_to_parent_click(self, event):
        """Navigate to parent directory."""
        if self.navigation_stack:
            # Pop from stack and navigate
            parent_id, _ = self.navigation_stack.pop()
            await self.load_directory(parent_id)
    
    async def go_to_root_button_click(self, event):
        """Navigate to root directory."""
        self.navigation_stack.clear()
        await self.load_directory(None)
    
    def select_document(self, document_id: str, document_name: str):
        """Handle document selection.
        
        Args:
            document_id: ID of selected document
            document_name: Name of selected document
        """
        # Call callback with selected document
        if self.on_select_callback:
            self.on_select_callback(document_id, document_name)
        
        # Close dialog
        self.close()
    
    def cancel_button_click(self, event):
        """Handle cancel button click."""
        self.close()
