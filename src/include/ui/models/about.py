import asyncio, gettext
import flet as ft

from flet_model import Model, route
from include.constants import APP_VERSION, BUILD_VERSION

from include.ui.controls.dialogs.upgrade import UpgradeDialog
from include.ui.controls.dialogs.whatsnew import ChangelogHistoryDialog
from include.util.upgrade.updater import (
    SUPPORTED_PLATFORM,
    GithubAsset,
    get_latest_release,
    is_new_version,
)

from include.ui.util.notifications import send_error
import requests, os

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext

SUPPORTED_PLATFORM: dict
RUNTIME_PATH: str
FLET_APP_STORAGE_TEMP: str


@route("about")
class AboutModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10
    scroll = ft.ScrollMode.AUTO

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.appbar = ft.AppBar(
            title=ft.Text("About"),
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=self.back_button_click,
            ),
        )

        self.about_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Classified File Management System Client",
                        size=22,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        _(f"Version: {APP_VERSION}"),
                        size=16,
                        text_align=ft.TextAlign.LEFT,
                    ),
                    ft.Text(
                        _("Copyright © 2025 Creeper Team"),
                        size=16,
                        text_align=ft.TextAlign.LEFT,
                    ),
                    ft.Text(
                        _("Licensed under Apache License Version 2.0."),
                        size=16,
                        text_align=ft.TextAlign.LEFT,
                    ),
                    ft.TextButton(
                        _("View changelogs"), on_click=self.view_changelogs_button_click
                    ),
                ],
                expand=True,
            ),
            margin=10,
            padding=10,
            # alignment=ft.alignment.center,
            visible=True,
        )

        self.suc_update_button = ft.IconButton(
            icon=ft.Icons.UPDATE,
            on_click=self.suc_button_click,
        )
        self.suc_progress_ring = ft.ProgressRing(visible=False)
        self.suc_progress_text = ft.Text(_("正在检查更新"), visible=False)
        self.suc_environ_unavailable_text = ft.Text(
            _("无法更新：源代码运行时不能检查更新。"), visible=False
        )
        self.suc_unavailable_text = ft.Text(visible=False)

        self.suc_upgrade_button = ft.Button(
            _("更新"),
            on_click=self.upgrade_button_click,
            visible=False,
        )
        self.suc_release_info = ft.Column(
            controls=[], visible=False, scroll=ft.ScrollMode.AUTO, expand=True
        )

        self.software_updater_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                _("软件更新"),
                                size=22,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            self.suc_update_button,
                            self.suc_upgrade_button,
                        ]
                    ),
                    ft.Column(
                        controls=[
                            self.suc_progress_ring,
                            self.suc_progress_text,
                            self.suc_unavailable_text,
                            self.suc_environ_unavailable_text,
                            self.suc_release_info,
                        ],
                    ),
                ],
            ),
            margin=10,
            padding=10,
            # alignment=ft.alignment.center,
            visible=True,
        )

        self.controls = [self.about_container, self.software_updater_container]

    async def on_link_tapped(self, event: ft.Event[ft.Markdown]):
        assert type(self.page) == ft.Page
        assert type(event.data) == str
        await self.page.launch_url(event.data)

    def disable_interactions(self):
        self.suc_update_button.disabled = True

        self.suc_upgrade_button.visible = False
        self.suc_upgrade_button.disabled = False

        self.suc_progress_ring.visible = True
        self.suc_progress_text.visible = True
        self.suc_environ_unavailable_text.visible = False
        self.suc_unavailable_text.visible = False
        self.suc_release_info.visible = False

    def enable_interactions(self):
        self.suc_update_button.disabled = False
        self.suc_progress_ring.visible = False
        self.suc_progress_text.visible = False

    async def suc_button_click(self, event: ft.Event[ft.IconButton]):
        async for i in self.check_for_updates():
            yield

    async def upgrade_button_click(self, event: ft.Event[ft.Button]):
        self.page.run_task(self.do_release_upgrade)

    async def view_changelogs_button_click(self, event: ft.Event[ft.TextButton]):
        self.page.show_dialog(ChangelogHistoryDialog())

    async def check_for_updates(self):
        yield self.disable_interactions()

        async def _impl_check_for_updates():

            # 设定运行架构下要查找的版本。
            assert self.page.platform
            match_text = SUPPORTED_PLATFORM.get(self.page.platform.value)

            try:
                # 使用线程池避免阻塞主事件循环
                loop = asyncio.get_running_loop()
                latest = await loop.run_in_executor(None, get_latest_release)
            except requests.exceptions.ConnectionError as e:
                send_error(self.page, _(f"连接失败：{e.strerror}"))
                return

            if not latest:
                self.suc_unavailable_text.value = _("未获取到版本信息")
                self.suc_unavailable_text.visible = True
                return

            self.suc_release_info.controls = [
                ft.Text(
                    _(f"当前版本：{APP_VERSION}"),
                    size=16,
                    text_align=ft.TextAlign.LEFT,
                ),
                ft.Text(
                    _(f"最新版本：{latest.version}"),
                    size=16,
                    text_align=ft.TextAlign.LEFT,
                ),
                ft.Text(
                    _("更新说明："),
                    size=16,
                    text_align=ft.TextAlign.LEFT,
                ),
                ft.Markdown(
                    latest.info,
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    on_tap_link=self.on_link_tapped,
                ),
            ]

            if not is_new_version(False, 0, BUILD_VERSION, latest.version):
                self.suc_unavailable_text.value = _("已是最新版本")
                self.suc_unavailable_text.visible = True
                return

            if match_text:
                for asset in latest.assets:
                    if match_text in asset.name:
                        self.suc_upgrade_button.data = asset  # 设置下载链接
                        self.suc_upgrade_button.visible = True
                        self.suc_release_info.visible = True
                        break  # releases 方面应当保证匹配结果唯一，如果唯一的话就没必要继续匹配了

                # 判断是否有找到对应架构的包
                if not self.suc_upgrade_button.visible:
                    self.suc_unavailable_text.value = _(
                        "未在最新版本中找到对应架构的包"
                    )
                    self.suc_unavailable_text.visible = True
            else:
                self.suc_unavailable_text.value = _("没有找到更新：不支持的架构")
                self.suc_unavailable_text.visible = True

        if not os.environ.get("FLET_APP_CONSOLE"):
            await _impl_check_for_updates()
        else:
            await asyncio.sleep(1)
            self.suc_environ_unavailable_text.visible = True

        yield self.enable_interactions()

    async def do_release_upgrade(self):
        target_asset: GithubAsset = self.suc_upgrade_button.data
        if not (download_url := target_asset.download_link):
            return
        assert type(download_url) == str
        save_filename = download_url.split("/")[-1]

        self.suc_upgrade_button.disabled = True
        self.update()

        self.page.show_dialog(
            UpgradeDialog(download_url, save_filename, target_asset.digest)
        )

        self.suc_upgrade_button.disabled = False
        self.update()

    async def back_button_click(self, event: ft.Event[ft.IconButton]):
        self.page.views.pop()
        if last_route := self.page.views[-1].route:
            await self.page.push_route(last_route)
        else:
            await self.page.push_route("/home")  # fallback

    def did_mount(self) -> None:
        async def run():
            async for _ in self.check_for_updates():
                self.update()

        asyncio.create_task(run())
