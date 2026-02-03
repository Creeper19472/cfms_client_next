from datetime import datetime
from typing import Optional

import flet as ft
from include.classes.shared import AppShared
from include.util.locale import get_translation
from include.util.userpref import save_user_preference


t = get_translation()
_ = t.gettext


class FileTile(ft.ListTile):
    def __init__(
        self,
        filename: str,
        file_id: str,
        size: Optional[int] = None,
        last_modified: Optional[float] = None,
        starred: bool = False,
        show_id: bool = False,
        on_click: ft.ControlEventHandler[ft.ListTile] | None = None,
        ref: ft.Ref | None = None,
    ):
        self.page: ft.Page
        self.app_shared = AppShared()
        self.filename = filename
        self.file_id = file_id
        self.starred = starred

        self.star_button = ft.IconButton(
            icon=(
                ft.Icons.STAR_BORDER_OUTLINED if not starred else ft.Icons.STAR_OUTLINED
            ),
            on_click=self.on_star_click,
            visible=starred,
        )

        subtitle_text = ""
        if show_id:
            subtitle_text += _("ID: {file_id}\n").format(file_id=file_id)

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

        super().__init__(
            leading=ft.Icon(ft.Icons.FILE_COPY),
            title=filename,
            subtitle=ft.Text(subtitle_text) if subtitle_text else None,
            trailing=self.star_button,
            is_three_line=is_three_line,
            on_click=on_click,
            align=ft.Alignment.CENTER,
            ref=ref,
        )

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
        on_click: ft.ControlEventHandler[ft.ListTile] | None = None,
        ref: ft.Ref | None = None,
    ):
        self.page: ft.Page
        self.app_shared = AppShared()
        self.dir_name = dir_name
        self.directory_id = directory_id
        self.starred = starred

        self.star_button = ft.IconButton(
            icon=(
                ft.Icons.STAR_BORDER_OUTLINED if not starred else ft.Icons.STAR_OUTLINED
            ),
            on_click=self.on_star_click,
            visible=starred,
        )

        subtitle_text = ""
        if show_id:
            subtitle_text += _("ID: {dir_id}\n").format(dir_id=self.directory_id)

        if created_at is not None:
            subtitle_text += _("Created at: {created_at}").format(
                created_at=datetime.fromtimestamp(created_at).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

        super().__init__(
            leading=ft.Icon(ft.Icons.FOLDER),
            title=dir_name,
            subtitle=ft.Text(subtitle_text) if subtitle_text else None,
            trailing=self.star_button,
            on_click=on_click,
            align=ft.Alignment.CENTER,
            ref=ref,
        )

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

        self.update_state()

    def post_init(self):
        self.update_state()

    def update_state(self):
        if self.starred:
            self.star_button.icon = ft.Icons.STAR_OUTLINED
        else:
            self.star_button.icon = ft.Icons.STAR_BORDER_OUTLINED
        self.update()
