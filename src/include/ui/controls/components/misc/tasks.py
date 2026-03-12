import flet as ft
from flet_material_symbols import Symbols
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class AddTaskComponent(ft.Row):
    def __init__(self, visible=True):
        super().__init__(visible=visible)
        self.textfield = ft.TextField(
            hint_text=_("Enter document ID"),
            expand=True,
            expand_loose=True,
            visible=False,
            on_submit=self._on_submit,
        )
        self.controls = [
            ft.IconButton(
                icon=Symbols.ADD_LINK,
                tooltip=_("Add new task"),
                on_click=self._on_add_task,
            ),
            self.textfield,
        ]

    async def _on_add_task(self, e):
        """Handle add new task button click."""
        self.textfield.visible = not self.textfield.visible

    async def _on_submit(self, e):
        """Handle task ID submission."""
        task_id = self.textfield.value.strip()
        if task_id:
            pass
