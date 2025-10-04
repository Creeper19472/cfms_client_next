import os
import asyncio, threading
import flet as ft
from flet_open_file import FletOpenFile
from flet_permission_handler import Permission, PermissionHandler, PermissionStatus
import requests

from include.classes.config import AppConfig
from include.constants import FLET_APP_STORAGE_TEMP, RUNTIME_PATH
from include.ui.util.notifications import send_error


class UpgradeDialog(ft.AlertDialog):
    def __init__(
        self,
        # stop_event: asyncio.Event,
        download_url: str,
        save_filename: str,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = True
        self.title = ft.Text("更新")

        # self.stop_event = stop_event
        self.download_url = download_url
        self.save_filename = save_filename
        self.download_thread = UpgradeDownloadThread(
            self, self.download_url, self.save_filename
        )

        self.upgrade_special_button = FletOpenFile(
            value=None, text="执行更新", visible=False
        )
        self.cancel_button = ft.TextButton("取消", on_click=self.cancel_button_click)
        self.upgrade_special_note = ft.Text(
            "您使用的设备需要手动执行更新。再次点击“执行更新”以继续。", visible=False
        )
        self.upgrade_note = ft.Text(visible=False)
        self.upgrade_progress = ft.ProgressBar()
        self.upgrade_progress_text = ft.Text(value="正在准备下载")

        self.content = ft.Column(
            controls=[
                self.upgrade_progress,
                self.upgrade_progress_text,
                self.upgrade_note,
                self.upgrade_special_note,
            ],
            # spacing=15,
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [
            self.upgrade_special_button,
            self.cancel_button,
        ]

    def close(self):
        self.open = False
        self.update()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        # self.stop_event.set()
        self.download_thread.stop()
        self.close()


class UpgradeDownloadThread(threading.Thread):
    def __init__(
        self, upgrade_dialog: UpgradeDialog, download_url: str, save_filename: str
    ):
        super().__init__()
        self.download_url = download_url
        self.save_filename = save_filename
        self.upgrade_dialog = upgrade_dialog
        self.page = upgrade_dialog.page
        self._stop_event = threading.Event()

    def run(self):
        if self._download_update():
            # print(os.getcwd())
            assert type(self.page) == ft.Page
            assert self.page.platform

            if self.page.platform.value == "windows":
                # os.startfile(f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}")
                # 开始执行安装
                self.upgrade_dialog.upgrade_progress_text.visible = False
                self.upgrade_dialog.upgrade_note.value = "正在解压缩版本包"
                self.upgrade_dialog.upgrade_note.visible = True
                self.upgrade_dialog.update()

                from zipfile import ZipFile
                import subprocess

                with ZipFile(
                    f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}", "r"
                ) as zip_ref:
                    zip_ref.extractall(f"{FLET_APP_STORAGE_TEMP}/update")

                self.upgrade_dialog.upgrade_note.value = "正在删除已解压缩的包"
                self.page.update()

                try:
                    os.remove(f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}")
                except FileNotFoundError:
                    pass
                except Exception as e:
                    send_error(self.page, f"删除临时文件失败：{e}")

                self.upgrade_dialog.upgrade_note.value = "正在写入更新脚本"
                self.page.update()

                _update_script = f'taskkill -f -im cfms_client.exe & xcopy "{FLET_APP_STORAGE_TEMP}/update/build/windows" "{RUNTIME_PATH}" /I /Y /S & rmdir /s /q "{FLET_APP_STORAGE_TEMP}/update"'
                with open(f"{FLET_APP_STORAGE_TEMP}/update.cmd", "w") as f:
                    f.write(_update_script)

                self.upgrade_dialog.upgrade_note.value = "正在关闭应用"
                self.page.update()

                # os.system(f'start "{FLET_APP_STORAGE_TEMP}/update.cmd"')
                subprocess.run(["cmd", "/c", f"{FLET_APP_STORAGE_TEMP}/update.cmd"])
                asyncio.create_task(self.page.window.close())

            else:
                self.upgrade_dialog.upgrade_special_button.value = (
                    f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}"
                )
                # print(upgrade_special_button.value)

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

                asyncio.create_task(_async_request())

                self.upgrade_dialog.upgrade_special_button.visible = True
                self.upgrade_dialog.upgrade_special_note.visible = True
                self.upgrade_dialog.update()

    def stop(self):
        self._stop_event.set()

    def _download_update(self):
        try:
            response = requests.get(self.download_url, stream=True)
            if response.status_code == 200:
                total_size = response.headers["content-length"]
                # print(response.headers)
                with open(f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}", "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self._stop_event.is_set():
                            break
                        if chunk:
                            f.write(chunk)
                            self.upgrade_dialog.upgrade_progress.value = (
                                int(f.tell() * 100 / int(total_size)) / 100
                            )
                            self.upgrade_dialog.upgrade_progress_text.value = (
                                f"{int(f.tell() * 100 / int(total_size))}%"
                                f"({int(f.tell())} / {total_size})"
                            )
                            self.upgrade_dialog.update()
                if self._stop_event.is_set():
                    try:
                        os.remove(f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}")
                    except FileNotFoundError:
                        pass
                    return False
                else:
                    return True

            return False

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.SSLError,
        ) as e:
            send_error(self.page, f"在更新时发生错误：{str(e)}")
            return False
