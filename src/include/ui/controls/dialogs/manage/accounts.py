from typing import TYPE_CHECKING
import flet as ft
import gettext, asyncio

from include.classes.config import AppConfig
from include.controllers.dialogs.management import (
    AddUserAccountDialogController,
    EditUserGroupDialogController,
    RenameUserNicknameDialogController,
    ViewUserInfoDialogController,
)
from include.controllers.dialogs.passwd import PasswdDialogController
from include.ui.controls.dialogs.base import AlertDialog

if TYPE_CHECKING:
    from include.ui.controls.views.manage.account import ManageAccountsView
    from include.ui.controls.rightmenu.manage.account import UserRightMenuDialog

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class PasswdUserDialog(AlertDialog):
    def __init__(
        self,
        tip: str = "",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.app_config = AppConfig()
        self.controller = PasswdDialogController(self)

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(_("Reset User Password"))

        self.progress_ring = ft.ProgressRing(visible=False)

        self.old_passwd_field = ft.TextField(
            label=_("Old Password"),
            password=True,
            can_reveal_password=True,
            on_submit=lambda e: asyncio.create_task(self.new_passwd_field.focus()),
            expand=True,
        )
        self.new_passwd_field = ft.TextField(
            label=_("New Password"),
            password=True,
            can_reveal_password=True,
            on_submit=self.request_passwd_user,
            expand=True,
        )
        self.tip_text = ft.Text(tip, text_align=ft.TextAlign.CENTER, visible=bool(tip))
        self.submit_button = ft.TextButton("Submit", on_click=self.request_passwd_user)
        self.cancel_button = ft.TextButton("Cancel", on_click=self.cancel_button_click)

        self.content = ft.Column(
            controls=[self.old_passwd_field, self.new_passwd_field, self.tip_text],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
        self.actions = [
            self.progress_ring,
            self.submit_button,
            self.cancel_button,
        ]

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def request_passwd_user(
        self, event: ft.Event[ft.TextButton] | ft.Event[ft.TextField]
    ):
        self.page.run_task(self.controller.action_passwd_user)


class AddUserAccountDialog(AlertDialog):
    def __init__(
        self,
        parent_view: "ManageAccountsView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = AddUserAccountDialogController(self)
        self.parent_view = parent_view
        self.app_config = AppConfig()

        self.modal = False
        self.scrollable = True
        self.title = ft.Text("Create User")

        self.progress_ring = ft.ProgressRing(visible=False)

        self.password_field = ft.TextField(
            label=_("Password"),
            password=True,
            can_reveal_password=True,
            on_submit=self.request_create_user,
            expand=True,
        )
        self.nickname_field = ft.TextField(
            label=_("Nickname"),
            on_submit=lambda _: asyncio.create_task(self.password_field.focus()),
            expand=True,
        )
        self.username_field = ft.TextField(
            label=_("Username"),
            on_submit=lambda _: asyncio.create_task(self.nickname_field.focus()),
            expand=True,
        )

        self.submit_button = ft.TextButton(
            "Create",
            on_click=self.request_create_user,
        )
        self.cancel_button = ft.TextButton("Cancel", on_click=self.cancel_button_click)

        self.content = ft.Column(
            controls=[self.username_field, self.nickname_field, self.password_field],
            # spacing=15,
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        self.actions = [
            self.progress_ring,
            self.submit_button,
            self.cancel_button,
        ]

    def disable_interactions(self):
        self.progress_ring.visible = True
        self.username_field.disabled = True
        self.nickname_field.disabled = True
        self.password_field.disabled = True
        self.submit_button.visible = False
        self.cancel_button.disabled = True
        self.modal = True

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def request_create_user(
        self, event: ft.Event[ft.TextField] | ft.Event[ft.TextButton]
    ):
        yield self.disable_interactions()
        self.page.run_task(self.controller.action_add_user_account)


class RenameUserNicknameDialog(AlertDialog):
    def __init__(
        self,
        parent_dialog: "UserRightMenuDialog",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = RenameUserNicknameDialogController(self)
        self.parent_dialog = parent_dialog
        self.app_config = AppConfig()

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(_("Rename User Nickname"))

        self.progress_ring = ft.ProgressRing(visible=False)

        self.nickname_field = ft.TextField(
            label=_("User's New Nickname"), on_submit=self.request_rename_user, expand=True
        )
        self.submit_button = ft.TextButton(_("Rename"), on_click=self.request_rename_user)
        self.cancel_button = ft.TextButton("Cancel", on_click=self.cancel_button_click)

        self.content = ft.Column(
            controls=[
                self.nickname_field,
            ],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        self.actions = [
            self.progress_ring,
            self.submit_button,
            self.cancel_button,
        ]

    def disable_interactions(self):
        self.nickname_field.disabled = True
        self.submit_button.visible = False
        self.cancel_button.disabled = True
        self.progress_ring.visible = True
        self.modal = True

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def request_rename_user(
        self, event: ft.Event[ft.TextButton] | ft.Event[ft.TextField]
    ):
        self.page.run_task(self.controller.action_rename_user_nickname)


class EditUserGroupDialog(AlertDialog):
    def __init__(
        self,
        parent_dialog: "UserRightMenuDialog",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = EditUserGroupDialogController(self)

        self.refresh_button = ft.IconButton(
            ft.Icons.REFRESH,
            on_click=self.refresh_button_click,
        )
        self.submit_button = ft.TextButton("Submit", on_click=self.submit_button_click)
        self.cancel_button = ft.TextButton("Cancel", on_click=self.cancel_button_click)

        self.modal = False
        self.title = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(_("Change User Group")),
                        self.refresh_button,
                    ]
                ),
            ]
        )

        self.parent_dialog = parent_dialog
        self.app_config = AppConfig()

        self.progress_ring = ft.ProgressRing(visible=False)
        self.group_listview = ft.ListView(expand=True, auto_scroll=True)

        self.content = ft.Column(
            controls=[self.progress_ring, self.group_listview],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            auto_scroll=True,
        )
        self.actions = [
            self.submit_button,
            self.cancel_button,
        ]

    def enable_interactions(self):
        self.group_listview.disabled = False
        self.refresh_button.disabled = False
        self.update()

    def disable_interactions(self):
        self.group_listview.disabled = True
        self.refresh_button.disabled = True
        self.update()

    def did_mount(self):
        super().did_mount()
        assert isinstance(self.page, ft.Page)
        self.page.run_task(self.controller.action_refresh_permission_list)

    async def submit_button_click(self, event: ft.Event[ft.TextButton]):
        self.group_listview.disabled = True
        yield

        # ... "data": {"latest": []}
        # All selected user groups after submitting changes
        to_submit_list = []
        for checkbox in self.group_listview.controls:
            assert isinstance(checkbox, ft.Checkbox)
            if checkbox.value == True:
                to_submit_list.append(checkbox.data)

        self.page.run_task(self.controller.submit_user_group_change, to_submit_list)

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def refresh_button_click(self, event: ft.Event[ft.IconButton]):
        self.page.run_task(self.controller.action_refresh_permission_list)


class ViewUserInfoDialog(AlertDialog):
    def __init__(
        self,
        parent_dialog: "UserRightMenuDialog",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = ViewUserInfoDialogController(self)
        self.parent_dialog = parent_dialog
        self.app_config = AppConfig()

        self.modal = False
        self.scrollable = True

        self.title = ft.Row(
            controls=[
                ft.Text(_("User Details")),
                ft.IconButton(
                    ft.Icons.REFRESH,
                    on_click=self.refresh_button_click,
                ),
            ]
        )

        self.progress_ring = ft.ProgressRing(visible=True)

        self.cancel_button = ft.TextButton("Cancel", on_click=self.cancel_button_click)

        self.info_listview = ft.ListView(visible=False)

        self.content = ft.Column(
            controls=[self.progress_ring, self.info_listview],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [
            self.cancel_button,
        ]

    def did_mount(self):
        super().did_mount()
        self.page.run_task(self.controller.action_refresh_user_info)

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def refresh_button_click(self, event: ft.Event[ft.IconButton]):
        self.page.run_task(self.controller.action_refresh_user_info)
