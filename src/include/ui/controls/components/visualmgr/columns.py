from typing import TYPE_CHECKING
import flet as ft
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.components.visualmgr.editor import (
        VisualRuleEditorEditSection,
    )

t = get_translation()
_ = t.gettext


class CollectionAreasControlBar(ft.Row):
    """
    The control bar for adding new rule groups to the collection areas column.
    """

    def __init__(
        self,
        parent_column: "CollectionAreasColumn",
        ref: ft.Ref | None = None,
    ):
        super().__init__(ref=ref)
        self.page: ft.Page
        self.parent_column = parent_column

        self.progress_ring = ft.ProgressRing(visible=False)
        self.add_button = ft.FilledButton(
            content=_("Add Rule Group"),
            icon=ft.Icons.ADD,
            on_click=self.on_add_button_click,
        )

        self.controls = [
            self.add_button,
            self.progress_ring,
        ]

    def disable_interactions(self):
        self.add_button.visible = False
        self.progress_ring.visible = True
        self.update()

    def enable_interactions(self):
        self.add_button.visible = True
        self.progress_ring.visible = False
        self.update()

    async def on_add_button_click(self, event: ft.Event[ft.Button]):
        from include.ui.controls.components.visualmgr.editor import (
            SubRuleGroupCollectionArea,
        )

        self.disable_interactions()

        # Determine the next index based on existing SubRuleGroupCollectionArea instances
        new_index = sum(
            1
            for control in self.parent_column.controls
            if isinstance(control, SubRuleGroupCollectionArea)
        )

        # Create a new rule group with default "any" match mode
        new_rule_group = SubRuleGroupCollectionArea(
            index=new_index,
            match_mode="any",
            match_groups=[],
            parent_edit_section=self.parent_column.parent_edit_section,
        )
        # Insert before the control bar (which is always the last control)
        self.parent_column.controls.insert(-1, new_rule_group)
        self.parent_column.parent_edit_section.update()
        
        # Sync data to parent editor immediately
        self.parent_column.parent_edit_section.sync_data_to_parent()

        self.enable_interactions()


class CollectionAreasColumn(ft.Column):
    def __init__(
        self,
        parent_edit_section: "VisualRuleEditorEditSection",
        ref: ft.Ref | None = None,
    ):
        super().__init__(expand=True, expand_loose=True, ref=ref)
        self.page: ft.Page
        self.parent_edit_section = parent_edit_section

        # Add the control bar as the last item in the column
        self.controls = [CollectionAreasControlBar(self)]
