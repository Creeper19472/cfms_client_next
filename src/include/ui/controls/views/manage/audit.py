from typing import TYPE_CHECKING, Optional
from datetime import datetime
import flet as ft
import flet_datatable2 as fdt

from include.classes.config import AppConfig
from include.ui.util.notifications import send_error
from include.util.requests import do_request

import gettext

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


if TYPE_CHECKING:
    from include.ui.models.manage import ManageModel


class AuditLogDatatable(fdt.DataTable2):
    def __init__(
        self,
        ref: Optional[ft.Ref] = None,
        visible=False,
    ):
        super().__init__(
            columns=[
                fdt.DataColumn2(
                    label=ft.Text("ID"),
                    size=fdt.DataColumnSize.L,
                    heading_row_alignment=ft.MainAxisAlignment.START,
                    on_sort=self.sort_column,
                ),
                fdt.DataColumn2(label=ft.Text("Action")),
                fdt.DataColumn2(label=ft.Text("Username")),
                fdt.DataColumn2(
                    label=ft.Text("Target"),
                    size=fdt.DataColumnSize.L,
                ),
                fdt.DataColumn2(
                    label=ft.Text("Data"),
                    size=fdt.DataColumnSize.M,
                ),
                fdt.DataColumn2(
                    label=ft.Text("Result"), size=fdt.DataColumnSize.S, numeric=True
                ),
                fdt.DataColumn2(
                    label=ft.Text("Remote Address"), size=fdt.DataColumnSize.M
                ),
                fdt.DataColumn2(
                    label=ft.Text("Time"), numeric=True, size=fdt.DataColumnSize.M
                ),
            ],
            ref=ref,
            visible=visible,
        )

        # heading_row_color=ft.Colors.SECONDARY_CONTAINER
        self.horizontal_margin = 12
        self.data_row_height = 60
        self.sort_ascending = True
        self.on_select_all = self.all_selected
        self.sort_column_index = 7
        self.bottom_margin = 10
        self.min_width = 600

        self.rows = []
        self.expand = True

    async def all_selected(self, event: ft.Event[ft.DataTable]):
        print("All selected")

    async def sort_column(self, event: ft.DataColumnSortEvent):
        print(f"Sorting column {event.column_index}, ascending={event.ascending}")


class AuditLogView(ft.Container):
    def __init__(
        self, parent_model: "ManageModel", ref: Optional[ft.Ref] = None, visible=True
    ):
        super().__init__(ref=ref, visible=visible)
        self.parent_model: "ManageModel" = parent_model
        self.app_config = AppConfig()

        self.margin = 10
        self.padding = 10
        self.alignment = ft.Alignment.TOP_CENTER
        self.expand = True

        self.audit_view_offset = 0
        self.audit_view_count = 100

        self.progress_ring = ft.Row(
            controls=[
                ft.ProgressRing(
                    width=40,
                    height=40,
                    stroke_width=4,
                    value=None,
                )
            ],
            visible=False,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.refresh_button = ft.IconButton(
            ft.Icons.REFRESH,
            on_click=self.refresh_button_click,
        )
        self.navigate_before_button = ft.IconButton(
            ft.Icons.NAVIGATE_BEFORE,
            on_click=self.audit_view_navigate_before_pressed,
        )
        self.navigate_next_button = ft.IconButton(
            ft.Icons.NAVIGATE_NEXT,
            on_click=self.audit_view_navigate_next_pressed,
        )

        self.audit_info_text = ft.Text()
        self.audit_logs_datatable = AuditLogDatatable(visible=False)

        self.content = ft.Column(
            controls=[
                ft.Text(_("Audit Logs"), size=24, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        self.refresh_button,
                        self.navigate_before_button,
                        self.navigate_next_button,
                        self.audit_info_text,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=10,
                ),
                # ft.Divider(),
                self.progress_ring,
                self.audit_logs_datatable,
            ],
        )

    def did_mount(self):
        super().did_mount()
        assert isinstance(self.page, ft.Page)
        self.page.run_task(self.refresh_audit_logs)

    def disable_interactions(self):
        # Show loading status
        self.progress_ring.visible = True
        self.audit_logs_datatable.visible = False
        self.refresh_button.disabled = True
        self.navigate_before_button.disabled = True
        self.navigate_next_button.disabled = True

    def enable_interactions(self):
        self.progress_ring.visible = False
        self.audit_logs_datatable.visible = True
        self.refresh_button.disabled = False

    async def refresh_button_click(self, event: ft.Event[ft.IconButton]):
        await self.refresh_audit_logs()

    async def audit_view_navigate_before_pressed(self, event: ft.Event[ft.IconButton]):
        self.audit_view_offset -= self.audit_view_count
        if self.audit_view_offset < 0:
            self.audit_view_offset = 0
        await self.refresh_audit_logs()

    async def audit_view_navigate_next_pressed(self, event: ft.Event[ft.IconButton]):
        self.audit_view_offset += self.audit_view_count
        await self.refresh_audit_logs()

    async def refresh_audit_logs(self):
        def update_audit_logs_controls(entries: list[dict]):
            self.audit_logs_datatable.rows.clear()

            for entry in entries:
                self.audit_logs_datatable.rows.append(
                    fdt.DataRow2(
                        cells=[
                            ft.DataCell(ft.Text(entry["id"])),
                            ft.DataCell(ft.Text(entry["action"])),
                            ft.DataCell(ft.Text(entry["username"])),
                            ft.DataCell(ft.Text(entry["target"])),
                            ft.DataCell(
                                ft.Text(str(entry["data"]) if entry["data"] else "")
                            ),
                            ft.DataCell(ft.Text(entry["result"])),
                            ft.DataCell(ft.Text(entry["remote_address"])),
                            ft.DataCell(
                                ft.Text(
                                    datetime.fromtimestamp(
                                        entry["logged_time"]
                                    ).strftime("%Y-%m-%d %H:%M:%S")
                                )
                            ),
                        ]
                    )
                )

        self.disable_interactions()
        self.update()

        try:
            response = await do_request(
                self.app_config.get_not_none_attribute("conn"),
                action="view_audit_logs",
                data={"offset": self.audit_view_offset, "count": self.audit_view_count},
                username=self.app_config.username,
                token=self.app_config.token,
            )

            if (code := response["code"]) != 200:
                send_error(
                    self.page,
                    _(f"Load failed: ({code}) {response.get('message', 'Unknown error')}"),
                )
            else:
                data: dict = response.get("data", {})
                total = data.get("total", 0)
                entries = data.get("entries", [])

                view_start = self.audit_view_offset + 1
                view_end = self.audit_view_offset + len(entries)

                # Fix string formatting issue
                self.audit_info_text.value = (
                    _(f"{view_start} - {view_end} of {total} items")
                )

                self.navigate_before_button.disabled = self.audit_view_offset <= 0
                self.navigate_next_button.disabled = (
                    self.audit_view_offset + self.audit_view_count >= total
                )

                update_audit_logs_controls(entries)

            self.enable_interactions()
            self.update()

        except Exception as e:
            # Hide loading status and enable button
            self.progress_ring.controls[0].visible = False
            self.refresh_button.disabled = False
            self.navigate_before_button.disabled = self.audit_view_offset <= 0
            self.navigate_next_button.disabled = False
            self.update()

            send_error(self.page, _(f"Load failed: {str(e)}"))
