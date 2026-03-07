from typing import TYPE_CHECKING, Optional
import asyncio

import flet as ft
from flet_material_symbols import Symbols

from include.classes.shared import AppShared
from include.ui.controls.dialogs.base import AlertDialog
from include.ui.util.notifications import send_error
from include.util.locale import get_translation
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.views.admin.group import ManageGroupsView

t = get_translation()
_ = t.gettext


class AddUserGroupDialog(AlertDialog):
    def __init__(
        self,
        parent_view: "ManageGroupsView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.parent_view = parent_view
        self.app_shared = AppShared()

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(_("Create User"))

        self.progress_ring = ft.ProgressRing(visible=False)

        self.display_name_field = ft.TextField(
            label=_("Display Name"), on_submit=self.request_create_group, expand=True
        )
        self.group_name_field = ft.TextField(
            label=_("User Group Name"),
            on_submit=lambda _: asyncio.create_task(self.display_name_field.focus()),
            expand=True,
        )

        self.submit_button = ft.TextButton(
            _("Create"),
            on_click=self.request_create_group,
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

        self.content = ft.Column(
            controls=[self.display_name_field, self.group_name_field],
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
        self.display_name_field.disabled = True
        self.group_name_field.disabled = True
        self.submit_button.visible = False
        self.cancel_button.disabled = True
        self.modal = True

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def request_create_group(
        self, event: ft.Event[ft.TextField] | ft.Event[ft.TextButton]
    ):

        yield self.disable_interactions()

        response = await do_request(
            action="create_group",
            data={
                "group_name": self.group_name_field.value,
                "display_name": self.display_name_field.value,
                "permissions": [],  # TODO
            },
            username=self.app_shared.username,
            token=self.app_shared.token,
        )
        if (code := response["code"]) != 200:
            send_error(
                self.page,
                _("Failed to create user group: ({code}) {message}").format(
                    code=code, message=response["message"]
                ),
            )
        else:
            await self.parent_view.refresh_group_list()

        self.close()


class RenameGroupDialog(AlertDialog):
    def __init__(
        self,
        group_name: str,
        parent_manager: "ManageGroupsView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = False
        self.title = ft.Text(_("Rename User Group"))

        self.group_name = group_name
        self.parent_manager = parent_manager
        self.app_shared = AppShared()

        self.progress_ring = ft.ProgressRing(visible=False)
        self.name_textfield = ft.TextField(
            label=_("New User Group Name"),
            on_submit=self.ok_button_click,
            expand=True,
        )
        self.textfield_empty_message = ft.Text(
            _("Group name cannot be empty"), color=ft.Colors.RED, visible=False
        )

        self.submit_button = ft.TextButton(
            _("Submit"),
            on_click=self.ok_button_click,
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

        self.content = ft.Column(
            controls=[self.name_textfield, self.textfield_empty_message],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.progress_ring, self.submit_button, self.cancel_button]

    def disable_interactions(self):
        self.name_textfield.disabled = True
        self.cancel_button.disabled = True
        self.submit_button.visible = False
        self.progress_ring.visible = True
        self.textfield_empty_message.visible = False
        self.name_textfield.border_color = None
        self.modal = False

    def enable_interactions(self):
        self.name_textfield.disabled = False
        self.cancel_button.disabled = False
        self.submit_button.visible = True
        self.progress_ring.visible = False
        self.modal = True

    async def ok_button_click(
        self, event: ft.Event[ft.TextButton] | ft.Event[ft.TextField]
    ):
        yield self.disable_interactions()

        if not (new_display_name := self.name_textfield.value):
            self.name_textfield.border_color = ft.Colors.RED
            self.textfield_empty_message.visible = True
            yield self.enable_interactions()
            return

        response = await do_request(
            action="rename_group",
            data={
                "group_name": self.group_name,
                "display_name": new_display_name,
            },
            username=self.app_shared.username,
            token=self.app_shared.token,
        )

        if (code := response["code"]) != 200:
            send_error(
                self.page,
                _("Rename failed: ({code}) {message}").format(
                    code=code, message=response["message"]
                ),
            )
        else:
            await self.parent_manager.refresh_group_list()

        self.close()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()


class EditGroupPermissionDialog(AlertDialog):
    def __init__(
        self,
        group_name: str,
        parent_manager: "ManageGroupsView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.refresh_button = ft.IconButton(
            Symbols.REFRESH,
            on_click=self.refresh_button_click,
        )
        self.add_button = ft.IconButton(
            Symbols.ADD, on_click=self.add_permission_submit, disabled=True
        )
        self.submit_button = ft.TextButton(
            _("Submit"), on_click=self.submit_button_click
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

        self.add_textfield = ft.TextField(
            label=_("Add Permission"),
            on_submit=self.add_permission_submit,
            on_change=self.add_textfield_on_change,
            expand=True,
        )

        self.modal = False
        self.title = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(_("Change User Group Permissions")),
                        self.refresh_button,
                    ]
                ),
                ft.Row(controls=[self.add_button, self.add_textfield]),
            ]
        )

        self.group_name = group_name
        self.parent_manager = parent_manager
        self.app_shared = AppShared()

        self.progress_ring = ft.ProgressRing(visible=False)
        self.permission_listview = ft.ListView(expand=True, auto_scroll=True)

        self.content = ft.Column(
            controls=[self.progress_ring, self.permission_listview],
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

    def did_mount(self):
        super().did_mount()
        assert isinstance(self.page, ft.Page)
        self.page.run_task(self.refresh_permission_list)

    async def add_permission_submit(
        self, event: ft.Event[ft.TextField] | ft.Event[ft.IconButton]
    ):
        if not self.add_textfield.value:
            return

        if self.add_textfield.value not in [
            control.data for control in self.permission_listview.controls
        ]:
            self.permission_listview.controls.append(
                ft.Checkbox(
                    label=self.add_textfield.value,
                    data=self.add_textfield.value,
                    on_change=None,  # Do nothing before submission
                    value=True,  # Selected by default
                )
            )

        self.add_textfield.value = ""
        yield
        await self.add_textfield_on_change()

    async def add_textfield_on_change(
        self, event: Optional[ft.Event[ft.TextField]] = None
    ):
        self.add_button.disabled = not self.add_textfield.value
        self.update()

    async def submit_button_click(self, event: ft.Event[ft.TextButton]):
        self.permission_listview.disabled = True
        yield

        # ... "data": {"latest": []}
        # All selected user groups after submitting changes
        to_submit_list = []
        for checkbox in self.permission_listview.controls:
            assert isinstance(checkbox, ft.Checkbox)
            if checkbox.value is True:
                to_submit_list.append(checkbox.data)

        response = await do_request(
            action="change_group_permissions",
            data={
                "group_name": self.group_name,
                "permissions": to_submit_list,
            },
            username=self.app_shared.username,
            token=self.app_shared.token,
        )
        if (code := response["code"]) != 200:
            send_error(
                self.page,
                _("Change user group permissions failed: ({code}) {message}").format(
                    code=code, message=response["message"]
                ),
            )
        else:
            await self.refresh_permission_list()

        self.close()
        await self.parent_manager.refresh_group_list()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def refresh_button_click(self, event: ft.Event[ft.IconButton]):
        assert isinstance(self.page, ft.Page)
        self.page.run_task(self.refresh_permission_list)

    async def refresh_permission_list(self):
        self.permission_listview.disabled = True
        self.refresh_button.disabled = True
        self.update()

        # Reset list
        self.permission_listview.controls = []

        # Fetch user group information
        group_info_response = await do_request(
            action="get_group_info",
            data={"group_name": self.group_name},
            username=self.app_shared.username,
            token=self.app_shared.token,
        )
        if (code := group_info_response["code"]) != 200:
            send_error(
                self.page,
                _("Failed to fetch user group info: ({code}) {message}").format(
                    code=code, message=group_info_response["message"]
                ),
            )
            return

        all_permission_list = group_info_response["data"]["permissions"]

        for each_permission in all_permission_list:
            self.permission_listview.controls.append(
                ft.Checkbox(
                    label=each_permission,  # May change to display name later
                    data=each_permission,
                    on_change=None,  # Do nothing before submission
                    value=each_permission in all_permission_list,
                )
            )

        self.permission_listview.disabled = False
        self.refresh_button.disabled = False
        self.update()
