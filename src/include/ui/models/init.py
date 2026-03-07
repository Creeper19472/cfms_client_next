"""Application first-time initialisation wizard.

Shown on the very first launch (when the CA certificate manifest does not yet
exist) to perform one-time setup tasks before the main UI is displayed.  The
wizard is designed with a **step list** so that future setup tasks can be
added by appending to :attr:`AppInitModel._steps` without restructuring the
UI.
"""

import asyncio
from typing import Any

import flet as ft
from flet_model import Model, Router, route
from flet_material_symbols import Symbols

from include.classes.services.ca_update import CACertUpdateService
from include.classes.shared import AppShared
from include.constants import ROOT_PATH
from include.util.ca_update import build_initial_manifest
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

# Path to the bundled CA certificate directory (mirrors the service constant)
_CA_DIR = ROOT_PATH / "include" / "ca"


@route("init")
class AppInitModel(Model):
    """Full-screen initialisation wizard displayed on first application launch.

    The wizard runs a list of *steps* sequentially.  Each step is a dict with:

    ``title`` (str)
        Short human-readable name displayed in the step list.
    ``action`` (async callable → None)
        Coroutine that performs the step; may raise on failure.

    Adding a new setup task for future expansion requires only appending one
    entry to :attr:`_steps` in :meth:`__init__` — no other changes needed.

    On completion the wizard navigates to ``/connect`` and shows a
    :class:`ft.SnackBar` offering an immediate CA certificate check.
    """

    vertical_alignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment = ft.CrossAxisAlignment.CENTER
    padding = 40
    spacing = 0

    def __init__(self, page: ft.Page, router: Router) -> None:
        super().__init__(page, router)
        self.page: ft.Page
        self.app_shared = AppShared()

        # --- step definitions (append here to add future setup tasks) ---------
        self._steps: list[dict[str, Any]] = [
            {
                "title": _("Compile CA certificate manifest"),
                "action": self._step_compile_manifest,
            },
        ]

        # --- overall progress bar ---------------------------------------------
        self.progress_bar = ft.ProgressBar(
            value=0.0,
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
            color=ft.Colors.BLUE_200,
        )

        # --- spinner shown while any step is running --------------------------
        self.progress_ring = ft.ProgressRing(
            width=32,
            height=32,
            stroke_width=3,
            color=ft.Colors.BLUE_200,
        )

        # --- current step description below progress bar ----------------------
        self.current_step_text = ft.Text(
            _("Preparing..."),
            size=13,
            text_align=ft.TextAlign.CENTER,
            color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
        )

        # --- step list (one row per step) -------------------------------------
        self._step_icons: list[ft.Icon] = []
        self._step_texts: list[ft.Text] = []
        step_rows: list[ft.Control] = []
        for step in self._steps:
            icon = ft.Icon(
                Symbols.RADIO_BUTTON_UNCHECKED,
                size=16,
                color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE),
            )
            label = ft.Text(
                step["title"],
                size=13,
                color=ft.Colors.with_opacity(0.65, ft.Colors.WHITE),
                expand=True,
                expand_loose=True,
            )
            self._step_icons.append(icon)
            self._step_texts.append(label)
            step_rows.append(
                ft.Row(
                    controls=[icon, label],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        # --- main column layout -----------------------------------------------
        self.controls = [
            ft.Column(
                controls=[
                    # Title row with spinner
                    ft.Row(
                        controls=[
                            self.progress_ring,
                            ft.Text(
                                _("Initializing"),
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                                expand=True,
                                expand_loose=True,
                            ),
                        ],
                        spacing=14,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=16),
                    # Step list
                    ft.Column(
                        controls=step_rows,
                        spacing=8,
                    ),
                    ft.Container(height=20),
                    # Active step label
                    self.current_step_text,
                    ft.Container(height=6),
                    # Progress bar
                    ft.Row(
                        controls=[self.progress_bar],
                        expand=True,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                width=420,
            )
        ]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def did_mount(self) -> None:
        super().did_mount()
        self.page.run_task(self._run_all_steps)

    # ------------------------------------------------------------------
    # Step execution engine
    # ------------------------------------------------------------------

    async def _run_all_steps(self) -> None:
        """Run every step in sequence, then navigate to the connect screen."""
        total = len(self._steps)

        for idx, step in enumerate(self._steps):
            # Mark current step as in-progress
            self._step_icons[idx].icon = Symbols.RADIO_BUTTON_CHECKED
            self._step_icons[idx].color = ft.Colors.BLUE_200
            self._step_texts[idx].color = ft.Colors.WHITE
            self.current_step_text.value = step["title"]
            self.progress_bar.value = idx / total
            self.update()

            try:
                await step["action"]()
                self._step_icons[idx].icon = Symbols.RADIO_BUTTON_CHECKED
                self._step_icons[idx].color = ft.Colors.GREEN_300
                self._step_texts[idx].color = ft.Colors.WHITE
            except Exception as exc:
                self._step_icons[idx].icon = Symbols.ERROR_OUTLINE
                self._step_icons[idx].color = ft.Colors.ORANGE_300
                label_val = self._step_texts[idx].value or ""
                self._step_texts[idx].value = f"{label_val} ({exc})"

            self.progress_bar.value = (idx + 1) / total
            self.update()
            # Brief pause so the user can see each step complete
            await asyncio.sleep(0.05)

        # All done — update label
        self.current_step_text.value = _("Setup complete.")
        self.update()

        await asyncio.sleep(0.3)

        # Navigate to the main connect screen
        await self.page.push_route("/connect")

        # Offer an immediate CA certificate check via SnackBar action
        service_manager = self.app_shared.service_manager
        if service_manager is not None:
            ca_service = service_manager.get_service(
                "ca_cert_update", CACertUpdateService
            )

            async def _do_update(e: ft.Event) -> None:
                if ca_service is None:
                    return

                service = ca_service

                from include.ui.controls.dialogs.ca_update_progress import (
                    CACertUpdateProgressDialog,
                )

                progress_dialog = CACertUpdateProgressDialog()
                self.page.show_dialog(progress_dialog)
                try:
                    await service.update_now(
                        on_progress=progress_dialog.make_progress_callback()
                    )
                finally:
                    progress_dialog.close()

            snackbar = ft.SnackBar(
                content=ft.Text(
                    _(
                        "CA certificate manifest is ready. "
                        "Would you like to check for updates now?"
                    )
                ),
                action=_("Update Now"),
                on_action=lambda e: self.page.run_task(_do_update, e),
                duration=ft.Duration(seconds=8),
            )
            self.page.show_dialog(snackbar)

    # ------------------------------------------------------------------
    # Step implementations
    # ------------------------------------------------------------------

    async def _step_compile_manifest(self) -> None:
        """Build the initial CA certificate manifest from existing local files."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, build_initial_manifest, _CA_DIR)
