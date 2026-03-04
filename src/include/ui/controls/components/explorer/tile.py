from datetime import datetime
from typing import Optional, Callable

import flet as ft
from include.classes.shared import AppShared
from include.util.locale import get_translation
from include.util.userpref import save_user_preference


t = get_translation()
_ = t.gettext


def _notify_favorites_changed(app_shared: AppShared) -> None:
    """Notify the FavoritesValidationService that the favorites list has changed."""
    if app_shared.service_manager:
        from include.classes.services.favorites_validation import (
            FavoritesValidationService,
        )

        service = app_shared.service_manager.get_service("favorites_validation")
        if isinstance(service, FavoritesValidationService):
            service.notify_favorites_changed()


class FileTile(ft.ListTile):
    def __init__(
        self,
        filename: str,
        file_id: str,
        size: Optional[int] = None,
        last_modified: Optional[float] = None,
        starred: bool = False,
        show_id: bool = False,
        selection_mode: bool = False,
        is_selected: bool = False,
        on_selection_changed: Optional[Callable[[str, bool], None]] = None,
        on_click: ft.ControlEventHandler[ft.ListTile] | None = None,
        ref: ft.Ref | None = None,
    ):
        self.page: ft.Page
        self.app_shared = AppShared()
        self.filename = filename
        self.file_id = file_id
        self.starred = starred
        self.selection_mode = selection_mode
        self.is_selected = is_selected
        self.on_selection_changed = on_selection_changed

        self.star_button = ft.IconButton(
            icon=(
                ft.Icons.STAR_BORDER_OUTLINED if not starred else ft.Icons.STAR_OUTLINED
            ),
            on_click=self.on_star_click,
            visible=starred,
        )
        
        # Checkbox for selection mode
        self.checkbox = ft.Checkbox(
            value=is_selected,
            on_change=self.on_checkbox_change,
        )

        subtitle_text = ""
        if show_id:
            subtitle_text += _("ID: {file_id}").format(file_id=file_id)

        if show_id and (last_modified is not None or size is not None):
            subtitle_text += "\n"  # Add extra newline for spacing if ID is shown

        if last_modified is not None:
            subtitle_text += _("Last modified: {last_modified}\n").format(
                last_modified=datetime.fromtimestamp(last_modified).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        if size is not None:
            subtitle_text += f"{size / 1024 / 1024:.3f} MB" if size > 0 else "0 Byte"

        if last_modified is not None and size is not None:
            is_three_line = True
        else:
            is_three_line = False

        # Determine leading control based on selection mode
        if selection_mode:
            leading_control = self.checkbox
        else:
            leading_control = ft.Icon(ft.Icons.FILE_COPY)

        super().__init__(
            leading=leading_control,
            title=filename,
            subtitle=ft.Text(subtitle_text) if subtitle_text else None,
            trailing=self.star_button,
            is_three_line=is_three_line,
            on_click=on_click if not selection_mode else self.on_tile_click_selection_mode,
            align=ft.Alignment.CENTER,
            ref=ref,
        )
    
    async def on_checkbox_change(self, event: ft.Event[ft.Checkbox]):
        """Handle checkbox state change."""
        self.is_selected = bool(event.control.value)
        if self.on_selection_changed:
            self.on_selection_changed(self.file_id, self.is_selected)
    
    async def on_tile_click_selection_mode(self, event: ft.Event[ft.ListTile]):
        """Handle tile click in selection mode - toggle checkbox."""
        self.checkbox.value = not self.checkbox.value
        self.is_selected = self.checkbox.value
        self.checkbox.update()
        if self.on_selection_changed:
            self.on_selection_changed(self.file_id, self.is_selected)

    async def on_star_click(self, event: ft.Event[ft.IconButton]):
        self.starred = not self.starred

        assert self.app_shared.user_perference
        if self.starred:
            # Add to favourites
            self.app_shared.user_perference.favourites["files"][
                self.file_id
            ] = self.filename
        else:
            # Remove from favourites
            try:
                del self.app_shared.user_perference.favourites["files"][self.file_id]
            except KeyError:
                pass

        save_user_preference(
            self.app_shared.get_not_none_attribute("username"),
            self.app_shared.user_perference,
        )

        # Notify listeners that favorites have changed
        _notify_favorites_changed(self.app_shared)

        self.update_state()

    def post_init(self):
        self.update_state()

    def update_state(self):
        if self.starred:
            self.star_button.icon = ft.Icons.STAR_OUTLINED
        else:
            self.star_button.icon = ft.Icons.STAR_BORDER_OUTLINED
        self.update()


class DirectoryTile(ft.ListTile):
    def __init__(
        self,
        dir_name: str,
        directory_id: str,
        created_at: Optional[float] = None,
        starred: bool = False,
        show_id: bool = False,
        selection_mode: bool = False,
        is_selected: bool = False,
        on_selection_changed: Optional[Callable[[str, bool], None]] = None,
        on_click: ft.ControlEventHandler[ft.ListTile] | None = None,
        ref: ft.Ref | None = None,
    ):
        self.page: ft.Page
        self.app_shared = AppShared()
        self.dir_name = dir_name
        self.directory_id = directory_id
        self.starred = starred
        self.selection_mode = selection_mode
        self.is_selected = is_selected
        self.on_selection_changed = on_selection_changed

        self.star_button = ft.IconButton(
            icon=(
                ft.Icons.STAR_BORDER_OUTLINED if not starred else ft.Icons.STAR_OUTLINED
            ),
            on_click=self.on_star_click,
            visible=starred,
        )
        
        # Checkbox for selection mode
        self.checkbox = ft.Checkbox(
            value=is_selected,
            on_change=self.on_checkbox_change,
        )

        subtitle_text = ""
        if show_id:
            subtitle_text += _("ID: {dir_id}").format(dir_id=self.directory_id)

        if show_id and created_at is not None:
            subtitle_text += "\n"  # Add extra newline for spacing if ID is shown

        if created_at is not None:
            subtitle_text += _("Created at: {created_at}").format(
                created_at=datetime.fromtimestamp(created_at).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

        # Determine leading control based on selection mode
        if selection_mode:
            leading_control = self.checkbox
        else:
            leading_control = ft.Icon(ft.Icons.FOLDER)

        super().__init__(
            leading=leading_control,
            title=dir_name,
            subtitle=ft.Text(subtitle_text) if subtitle_text else None,
            trailing=self.star_button,
            on_click=on_click if not selection_mode else self.on_tile_click_selection_mode,
            align=ft.Alignment.CENTER,
            ref=ref,
        )
    
    async def on_checkbox_change(self, event: ft.Event[ft.Checkbox]):
        """Handle checkbox state change."""
        self.is_selected = bool(event.control.value)
        if self.on_selection_changed:
            self.on_selection_changed(self.directory_id, self.is_selected)
    
    async def on_tile_click_selection_mode(self, event: ft.Event[ft.ListTile]):
        """Handle tile click in selection mode - toggle checkbox."""
        self.checkbox.value = not self.checkbox.value
        self.is_selected = self.checkbox.value
        self.checkbox.update()
        if self.on_selection_changed:
            self.on_selection_changed(self.directory_id, self.is_selected)

    async def on_star_click(self, event: ft.Event[ft.IconButton]):
        self.starred = not self.starred

        assert self.app_shared.user_perference
        if self.starred:
            # Add to favourites
            self.app_shared.user_perference.favourites["directories"][
                self.directory_id
            ] = self.dir_name
        else:
            # Remove from favourites
            try:
                del self.app_shared.user_perference.favourites["directories"][
                    self.directory_id
                ]
            except KeyError:
                pass

        save_user_preference(
            self.app_shared.get_not_none_attribute("username"),
            self.app_shared.user_perference,
        )

        # Notify listeners that favorites have changed
        _notify_favorites_changed(self.app_shared)

        self.update_state()

    def post_init(self):
        self.update_state()

    def update_state(self):
        if self.starred:
            self.star_button.icon = ft.Icons.STAR_OUTLINED
        else:
            self.star_button.icon = ft.Icons.STAR_BORDER_OUTLINED
        self.update()
