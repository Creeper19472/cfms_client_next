from typing import TYPE_CHECKING

import flet as ft

from include.ui.controls.explorer.contextmenus import DirectoryContextMenu, FileContextMenu
from include.ui.controls.explorer.state import ExplorerState
from include.classes.ui.enum import SortMode, SortOrder
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.explorer.view import FileManagerView

t = get_translation()
_ = t.gettext

_SORT_OPTIONS = [
    ft.DropdownOption("name", _("Name")),
    ft.DropdownOption("created_at", _("Created at")),
    ft.DropdownOption("modified", _("Last Modified")),
    ft.DropdownOption("size", _("Size")),
    ft.DropdownOption("type", _("Type")),
]

_SORT_MODE_MAP: dict[str, SortMode] = {
    "name": SortMode.BY_NAME,
    "created_at": SortMode.BY_CREATED_AT,
    "modified": SortMode.BY_LAST_MODIFIED,
    "size": SortMode.BY_SIZE,
    "type": SortMode.BY_TYPE,
}

_SORT_VALUE_MAP: dict[SortMode, str] = {v: k for k, v in _SORT_MODE_MAP.items()}


@ft.component
def ExplorerBody(state: ExplorerState, parent_manager: "FileManagerView") -> ft.Control:
    """Declarative component that renders the file-explorer body from state.

    Flet automatically re-runs this function and reconciles the returned
    control tree whenever any field on *state* changes — no explicit
    ``update()`` / ``visible`` mutations are needed.

    Three mutually-exclusive rendering paths:

    * ``state.is_loading`` → progress indicator
    * ``state.is_access_denied`` → access-denied message with reason
    * otherwise → optional selection toolbar + sort bar + file/folder list
    """
    from include.ui.controls.explorer.path import get_directory

    # ── 1. Loading ─────────────────────────────────────────────────────────
    if state.is_loading:
        return ft.Row(
            [ft.ProgressRing()],
            alignment=ft.MainAxisAlignment.CENTER,
        )

    # ── 2. Access denied ───────────────────────────────────────────────────
    if state.is_access_denied:
        return _AccessDeniedBody(state=state, parent_manager=parent_manager)

    # ── 3. Normal content ──────────────────────────────────────────────────
    dirs, files = state.sorted_items()

    show_parent = (
        state.parent_id is not None
        and state.current_directory_id != state.root_directory_id
    )

    async def parent_button_click(e: ft.Event[ft.ListTile]) -> None:
        parent_manager.state.current_directory_id = (
            None if state.parent_id == "/" else state.parent_id
        )
        if await get_directory(
            parent_manager.state.current_directory_id,
            parent_manager.file_listview,
        ):
            parent_manager.indicator.back()

    # Build list items -------------------------------------------------
    if state.selection_mode:
        from include.ui.controls.explorer.components.tile import DirectoryTile, FileTile

        def on_directory_selection_changed(dir_id: str, is_selected: bool) -> None:
            new = set(state.selected_directory_ids)
            if is_selected:
                new.add(dir_id)
            else:
                new.discard(dir_id)
            state.selected_directory_ids = new

        def on_file_selection_changed(file_id: str, is_selected: bool) -> None:
            new = set(state.selected_file_ids)
            if is_selected:
                new.add(file_id)
            else:
                new.discard(file_id)
            state.selected_file_ids = new

        items: list[ft.Control] = []
        if show_parent:
            items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.ARROW_BACK),
                    title=ft.Text("<...>"),
                    subtitle=ft.Text(_("Parent directory")),
                    on_click=parent_button_click,
                )
            )
        items += [
            DirectoryTile(
                dir_name=d["name"],
                directory_id=d["id"],
                created_at=d["created_time"],
                selection_mode=True,
                is_selected=d["id"] in state.selected_directory_ids,
                on_selection_changed=on_directory_selection_changed,
            )
            for d in dirs
        ]
        items += [
            FileTile(
                filename=f["title"],
                file_id=f["id"],
                size=f["size"],
                last_modified=f["last_modified"],
                selection_mode=True,
                is_selected=f["id"] in state.selected_file_ids,
                on_selection_changed=on_file_selection_changed,
            )
            for f in files
        ]
    else:
        items = []
        if show_parent:
            items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.ARROW_BACK),
                    title=ft.Text("<...>"),
                    subtitle=ft.Text(_("Parent directory")),
                    on_click=parent_button_click,
                )
            )
        items += [
            DirectoryContextMenu(
                parent_listview=parent_manager.file_listview,
                directory_id=d["id"],
                dir_name=d["name"],
                created_at=d["created_time"],
            )
            for d in dirs
        ]
        items += [
            FileContextMenu(
                parent_listview=parent_manager.file_listview,
                file_id=f["id"],
                filename=f["title"],
                size=f["size"],
                last_modified=f["last_modified"],
            )
            for f in files
        ]

    # Selection toolbar (shown when in selection mode) -----------------
    count = state.get_selected_count()

    async def cancel_selection(e: ft.Event[ft.TextButton]) -> None:
        state.selection_mode = False
        state.clear_selection()
        parent_manager.top_bar.selection_toggle_button.visible = True
        parent_manager.top_bar.update()

    selection_bar = ft.Row(
        controls=[
            ft.Text(
                _("1 item selected")
                if count == 1
                else _("{count} items selected").format(count=count),
                size=14,
                weight=ft.FontWeight.W_500,
            ),
            ft.VerticalDivider(),
            ft.TextButton(
                content=_("Select All"),
                icon=ft.Icons.SELECT_ALL,
                on_click=lambda _: state.select_all(),
            ),
            ft.TextButton(
                content=_("Clear"),
                icon=ft.Icons.CLEAR,
                on_click=lambda _: state.clear_selection(),
            ),
            ft.VerticalDivider(),
            ft.TextButton(
                content=_("Download"),
                icon=ft.Icons.DOWNLOAD,
                on_click=lambda _: parent_manager.page.run_task(
                    parent_manager.controller.action_batch_download
                ),
            ),
            ft.TextButton(
                content=_("Move"),
                icon=ft.Icons.DRIVE_FILE_MOVE,
                on_click=lambda _: parent_manager.page.run_task(
                    parent_manager.controller.action_batch_move
                ),
            ),
            ft.TextButton(
                content=_("Delete"),
                icon=ft.Icons.DELETE,
                on_click=lambda _: parent_manager.page.run_task(
                    parent_manager.controller.action_batch_delete
                ),
            ),
            ft.VerticalDivider(),
            ft.TextButton(
                content=_("Cancel"),
                icon=ft.Icons.CLOSE,
                on_click=cancel_selection,
            ),
        ],
        spacing=10,
    )

    # Sort bar ---------------------------------------------------------
    async def on_sort_change(e: ft.Event[ft.Dropdown]) -> None:
        state.sort_mode = _SORT_MODE_MAP.get(e.control.value, SortMode.BY_NAME)

    async def on_order_toggle(e: ft.Event[ft.IconButton]) -> None:
        state.sort_order = (
            SortOrder.DESCENDING
            if state.sort_order == SortOrder.ASCENDING
            else SortOrder.ASCENDING
        )

    sort_bar = ft.Row(
        controls=[
            ft.Text(_("Sort by:"), size=14),
            ft.Dropdown(
                options=_SORT_OPTIONS,
                value=_SORT_VALUE_MAP.get(state.sort_mode, "name"),
                on_select=on_sort_change,
                expand=True,
                expand_loose=True,
            ),
            ft.IconButton(
                icon=(
                    ft.Icons.ARROW_UPWARD
                    if state.sort_order == SortOrder.ASCENDING
                    else ft.Icons.ARROW_DOWNWARD
                ),
                tooltip=_("Toggle Sort Order"),
                on_click=on_order_toggle,
            ),
        ],
        margin=ft.Margin(10, 0, 10, 0),
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return ft.Column(
        controls=[
            *(([selection_bar]) if state.selection_mode else []),
            sort_bar,
            ft.ListView(items, expand=True),
        ],
        expand=True,
    )


@ft.component
def _AccessDeniedBody(
    state: ExplorerState, parent_manager: "FileManagerView"
) -> ft.Control:
    """Component that renders the access-denied message."""
    from include.ui.controls.explorer.path import get_directory

    async def back_button_click(e: ft.Event[ft.Button]) -> None:
        await get_directory(state.current_directory_id, parent_manager.file_listview)

    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding(top=30, left=40, right=40),
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.LOCK, size=80, color=ft.Colors.WHITE),
                ft.Container(height=20),
                ft.Text(
                    _("Access Denied"),
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=10),
                ft.Text(
                    _(
                        "You don't have permission to access this directory. "
                        "The reasons are as follows:"
                    ),
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=20),
                ft.Container(
                    content=ft.Text(
                        state.access_denied_reason,
                        size=14,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.GREY_400,
                    ),
                    padding=10,
                    border=ft.Border(
                        top=ft.BorderSide(1, ft.Colors.GREY_700),
                        bottom=ft.BorderSide(1, ft.Colors.GREY_700),
                    ),
                ),
                ft.Text(
                    _(
                        "According to the server's protocol, you do not have "
                        "permission to access the requested directory. There "
                        "could be various reasons for this. If you have any "
                        "questions about this situation, please contact your "
                        "system administrator. This incident will be reported."
                    ),
                    size=14,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.GREY_400,
                    margin=ft.Margin(top=20),
                ),
                ft.Container(height=30),
                ft.Row(
                    controls=[
                        ft.Button(
                            content=_("Go Back"),
                            icon=ft.Icons.ARROW_BACK,
                            on_click=back_button_click,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

