from datetime import datetime
from typing import TYPE_CHECKING
import flet as ft
import gettext, asyncio

from include.classes.config import AppConfig
from include.controllers.dialogs.passwd import PasswdDialogController
from include.ui.controls.dialogs.base import AlertDialog
from include.ui.util.notifications import send_error
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.views.manage.account import ManageAccountsView
    from include.ui.controls.rightmenu.manage.account import UserRightMenuDialog

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class PasswdUserDialog(AlertDialog):
    def __init__(
        self,
        tip: str | None = None,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.app_config = AppConfig()
        self.controller = PasswdDialogController(self)

        self.modal = False
        self.scrollable = True
        self.title = ft.Text("重置用户密码")

        self.progress_ring = ft.ProgressRing(visible=False)

        self.old_passwd_field = ft.TextField(
            label="旧密码",
            password=True,
            can_reveal_password=True,
            on_submit=lambda e: asyncio.create_task(self.new_passwd_field.focus()),
            expand=True,
        )
        self.new_passwd_field = ft.TextField(
            label="新密码",
            password=True,
            can_reveal_password=True,
            on_submit=self.request_passwd_user,
            expand=True,
        )
        self.submit_button = ft.TextButton("提交", on_click=self.request_passwd_user)
        self.cancel_button = ft.TextButton("取消", on_click=self.cancel_button_click)

        self.content = ft.Column(
            controls=[
                self.new_passwd_field,
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

    def send_error(self, message: str):
        send_error(self.page, message)

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
        self.parent_view = parent_view
        self.app_config = AppConfig()

        self.modal = False
        self.scrollable = True
        self.title = ft.Text("创建用户")

        self.progress_ring = ft.ProgressRing(visible=False)

        self.password_field = ft.TextField(
            label="密码",
            password=True,
            can_reveal_password=True,
            on_submit=self.request_create_user,
            expand=True,
        )
        self.nickname_field = ft.TextField(
            label="昵称",
            on_submit=lambda _: asyncio.create_task(self.password_field.focus()),
            expand=True,
        )
        self.username_field = ft.TextField(
            label="用户名",
            on_submit=lambda _: asyncio.create_task(self.nickname_field.focus()),
            expand=True,
        )

        self.submit_button = ft.TextButton(
            "创建",
            on_click=self.request_create_user,
        )
        self.cancel_button = ft.TextButton("取消", on_click=self.cancel_button_click)

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

        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="create_user",
            data={
                "username": self.username_field.value,
                "password": self.password_field.value,
                "nickname": self.nickname_field.value,
                "permissions": [],  # TODO
                "groups": [],
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            send_error(event.page, f"创建用户失败: ({code}) {response['message']}")
        else:
            await self.parent_view.refresh_user_list()

        self.close()


class RenameUserNicknameDialog(AlertDialog):
    def __init__(
        self,
        parent_dialog: "UserRightMenuDialog",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.parent_dialog = parent_dialog
        self.app_config = AppConfig()

        self.modal = False
        self.scrollable = True
        self.title = ft.Text("重命名用户昵称")

        self.progress_ring = ft.ProgressRing(visible=False)

        self.nickname_field = ft.TextField(
            label="用户的新昵称", on_submit=self.request_rename_user, expand=True
        )
        self.submit_button = ft.TextButton("重命名", on_click=self.request_rename_user)
        self.cancel_button = ft.TextButton("取消", on_click=self.cancel_button_click)

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
        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="rename_user",
            data={
                "username": self.parent_dialog.username,
                "nickname": self.nickname_field.value,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )

        if (code := response["code"]) != 200:
            send_error(
                self.page,
                f"重命名用户昵称失败: ({code}) {response['message']}",
            )
        else:
            await self.parent_dialog.parent_listview.parent_manager.refresh_user_list()

        self.close()


class EditUserGroupDialog(AlertDialog):
    def __init__(
        self,
        parent_dialog: "UserRightMenuDialog",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.refresh_button = ft.IconButton(
            ft.Icons.REFRESH,
            on_click=self.refresh_button_click,
        )
        self.submit_button = ft.TextButton("提交", on_click=self.submit_button_click)
        self.cancel_button = ft.TextButton("取消", on_click=self.cancel_button_click)

        self.modal = False
        self.title = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("更改用户组"),
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

    def did_mount(self):
        super().did_mount()
        assert isinstance(self.page, ft.Page)
        self.page.run_task(self.refresh_permission_list)

    async def submit_button_click(self, event: ft.Event[ft.TextButton]):
        self.group_listview.disabled = True
        yield

        # ... "data": {"latest": []}
        # 提交更改后所有勾选的用户组
        to_submit_list = []
        for checkbox in self.group_listview.controls:
            assert isinstance(checkbox, ft.Checkbox)
            if checkbox.value == True:
                to_submit_list.append(checkbox.data)

        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="change_user_groups",
            data={
                "username": self.parent_dialog.username,
                "groups": to_submit_list,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            send_error(
                self.page,
                f"更改用户组失败: ({code}) {response['message']}",
            )

        self.close()
        await self.parent_dialog.parent_listview.parent_manager.refresh_user_list()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def refresh_button_click(self, event: ft.Event[ft.IconButton]):
        assert isinstance(self.page, ft.Page)
        self.page.run_task(self.refresh_permission_list)

    async def refresh_permission_list(self):
        self.group_listview.disabled = True
        self.refresh_button.disabled = True
        self.update()

        # 重置列表
        self.group_listview.controls = []

        # 拉取用户组信息
        group_list_response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="list_groups",
            data={},
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := group_list_response["code"]) != 200:
            send_error(
                self.page,
                f"拉取用户组列表失败: ({code}) {group_list_response['message']}",
            )
            return

        all_group_list = [
            group["name"] for group in group_list_response["data"]["groups"]
        ]

        user_data_response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="get_user_info",
            data={
                "username": self.parent_dialog.username,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := user_data_response["code"]) != 200:
            send_error(
                self.page,
                f"拉取用户信息失败: ({code}) {user_data_response['message']}",
            )
            return
        user_membership_list = user_data_response["data"]["groups"]

        for each_group in all_group_list:
            self.group_listview.controls.append(
                ft.Checkbox(
                    label=each_group,  # 后面可能改成显示名称
                    data=each_group,
                    on_change=None,  # 提交前什么都不处理
                    value=each_group in user_membership_list,
                )
            )

        self.group_listview.disabled = False
        self.refresh_button.disabled = False
        self.update()


class ViewUserInfoDialog(AlertDialog):
    def __init__(
        self,
        parent_dialog: "UserRightMenuDialog",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.parent_dialog = parent_dialog
        self.app_config = AppConfig()

        self.modal = False
        self.scrollable = True

        self.title = ft.Row(
            controls=[
                ft.Text("用户详情"),
                ft.IconButton(
                    ft.Icons.REFRESH,
                    on_click=self.refresh_button_click,
                ),
            ]
        )

        self.progress_ring = ft.ProgressRing(visible=True)

        self.cancel_button = ft.TextButton("取消", on_click=self.cancel_button_click)

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
        assert isinstance(self.page, ft.Page)
        self.page.run_task(self.request_user_info)

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def refresh_button_click(self, event: ft.Event[ft.IconButton]):
        assert isinstance(self.page, ft.Page)
        self.page.run_task(self.request_user_info)

    async def request_user_info(self):

        self.progress_ring.visible = True
        self.info_listview.visible = False
        self.update()

        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="get_user_info",
            data={
                "username": self.parent_dialog.username,
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            self.close()
            send_error(
                self.page,
                f"拉取用户信息失败: ({code}) {response['message']}",
            )
        else:
            self.info_listview.controls = [
                ft.Text(f"用户名: {response['data']['username']}"),
                ft.Text(
                    f"用户昵称: {response['data']['nickname'] if response['data']['nickname'] else '（无）'}"
                ),
                ft.Text(f"用户权限: {response['data']['permissions']}"),
                ft.Text(f"用户组： {response['data']['groups']}"),
                ft.Text(
                    f"用户注册时间: {datetime.fromtimestamp(response['data']['created_time']).strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                ft.Text(
                    f"最后登录于: {datetime.fromtimestamp(response['data']['last_login']).strftime('%Y-%m-%d %H:%M:%S')}"
                ),
            ]
            self.progress_ring.visible = False
            self.info_listview.visible = True

        self.update()
