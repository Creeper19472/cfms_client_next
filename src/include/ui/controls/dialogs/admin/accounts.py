from typing import TYPE_CHECKING, cast
import asyncio
from datetime import datetime

import flet as ft

from include.classes.shared import AppShared
from include.controllers.dialogs.management import (
    AddUserAccountDialogController,
    EditUserGroupDialogController,
    RenameUserNicknameDialogController,
    ViewUserInfoDialogController,
    BlockUserDialogController,
    ListUserBlocksDialogController,
)
from include.controllers.dialogs.passwd import PasswdDialogController
from include.ui.controls.dialogs.base import AlertDialog
from include.ui.controls.dialogs.file_browser import FileBrowserDialog
from include.util.passwd import generate_random_password

if TYPE_CHECKING:
    from include.ui.controls.views.admin.account import ManageAccountsView

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class PasswdUserDialog(AlertDialog):
    def __init__(
        self,
        username: str,
        tip: str = "",
        passwd_other: bool = False,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.app_shared = AppShared()
        self.controller = PasswdDialogController(self)
        self.username = username
        self.passwd_other = passwd_other

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(
            _("{action_type} User Password").format(
                action_type=_("Change") if not passwd_other else _("Reset")
            )
        )

        self.progress_ring = ft.ProgressRing(visible=False)

        self.old_passwd_field = ft.TextField(
            label=_("Old Password"),
            password=True,
            can_reveal_password=True,
            on_submit=lambda e: asyncio.create_task(self.new_passwd_field.focus()),
            expand=True,
            visible=not passwd_other,
        )
        self.new_passwd_field = ft.TextField(
            label=_("New Password"),
            password=True,
            can_reveal_password=True,
            on_submit=self.request_passwd_user,
            expand=True,
        )
        self.dicing_button = ft.IconButton(
            ft.Icons.CASINO_OUTLINED,
            on_click=self.dicing_button_click,
            tooltip=_("Generate a random password"),
        )

        self.tip_text = ft.Text(tip, text_align=ft.TextAlign.CENTER, visible=bool(tip))
        self.bypass_requirements_checkbox = ft.Checkbox(
            label=_("Bypass password requirements"),
            value=False,
            visible=passwd_other,
        )
        self.force_update_after_login_checkbox = ft.Checkbox(
            label=_("Force user to update password after next login"),
            value=False,
            visible=passwd_other,
        )

        self.submit_button = ft.TextButton(
            _("Submit"), on_click=self.request_passwd_user
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

        self.content = ft.Column(
            controls=[
                self.old_passwd_field,
                ft.Row(
                    [self.new_passwd_field, self.dicing_button],
                    expand=True,
                    expand_loose=True,
                ),
                self.tip_text,
                ft.Column(
                    [
                        self.bypass_requirements_checkbox,
                        self.force_update_after_login_checkbox,
                    ],
                    spacing=0,
                    expand=True,
                    expand_loose=True,
                ),
            ],
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

    async def dicing_button_click(self, event: ft.Event[ft.IconButton]):
        self.new_passwd_field.value = generate_random_password()
        await self.new_passwd_field.focus()
        self.new_passwd_field.selection = ft.TextSelection(
            0, len(self.new_passwd_field.value)
        )
        self.new_passwd_field.password = False  # will permanently show the password
        self.update()

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
        self.app_shared = AppShared()

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(_("Create User"))

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
            _("Create"),
            on_click=self.request_create_user,
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

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
        username: str,
        parent_manager: "ManageAccountsView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.username = username
        self.app_shared = AppShared()
        self.parent_manager = parent_manager
        self.controller = RenameUserNicknameDialogController(self)

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(_("Rename User Nickname"))

        self.progress_ring = ft.ProgressRing(visible=False)

        self.nickname_field = ft.TextField(
            label=_("User's New Nickname"),
            on_submit=self.request_rename_user,
            expand=True,
        )
        self.submit_button = ft.TextButton(
            _("Rename"), on_click=self.request_rename_user
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

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
        username: str,
        parent_manager: "ManageAccountsView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = EditUserGroupDialogController(self)
        self.username = username
        self.parent_manager = parent_manager
        self.app_shared = AppShared()

        self.refresh_button = ft.IconButton(
            ft.Icons.REFRESH,
            on_click=self.refresh_button_click,
        )
        self.submit_button = ft.TextButton(
            _("Submit"), on_click=self.submit_button_click
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

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
        username: str,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = ViewUserInfoDialogController(self)
        self.username = username
        self.app_shared = AppShared()

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

        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

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


class BlockUserDialog(AlertDialog):
    def __init__(
        self,
        username: str,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.username = username
        self.controller = BlockUserDialogController(self)
        self.target_id: str | None = None

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(_("Block User"))

        self.progress_ring = ft.ProgressRing(visible=False)

        # --- Block types ---
        self.block_types_button = ft.SegmentedButton(
            selected_icon=ft.Icon(ft.Icons.BLOCK),
            selected=["read", "write", "move"],
            allow_empty_selection=False,
            allow_multiple_selection=True,
            segments=[
                ft.Segment(
                    value="read",
                    label=ft.Text(_("Read")),
                    icon=ft.Icon(ft.Icons.VISIBILITY_OUTLINED),
                ),
                ft.Segment(
                    value="write",
                    label=ft.Text(_("Write")),
                    icon=ft.Icon(ft.Icons.EDIT_OUTLINED),
                ),
                ft.Segment(
                    value="move",
                    label=ft.Text(_("Move")),
                    icon=ft.Icon(ft.Icons.DRIVE_FILE_MOVE_OUTLINED),
                ),
            ],
        )

        # --- Target type ---
        self.target_type_radio = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="all", label=_("All")),
                    ft.Radio(value="directory", label=_("Directory")),
                    ft.Radio(value="document", label=_("Document")),
                ]
            ),
            value="all",
            on_change=self.on_target_type_change,
        )
        self.target_name_text = ft.Text(
            _("(No target selected)"), italic=True, visible=False, size=12
        )
        self.browse_target_button = ft.TextButton(
            _("Browse..."),
            icon=ft.Icons.FOLDER_OPEN_OUTLINED,
            on_click=self.browse_target_click,
            visible=False,
        )

        # --- Expiry (not_after) ---
        now = datetime.now()
        self.expires_enabled_checkbox = ft.Checkbox(
            label=_("Set expiry time"),
            value=False,
            on_change=self.on_expires_enabled_change,
        )
        self.date_picker = ft.DatePicker(
            first_date=now,
            value=now,
            on_change=self.on_date_change,
        )
        self.time_picker = ft.TimePicker(
            now.time(),
            on_change=self.on_time_change,
        )
        self.date_button = ft.TextButton(
            _("Pick Date"),
            icon=ft.Icons.CALENDAR_TODAY,
            on_click=lambda _: self.page.show_dialog(self.date_picker),
            visible=False,
        )
        self.time_button = ft.TextButton(
            _("Pick Time"),
            icon=ft.Icons.ACCESS_TIME,
            on_click=lambda _: self.page.show_dialog(self.time_picker),
            visible=False,
        )
        self.expires_text = ft.Text(
            now.strftime("%Y-%m-%d %H:%M"), visible=False, size=12
        )

        self.submit_button = ft.TextButton(_("Block"), on_click=self.request_block_user)
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

        self.content = ft.Column(
            controls=[
                ft.Text(_("Block Types"), weight=ft.FontWeight.BOLD),
                self.block_types_button,
                ft.Divider(),
                ft.Text(_("Target"), weight=ft.FontWeight.BOLD),
                self.target_type_radio,
                ft.Row(
                    [self.target_name_text, self.browse_target_button],
                    spacing=10,
                ),
                ft.Divider(),
                ft.Text(_("Expiry"), weight=ft.FontWeight.BOLD),
                self.expires_enabled_checkbox,
                ft.Row(
                    [self.date_button, self.time_button],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.CENTER,
                    wrap=True,
                ),
                self.expires_text,
            ],
            width=480,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=8,
        )
        self.actions = [
            self.progress_ring,
            self.submit_button,
            self.cancel_button,
        ]

    def did_mount(self):
        super().did_mount()
        self.page.overlay.extend([self.date_picker, self.time_picker])
        self.page.update()

    def will_unmount(self):
        for picker in [self.date_picker, self.time_picker]:
            if picker in self.page.overlay:
                self.page.overlay.remove(picker)

    def _update_expires_text(self):
        date_val = self.date_picker.value
        time_val = self.time_picker.value
        date_str = (
            date_val.strftime("%Y-%m-%d")
            if date_val
            else datetime.now().strftime("%Y-%m-%d")
        )
        time_str = time_val.strftime("%H:%M") if time_val else "00:00"
        self.expires_text.value = f"{date_str} {time_str}"

    def disable_interactions(self):
        self.block_types_button.disabled = True
        self.target_type_radio.disabled = True
        self.browse_target_button.disabled = True
        self.expires_enabled_checkbox.disabled = True
        self.date_button.disabled = True
        self.time_button.disabled = True
        self.submit_button.visible = False
        self.cancel_button.disabled = True
        self.progress_ring.visible = True
        self.modal = True

    def enable_interactions(self):
        self.block_types_button.disabled = False
        self.target_type_radio.disabled = False
        self.browse_target_button.disabled = False
        self.expires_enabled_checkbox.disabled = False
        self.date_button.disabled = False
        self.time_button.disabled = False
        self.submit_button.visible = True
        self.cancel_button.disabled = False
        self.progress_ring.visible = False
        self.modal = False
        self.update()

    async def on_target_type_change(self, event: ft.Event[ft.RadioGroup]):
        is_all = event.control.value == "all"
        self.target_name_text.visible = not is_all
        self.browse_target_button.visible = not is_all
        # Always reset the selected target when target type changes
        self.target_id = None
        self.target_name_text.value = _("(No target selected)")
        self.update()

    async def on_expires_enabled_change(self, event: ft.Event[ft.Checkbox]):
        enabled = bool(event.control.value)
        self.date_button.visible = enabled
        self.time_button.visible = enabled
        self.expires_text.visible = enabled
        self.update()

    async def on_date_change(self, event: ft.Event[ft.DatePicker]):
        self._update_expires_text()
        self.update()

    async def on_time_change(self, event: ft.Event[ft.TimePicker]):
        self._update_expires_text()
        self.update()

    async def browse_target_click(self, event: ft.Event[ft.TextButton]):
        target_type = self.target_type_radio.value
        if target_type == "directory":
            browser = FileBrowserDialog(
                title=_("Select Directory"),
                on_select_callback=self._on_target_selected,
                mode="directories",
                show_select_button=True,
            )
        else:
            browser = FileBrowserDialog(
                title=_("Select Document"),
                on_select_callback=self._on_target_selected,
                mode="files",
            )
        self.page.show_dialog(browser)

    def _on_target_selected(self, item_id: str, item_name: str, item_type: str):
        self.target_id = item_id
        self.target_name_text.value = item_name
        self.update()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def request_block_user(self, event: ft.Event[ft.TextButton]):
        self.disable_interactions()
        self.page.run_task(self.controller.action_block_user)


class ListUserBlocksDialog(AlertDialog):
    def __init__(
        self,
        username: str,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.username = username
        self.controller = ListUserBlocksDialogController(self)

        self.modal = False
        self.scrollable = True
        self.title = ft.Row(
            controls=[
                ft.Text(_("User Blocks")),
                ft.IconButton(
                    ft.Icons.REFRESH,
                    on_click=self.refresh_button_click,
                ),
            ]
        )

        self.progress_ring = ft.ProgressRing(visible=True)
        self.blocks_listview = ft.ListView(visible=False, expand=True)

        self.cancel_button = ft.TextButton(
            _("Close"), on_click=self.cancel_button_click
        )

        self.content = ft.Column(
            controls=[self.progress_ring, self.blocks_listview],
            width=500,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        self.actions = [self.cancel_button]

    def disable_interactions(self):
        self.progress_ring.visible = True
        self.blocks_listview.visible = False
        self.update()

    def enable_interactions(self):
        self.progress_ring.visible = False
        self.blocks_listview.visible = True
        self.update()

    def build_block_list(self, blocks: list[dict]):
        """Build the UI list from a list of block records, merging overlapping active blocks."""
        from datetime import datetime as _dt

        self.blocks_listview.controls = []

        if not blocks:
            self.blocks_listview.controls.append(
                ft.Text(_("No active blocks found."), italic=True)
            )
            return

        # Compute merged effective block span across all records.
        # not_after == -1 means no expiry (permanent).
        permanent = any(b.get("not_after", -1) == -1 for b in blocks)
        if not permanent:
            max_not_after = max(b["not_after"] for b in blocks)
        else:
            max_not_after = None

        min_not_before = min(b.get("not_before", 0) for b in blocks)

        # Summary section
        if permanent:
            effective_expires_str = _("Permanent")
        else:
            effective_expires_str = _dt.fromtimestamp(
                cast(float, max_not_after)
            ).strftime("%Y-%m-%d %H:%M:%S")

        not_before_str = (
            _dt.fromtimestamp(min_not_before).strftime("%Y-%m-%d %H:%M:%S")
            if min_not_before > 0
            else _("Immediate")
        )

        self.blocks_listview.controls.append(
            ft.ListTile(
                title=ft.Text(
                    _("Effective block: from {since}, expires {expires}").format(
                        since=not_before_str,
                        expires=effective_expires_str,
                    ),
                    weight=ft.FontWeight.BOLD,
                ),
                subtitle=ft.Text(
                    _("{count} underlying record(s)").format(count=len(blocks))
                ),
            )
        )
        self.blocks_listview.controls.append(ft.Divider())

        # Individual records
        for block in blocks:
            block_id = block.get("block_id", "")
            block_types = block.get("block_types", [])
            target_type = block.get("target_type", "all")
            target_id = block.get("target_id")

            if target_type == "all":
                target_str = _("All")
            elif target_id:
                target_str = f"{target_type}: {target_id}"
            else:
                target_str = target_type

            timestamp = block.get("timestamp")
            timestamp_str = (
                _dt.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                if timestamp is not None
                else _("(Unknown)")
            )

            not_after = block.get("not_after", -1)
            expires_str = (
                _dt.fromtimestamp(not_after).strftime("%Y-%m-%d %H:%M:%S")
                if not_after >= 0
                else _("Permanent")
            )

            block_not_before = block.get("not_before", 0)
            block_not_before_str = (
                _dt.fromtimestamp(block_not_before).strftime("%Y-%m-%d %H:%M:%S")
                if block_not_before > 0
                else _("Immediate")
            )

            revoke_button = ft.TextButton(
                _("Revoke"),
                data=block_id,
                on_click=self.revoke_button_click,
            )

            self.blocks_listview.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.BLOCK),
                    title=ft.Text(
                        _("Types: {types} | Target: {target}").format(
                            types=(
                                ", ".join(block_types) if block_types else _("(None)")
                            ),
                            target=target_str,
                        )
                    ),
                    subtitle=ft.Text(
                        _(
                            "ID: {id}\n"
                            "Created: {created}\n"
                            "Period: {not_before} - {expires}"
                        ).format(
                            created=timestamp_str,
                            not_before=block_not_before_str,
                            expires=expires_str,
                            id=block_id,
                        )
                    ),
                    trailing=revoke_button,
                    is_three_line=True,
                )
            )

    def did_mount(self):
        super().did_mount()
        self.page.run_task(self.controller.action_refresh_blocks)

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def refresh_button_click(self, event: ft.Event[ft.IconButton]):
        self.page.run_task(self.controller.action_refresh_blocks)

    async def revoke_button_click(self, event: ft.Event[ft.TextButton]):
        block_id = event.control.data
        self.page.run_task(self.controller.action_revoke_block, block_id)
