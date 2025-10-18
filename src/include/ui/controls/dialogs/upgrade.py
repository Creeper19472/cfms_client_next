import os
import asyncio
import threading
from typing import Optional
import flet as ft
from flet_open_file import OpenFile
from flet_permission_handler import Permission, PermissionHandler, PermissionStatus
import requests

from include.classes.config import AppConfig
from include.constants import FLET_APP_STORAGE_TEMP, RUNTIME_PATH
from include.ui.controls.dialogs.base import AlertDialog
from include.ui.util.notifications import send_error
from include.util.transfer import calculate_sha256
from include.util.upgrade.updater import AssetDigest, AssetDigestType

import gettext

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext



class UpgradeDialog(AlertDialog):
    def __init__(
        self,
        download_url: str,
        save_filename: str,
        asset_digest: Optional[AssetDigest] = None,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = True
        self.title = ft.Text(_("更新"))

        self.stop_event = asyncio.Event()
        self.download_url = download_url
        self.save_filename = save_filename
        self.asset_digest = asset_digest

        self.cancel_button = ft.TextButton(_("取消"), on_click=self.cancel_button_click)
        self.upgrade_note = ft.Text(visible=False)
        self.upgrade_progress = ft.ProgressBar()
        self.upgrade_progress_text = ft.Text(value=_("正在准备下载"))

        self.content = ft.Column(
            controls=[
                self.upgrade_progress,
                self.upgrade_progress_text,
                self.upgrade_note,
            ],
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
        self.page.run_task(self.do_release_upgrade)

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.stop_event.set()
        self.close()

    async def do_release_upgrade(self):
        if await self._download_update():
            assert isinstance(self.page, ft.Page)
            assert self.page.platform

            if self.page.platform.value == "windows":
                await self._handle_windows_update()
            else:
                await self._handle_other_platforms_update()

    async def _handle_windows_update(self):
        self.upgrade_progress_text.visible = False
        self.upgrade_note.value = "正在解压缩版本包"
        self.upgrade_note.visible = True
        self.update()
        await asyncio.sleep(0)

        try:
            from zipfile import ZipFile
            import subprocess

            # 确保临时目录存在
            os.makedirs(f"{FLET_APP_STORAGE_TEMP}/update", exist_ok=True)

            with ZipFile(
                f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}", "r"
            ) as zip_ref:
                zip_ref.extractall(f"{FLET_APP_STORAGE_TEMP}/update")

            self.upgrade_note.value = "正在删除已解压缩的包"
            self.update()
            await asyncio.sleep(0)

            try:
                os.remove(f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}")
            except FileNotFoundError:
                pass
            except Exception as e:
                send_error(self.page, _(f"删除临时文件失败：{e}"))

            self.upgrade_note.value = "正在写入更新脚本"
            self.update()
            await asyncio.sleep(0)

            _update_script = f"""@echo off
timeout /t 2 /nobreak >nul
taskkill /f /im cfms_client_next.exe >nul 2>&1
xcopy "{FLET_APP_STORAGE_TEMP}\\update\\build\\windows" "{RUNTIME_PATH}" /I /Y /S
rmdir /s /q "{FLET_APP_STORAGE_TEMP}\\update"
exit
"""

            update_script_path = f"{FLET_APP_STORAGE_TEMP}/update.cmd"
            with open(update_script_path, "w", encoding="utf-8") as f:
                f.write(_update_script)

            self.upgrade_note.value = "正在关闭应用"
            self.update()
            await asyncio.sleep(0)

            # 使用subprocess启动更新脚本
            subprocess.Popen(["cmd", "/c", "start", "", update_script_path], shell=True)

            # 关闭应用
            await asyncio.sleep(1)

            assert isinstance(self.page, ft.Page)
            await self.page.window.close()

        except Exception as e:
            send_error(self.page, _(f"更新过程中发生错误：{e}"))

    async def _handle_other_platforms_update(self):
        assert isinstance(self.page, ft.Page)
        app_config = AppConfig()
        ph: PermissionHandler = app_config.get_not_none_attribute("ph_service")

        async def _async_request():
            if (
                await ph.request(Permission.REQUEST_INSTALL_PACKAGES)
                == PermissionStatus.DENIED
            ):
                send_error(
                    self.page,
                    "授权失败，您将无法正常安装更新。请在设置中允许应用安装更新。",
                )
                return False
            return True

        if await _async_request():
            self.open_file_service = OpenFile()
            self.page._services.append(self.open_file_service)
            await self.open_file_service.open(
                f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}"
            )

    async def _download_update(self):
        """下载更新文件"""
        try:
            # 确保临时目录存在
            os.makedirs(FLET_APP_STORAGE_TEMP, exist_ok=True)

            target_path = f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}"
            if (
                self.asset_digest
                and os.path.exists(target_path)
                and os.path.getsize(target_path)
            ):
                match self.asset_digest.type:
                    case AssetDigestType.SHA256:
                        if self.asset_digest.digest == await calculate_sha256(
                            target_path
                        ):
                            return True

            response = requests.get(self.download_url, stream=True, timeout=30)
            if response.status_code == 200:
                total_size = int(response.headers.get("content-length", 0))
                downloaded_size = 0

                with open(f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}", "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.stop_event.is_set():
                            break
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            # 更新进度
                            if total_size > 0:
                                progress = downloaded_size / total_size
                                self.upgrade_progress.value = progress
                                self.upgrade_progress_text.value = (
                                    f"{progress:.1%} "
                                    f"({downloaded_size} / {total_size} bytes)"
                                )
                            else:
                                self.upgrade_progress_text.value = (
                                    _(f"已下载: {downloaded_size} bytes")
                                )

                            self.update()
                            await asyncio.sleep(0)  # 让出控制权，避免阻塞

                if self.stop_event.is_set():
                    try:
                        os.remove(f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}")
                    except FileNotFoundError:
                        pass
                    return False
                else:
                    return True
            else:
                send_error(self.page, _(f"下载失败，HTTP状态码: {response.status_code}"))
                return False

        except (requests.exceptions.ConnectionError, requests.exceptions.SSLError) as e:
            send_error(self.page, _(f"在更新时发生网络错误：{str(e)}"))
            return False
        except requests.exceptions.Timeout:
            send_error(self.page, "下载超时，请检查网络连接")
            return False
        except Exception as e:
            send_error(self.page, _(f"下载过程中发生未知错误：{str(e)}"))
            return False
