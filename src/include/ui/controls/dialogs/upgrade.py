import os
import asyncio
import threading
from typing import Optional
import flet as ft
from flet_open_file import OpenFile
from flet_permission_handler import Permission, PermissionHandler, PermissionStatus
import requests

from include.classes.config import AppConfig
from include.constants import FLET_APP_STORAGE_TEMP, LOCALE_PATH, RUNTIME_PATH
from include.ui.controls.dialogs.base import AlertDialog
from include.ui.util.notifications import send_error
from include.util.transfer import calculate_sha256
from include.util.upgrade.updater import AssetDigest, AssetDigestType

import gettext

t = gettext.translation("client", LOCALE_PATH, fallback=True)
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
        self.title = ft.Text(_("Update"))

        self.stop_event = asyncio.Event()
        self.download_url = download_url
        self.save_filename = save_filename
        self.asset_digest = asset_digest

        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )
        self.upgrade_note = ft.Text(visible=False)
        self.upgrade_progress = ft.ProgressBar()
        self.upgrade_progress_text = ft.Text(value=_("Preparing download"))

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
        self.upgrade_note.value = _("Extracting version package")
        self.upgrade_note.visible = True
        self.update()
        await asyncio.sleep(0)

        try:
            from zipfile import ZipFile
            import subprocess

            # Ensure temporary directory exists
            os.makedirs(f"{FLET_APP_STORAGE_TEMP}/update", exist_ok=True)

            with ZipFile(
                f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}", "r"
            ) as zip_ref:
                zip_ref.extractall(f"{FLET_APP_STORAGE_TEMP}/update")

            self.upgrade_note.value = _("Deleting extracted package")
            self.update()
            await asyncio.sleep(0)

            try:
                os.remove(f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}")
            except FileNotFoundError:
                pass
            except Exception as e:
                send_error(
                    self.page, _("Failed to delete temporary file: {e}").format(e=e)
                )

            self.upgrade_note.value = _("Writing update script")
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

            self.upgrade_note.value = _("Closing application")
            self.update()
            await asyncio.sleep(0)

            # Launch update script using subprocess
            subprocess.Popen(["cmd", "/c", "start", "", update_script_path], shell=True)

            # Close application
            await asyncio.sleep(1)

            assert isinstance(self.page, ft.Page)
            await self.page.window.close()

        except Exception as e:
            send_error(self.page, _("Error occurred during update: {e}").format(e=e))

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
                    _(
                        "Authorization failed, you will not be able to install updates normally. Please allow the app to install updates in settings."
                    ),
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
        """Download Update File"""
        try:
            # Ensure temporary directory exists
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

                            # Update progress
                            if total_size > 0:
                                progress = downloaded_size / total_size
                                self.upgrade_progress.value = progress
                                self.upgrade_progress_text.value = (
                                    f"{progress:.1%} "
                                    f"({downloaded_size} / {total_size} bytes)"
                                )
                            else:
                                self.upgrade_progress_text.value = _(
                                    "Downloaded: {downloaded_size} bytes"
                                ).format(downloaded_size=downloaded_size)

                            self.update()
                            await asyncio.sleep(0)  # Yield control to avoid blocking

                if self.stop_event.is_set():
                    try:
                        os.remove(f"{FLET_APP_STORAGE_TEMP}/{self.save_filename}")
                    except FileNotFoundError:
                        pass
                    return False
                else:
                    return True
            else:
                send_error(
                    self.page,
                    _("Download failed, HTTP status code: {status_code}").format(
                        status_code=response.status_code
                    ),
                )
                return False

        except (requests.exceptions.ConnectionError, requests.exceptions.SSLError) as e:
            send_error(
                self.page,
                _("Network error occurred during update: {strerr}").format(
                    strerr=str(e)
                ),
            )
            return False
        except requests.exceptions.Timeout:
            send_error(
                self.page, _("Download timeout, please check network connection")
            )
            return False
        except Exception as e:
            send_error(
                self.page,
                _("Unknown error occurred during download: {strerr}").format(
                    strerr=str(e)
                ),
            )
            return False
