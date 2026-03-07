"""Progress dialog shown while a CA certificate store update is running.

The dialog displays a step list (like the first-run init wizard) so the user
can see exactly which phase the update is in.  The four phases map onto the
``CACertUpdateStages.*`` constants from :mod:`include.util.ca_update`:

* **Connecting** — contacting the remote certificate repository
* **Checking** — comparing the remote listing with the local store
* **Downloading / Removing** — fetching new / updated certificates and
  deleting obsolete ones
* **Saving** — persisting the updated manifest

Usage::

    dialog = CACertUpdateProgressDialog()
    self.page.show_dialog(dialog)
    try:
        result = await service.update_now(
            on_progress=dialog.make_progress_callback()
        )
    finally:
        dialog.close()
"""

from typing import Callable

import flet as ft
from flet_material_symbols import Symbols

from include.ui.controls.dialogs.base import AlertDialog
from include.util.ca_update import CACertUpdateStages
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

__all__ = ["CACertUpdateProgressDialog"]

# Map each CACertUpdateStages.* constant to the index of the step it belongs to.
_STAGE_STEP: dict[CACertUpdateStages, int] = {
    CACertUpdateStages.CONNECTING: 0,
    CACertUpdateStages.CHECKING: 1,
    CACertUpdateStages.DOWNLOADING: 2,
    CACertUpdateStages.REMOVING: 2,
    CACertUpdateStages.SAVING: 3,
}


class CACertUpdateProgressDialog(AlertDialog):
    """Modal dialog that shows step-by-step progress while a CA cert update runs.

    The dialog has four labelled steps (with status icons) and a detail line
    that shows the most recent item being processed (e.g. the filename being
    downloaded).

    Call :meth:`make_progress_callback` to obtain an ``on_progress`` callable
    that can be passed directly to
    :meth:`~include.classes.services.ca_update.CACertUpdateService.update_now`.
    """

    _STEP_LABELS = [
        _("Connecting to repository"),
        _("Checking for updates"),
        _("Downloading / removing files"),
        _("Saving manifest"),
    ]

    def __init__(self) -> None:
        self._current_step: int = -1

        # --- step list --------------------------------------------------------
        self._step_icons: list[ft.Icon] = []
        self._step_texts: list[ft.Text] = []
        step_rows: list[ft.Control] = []
        for label in self._STEP_LABELS:
            icon = ft.Icon(
                Symbols.RADIO_BUTTON_UNCHECKED,
                size=16,
                color=ft.Colors.with_opacity(0.4, ft.Colors.ON_SURFACE),
            )
            text = ft.Text(
                label,
                size=13,
                color=ft.Colors.with_opacity(0.55, ft.Colors.ON_SURFACE),
                expand=True,
                expand_loose=True,
            )
            self._step_icons.append(icon)
            self._step_texts.append(text)
            step_rows.append(
                ft.Row(
                    controls=[icon, text],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        # --- detail label (current item, e.g. filename being downloaded) ------
        self._detail_text = ft.Text(
            _("Starting..."),
            size=12,
            italic=True,
            color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
            text_align=ft.TextAlign.CENTER,
        )

        super().__init__(
            title=ft.Text(_("Updating CA Certificates")),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.ProgressRing(width=28, height=28, stroke_width=3),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Column(controls=step_rows, spacing=6, tight=True),
                    ft.Divider(height=6, color=ft.Colors.TRANSPARENT),
                    self._detail_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                tight=True,
                width=320,
            ),
            modal=True,
            scrollable=True,
        )

    # ------------------------------------------------------------------
    # Internal step management
    # ------------------------------------------------------------------

    def _activate_step(self, idx: int) -> None:
        """Mark *idx* as in-progress and all prior steps as done."""
        if idx <= self._current_step:
            return
        # Complete all steps between current and new
        for i in range(self._current_step + 1, idx):
            self._step_icons[i].icon = Symbols.RADIO_BUTTON_CHECKED
            self._step_icons[i].color = ft.Colors.GREEN_400
            self._step_texts[i].color = ft.Colors.ON_SURFACE
        # Activate the new step
        self._step_icons[idx].icon = Symbols.RADIO_BUTTON_CHECKED
        self._step_icons[idx].color = ft.Colors.BLUE_400
        self._step_texts[idx].color = ft.Colors.ON_SURFACE
        self._current_step = idx

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def make_progress_callback(self) -> "Callable[[CACertUpdateStages, str], None]":
        """Return an ``on_progress(stage, detail)`` callable for this dialog.

        The returned callable is thread-safe: it updates the step list and
        detail label in response to ``CACertUpdateStages.*`` events emitted by
        :func:`~include.util.ca_update.check_and_update_ca_certs`.

        Typical usage::

            result = await service.update_now(
                on_progress=dialog.make_progress_callback()
            )
        """

        def _on_progress(stage: CACertUpdateStages, detail: str = "") -> None:
            step_idx = _STAGE_STEP.get(stage)
            if step_idx is not None:
                self._activate_step(step_idx)

            # Build a human-readable detail line
            if stage == CACertUpdateStages.CONNECTING:
                msg = _("Connecting to certificate repository...")
            elif stage == CACertUpdateStages.CHECKING:
                n = detail or "?"
                msg = _("Fetched {n} remote certificate(s); comparing...").format(n=n)
            elif stage == CACertUpdateStages.DOWNLOADING:
                msg = (
                    _("Downloading {name}...").format(name=detail)
                    if detail
                    else _("Downloading...")
                )
            elif stage == CACertUpdateStages.REMOVING:
                msg = (
                    _("Removing {name}...").format(name=detail)
                    if detail
                    else _("Removing...")
                )
            elif stage == CACertUpdateStages.SAVING:
                msg = _("Saving manifest...")
            else:
                msg = detail or stage

            self._detail_text.value = msg
            try:
                self.update()
            except Exception:
                pass

        return _on_progress
