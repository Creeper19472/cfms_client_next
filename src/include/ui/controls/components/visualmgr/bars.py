from typing import TYPE_CHECKING
import flet as ft
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.components.visualmgr.editor import (
        SubRuleGroupCollectionArea,
        SubRuleGroupEditEntriesArea,
    )

t = get_translation()
_ = t.gettext


class SubRuleGroupControlBar(ft.Row):
    """
    The control bar for a `SubRuleGroupCollectionArea`.
    Contains an add `IconButton` to add sub-rulegroups.
    """

    def __init__(
        self,
        parent_collection_area: "SubRuleGroupCollectionArea",
        ref: ft.Ref | None = None,
    ):
        super().__init__(ref=ref)
        self.page: ft.Page
        self.parent_collection_area = parent_collection_area

        self.progress_ring = ft.ProgressRing(visible=False)
        self.add_button = ft.IconButton(
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

    async def on_add_button_click(self, event: ft.Event[ft.IconButton]):
        from include.ui.controls.components.visualmgr.editor import SubRuleGroupEditArea

        assert type(self.parent_collection_area.controls) == list

        self.disable_interactions()
        
        # Count existing subgroups to determine the correct index
        existing_subgroups = sum(
            1 for control in self.parent_collection_area.controls
            if isinstance(control, SubRuleGroupEditArea)
        )
        
        new_subgroup = SubRuleGroupEditArea(
            self.parent_collection_area,
            index=existing_subgroups + 1,  # Start from 1
            match_mode="all",
            match_groups={},
            match_rights={},
        )
        self.parent_collection_area.controls.append(new_subgroup)
        self.parent_collection_area.update()
        
        # Sync data to parent editor immediately
        self.parent_collection_area.parent_edit_section.sync_data_to_parent()
        
        self.enable_interactions()


class EntryListTileControlBar(ft.Row):
    """
    The control bar for adding entries to a `SubRuleGroupEditEntriesArea`.
    Contains a `TextField` for entry name input and an Add `IconButton`.
    """

    def __init__(
        self,
        parent_area: "SubRuleGroupEditEntriesArea",
        ref: ft.Ref | None = None,
    ):
        super().__init__(ref=ref)
        self.page: ft.Page
        self.parent_area = parent_area

        self.progress_ring = ft.ProgressRing(visible=False)
        self.name_textfield = ft.TextField(
            expand=True,
            expand_loose=True,
            hint_text=_("Add..."),
            on_submit=self.on_textfield_submit,
        )
        self.submit_button = ft.IconButton(
            icon=ft.Icons.ADD,
            on_click=self.on_add_button_click,
        )

        self.controls = [
            self.name_textfield,
            self.submit_button,
            self.progress_ring,
        ]

    def disable_interactions(self):
        self.name_textfield.disabled = True
        self.submit_button.visible = False
        self.progress_ring.visible = True
        self.update()

    def enable_interactions(self):
        self.name_textfield.disabled = False
        self.submit_button.visible = True
        self.progress_ring.visible = False
        self.update()

    async def on_textfield_submit(self, event: ft.Event[ft.TextField]):
        self.page.run_task(self.action_submit)

    async def on_add_button_click(self, event: ft.Event[ft.IconButton]):
        self.page.run_task(self.action_submit)

    async def action_submit(self):
        from include.ui.controls.components.visualmgr.editor import EntryListTile
        current_textfield_value = self.name_textfield.value.strip()
        if not current_textfield_value:
            return  # Ignore empty input

        self.disable_interactions()
        self.parent_area.require.append(current_textfield_value)
        self.parent_area.require_listview.controls.append(
            EntryListTile(self.parent_area, current_textfield_value)
        )
        self.parent_area.require_listview.update()
        self.name_textfield.value = ""
        
        # Sync data to parent editor immediately
        self.parent_area.parent_edit_area.parent_collection_area.parent_edit_section.sync_data_to_parent()
        
        self.enable_interactions()
