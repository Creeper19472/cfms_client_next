from copy import deepcopy
from typing import TYPE_CHECKING, Any, Optional
import flet as ft

if TYPE_CHECKING:
    from include.ui.controls.components.rulemanager import VisualRuleEditor

from include.ui.controls.components.visualmgr.columns import (
    CollectionAreasColumn,
    CollectionAreasControlBar,
)
from include.util.locale import get_translation
from include.ui.controls.components.visualmgr.bars import (
    EntryListTileControlBar,
    SubRuleGroupControlBar,
)

t = get_translation()
_ = t.gettext


class EntryListTile(ft.ListTile):
    def __init__(
        self,
        parent_entries_area: "SubRuleGroupEditEntriesArea",
        entry_name: str,
        ref: ft.Ref | None = None,
    ):
        super().__init__(ref=ref)
        self.page: ft.Page
        self.parent_entries_area = parent_entries_area
        self.entry_name = entry_name

        self.title = ft.Text(self.entry_name)
        self.trailing = ft.IconButton(
            icon=ft.Icons.REMOVE,
            on_click=self.on_remove_clicked,
        )

    async def on_remove_clicked(self, event: ft.Event[ft.IconButton]):
        self.parent_entries_area.require.remove(self.entry_name)
        self.parent_entries_area.require_listview.controls.remove(self)
        
        # Sync data to parent editor immediately
        self.parent_entries_area.parent_edit_area.parent_collection_area.parent_edit_section.sync_data_to_parent()


class SubRuleGroupEditEntriesArea(ft.ExpansionTile):
    def __init__(
        self,
        parent_edit_area: "SubRuleGroupEditArea",
        entry_type: str,  # "groups" | "rights"
        match_mode: str,
        require: list[str],
        ref: ft.Ref | None = None,
    ):
        self.page: ft.Page
        self.parent_edit_area = parent_edit_area
        self.entry_type = entry_type
        self.match_mode = match_mode
        self.require = require

        self.mode_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption(
                    "all",
                    _("All"),
                    leading_icon=ft.Icons.SELECT_ALL,
                ),
                ft.DropdownOption(
                    "any",
                    _("Any"),
                    leading_icon=ft.Icons.FILE_COPY,
                ),
            ],
            label=_("Match Mode"),
            value=self.match_mode,
            on_select=self.on_match_mode_changed,
            align=ft.Alignment.TOP_LEFT,
            dense=True,
            expand=True,
            expand_loose=True,
        )

        self.require_listview = ft.ListView(
            expand=True,
            expand_loose=True,
            spacing=5,
            padding=ft.Padding.only(top=5),
            controls=[EntryListTile(self, name) for name in self.require],
        )

        controls = [
            self.mode_dropdown,
            EntryListTileControlBar(self),
            self.require_listview,
            # EditSectionEntriesControlBar(self),
        ]

        match self.entry_type:
            case "groups":
                title = _("Groups")
            case "rights":
                title = _("Rights")
            case _:
                raise ValueError(f"Invalid entry type '{self.entry_type}'")

        super().__init__(
            title=title,
            controls=controls,
            ref=ref,
            controls_padding=ft.Padding(top=15),
            expanded=True,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.PRIMARY),
        )

    async def on_match_mode_changed(self, event: ft.Event[ft.Dropdown]):
        self.match_mode = event.data
        # Sync data to parent editor immediately
        self.parent_edit_area.parent_collection_area.parent_edit_section.sync_data_to_parent()

    @property
    def dict_data(self) -> dict[str, Any]:
        return {
            "match": self.match_mode,
            "require": self.require,
        }


class SubRuleGroupEditArea(ft.ExpansionTile):
    def __init__(
        self,
        parent_collection_area: "SubRuleGroupCollectionArea",
        index: int,
        match_mode: str,
        match_groups: dict[str, Any],
        match_rights: dict[str, Any],
        ref: ft.Ref | None = None,
    ):

        self.page: ft.Page
        self.parent_collection_area = parent_collection_area
        self.index = index
        self.match_mode = match_mode
        self.match_groups = deepcopy(match_groups)
        self.match_rights = deepcopy(match_rights)

        # Create match mode dropdown
        self.match_mode_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption(
                    "all",
                    _("All (AND)"),
                    leading_icon=ft.Icons.SELECT_ALL,
                ),
                ft.DropdownOption(
                    "any",
                    _("Any (OR)"),
                    leading_icon=ft.Icons.FILE_COPY,
                ),
            ],
            label=_("Match Mode"),
            value=self.match_mode,
            on_select=self.on_match_mode_changed,
            dense=True,
            width=180,
        )

        # Create delete button
        self.delete_button = ft.IconButton(
            icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
            tooltip=_("Delete Subgroup"),
            on_click=self.on_delete_button_click,
        )

        # Create control bar
        control_bar = ft.Row(
            controls=[
                self.match_mode_dropdown,
                self.delete_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Add whitespace container around control bar for better visual spacing
        control_bar_container = ft.Container(
            content=control_bar,
            padding=ft.Padding(top=10, left=0, right=0, bottom=0),
        )

        controls: list = [control_bar_container]

        # Store references for dynamic addition
        self.rights_expansion_tile = None
        self.groups_expansion_tile = None

        if self.match_rights:  # handle rights
            rights_block_match_mode = self.match_rights.get("match", None)
            rights_block_require = self.match_rights.get("require", [])
            assert rights_block_match_mode is not None

            self.rights_expansion_tile = SubRuleGroupEditEntriesArea(
                self,
                "rights",
                rights_block_match_mode,
                rights_block_require,
            )
            controls.append(self.rights_expansion_tile)

        if self.match_groups:  # handle groups
            groups_block_match_mode = self.match_groups.get("match", None)
            groups_block_require = self.match_groups.get("require", [])
            assert groups_block_match_mode is not None

            self.groups_expansion_tile = SubRuleGroupEditEntriesArea(
                self,
                "groups",
                groups_block_match_mode,
                groups_block_require,
            )

            controls.append(self.groups_expansion_tile)

        # Add buttons for adding missing sections
        self.add_buttons_row = None
        add_buttons = []
        if not self.match_rights:
            self.add_rights_button = ft.OutlinedButton(
                content=_("Add Rights Section"),
                icon=ft.Icons.ADD,
                on_click=self.on_add_rights_section,
            )
            add_buttons.append(self.add_rights_button)
        else:
            self.add_rights_button = None
            
        if not self.match_groups:
            self.add_groups_button = ft.OutlinedButton(
                content=_("Add Groups Section"),
                icon=ft.Icons.ADD,
                on_click=self.on_add_groups_section,
            )
            add_buttons.append(self.add_groups_button)
        else:
            self.add_groups_button = None

        if add_buttons:
            self.add_buttons_row = ft.Row(
                controls=add_buttons,
                wrap=True,
                spacing=10,
            )
            controls.append(self.add_buttons_row)

        super().__init__(
            _("Subgroup #{index}").format(
                index=self.index,
            ),
            subtitle=_("Mode: {mode}").format(mode=self._get_display_mode()),
            controls=controls,
            expanded=True,
            ref=ref,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.SURFACE_CONTAINER),
        )

    def _get_display_mode(self) -> str:
        """Get user-friendly display name for match mode"""
        return _("All (AND)") if self.match_mode == "all" else _("Any (OR)")

    async def on_match_mode_changed(self, event: ft.Event[ft.Dropdown]):
        self.match_mode = event.data
        self.subtitle = _("Mode: {mode}").format(mode=self._get_display_mode())
        self.update()
        
        # Sync data to parent editor immediately
        self.parent_collection_area.parent_edit_section.sync_data_to_parent()

    async def on_add_rights_section(self, event: ft.Event[ft.OutlinedButton]):
        """Add a rights section to this subgroup"""
        if not self.match_rights:
            self.match_rights = {"match": "any", "require": []}
            self.rights_expansion_tile = SubRuleGroupEditEntriesArea(
                self,
                "rights",
                "any",
                [],
            )
            # Insert before the button row
            assert self.controls is not None
            self.controls.insert(-1, self.rights_expansion_tile)
            # Hide the add button
            if self.add_rights_button:
                self.add_rights_button.visible = False
            # Remove button row if both sections are added
            if self.add_buttons_row and self.match_groups:
                self.controls.remove(self.add_buttons_row)
                self.add_buttons_row = None
            self.update()
            
            # Sync data to parent editor immediately
            self.parent_collection_area.parent_edit_section.sync_data_to_parent()

    async def on_add_groups_section(self, event: ft.Event[ft.OutlinedButton]):
        """Add a groups section to this subgroup"""
        if not self.match_groups:
            self.match_groups = {"match": "any", "require": []}
            self.groups_expansion_tile = SubRuleGroupEditEntriesArea(
                self,
                "groups",
                "any",
                [],
            )
            # Insert before the button row
            assert self.controls is not None
            self.controls.insert(-1, self.groups_expansion_tile)
            # Hide the add button
            if self.add_groups_button:
                self.add_groups_button.visible = False
            # Remove button row if both sections are added
            if self.add_buttons_row and self.match_rights:
                self.controls.remove(self.add_buttons_row)
                self.add_buttons_row = None
            self.update()
            
            # Sync data to parent editor immediately
            self.parent_collection_area.parent_edit_section.sync_data_to_parent()

    async def on_delete_button_click(self, event: ft.Event[ft.IconButton]):
        # Remove this subgroup from the parent collection area
        assert self.parent_collection_area.controls is not None
        self.parent_collection_area.controls.remove(self)

        # Reindex remaining subgroups
        subgroup_index = 1
        for control in self.parent_collection_area.controls:
            if isinstance(control, SubRuleGroupEditArea):
                control.index = subgroup_index
                control.title = _("Subgroup #{index}").format(index=subgroup_index)
                subgroup_index += 1

        self.parent_collection_area.update()
        
        # Sync data to parent editor immediately
        self.parent_collection_area.parent_edit_section.sync_data_to_parent()

    def did_mount(self):
        super().did_mount()

    @property
    def dict_data(self) -> dict[str, Any]:
        assert type(self.controls) == list
        data: dict[str, Any] = {"match": self.match_mode}

        for control in self.controls:
            if isinstance(control, SubRuleGroupEditEntriesArea):
                data[control.entry_type] = control.dict_data
            # Skip control bars - they're not data

        return data


class SubRuleGroupCollectionArea(ft.ExpansionTile):
    def __init__(
        self,
        index: int,
        match_mode: str,
        match_groups: list[dict],
        parent_edit_section: "VisualRuleEditorEditSection",
        ref: ft.Ref | None = None,
    ):
        self.page: ft.Page
        self.parent_edit_section = parent_edit_section
        self.index = index
        self.match_mode = match_mode

        # Create match mode dropdown
        self.match_mode_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption(
                    "all",
                    _("All (AND)"),
                    leading_icon=ft.Icons.SELECT_ALL,
                ),
                ft.DropdownOption(
                    "any",
                    _("Any (OR)"),
                    leading_icon=ft.Icons.FILE_COPY,
                ),
            ],
            label=_("Match Mode"),
            value=self.match_mode,
            on_select=self.on_match_mode_changed,
            dense=True,
            width=180,
        )

        # Create delete button
        self.delete_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            tooltip=_("Delete Rule Group"),
            on_click=self.on_delete_button_click,
        )

        # Create control bar at the top
        self.top_control_bar = ft.Row(
            controls=[
                self.match_mode_dropdown,
                self.delete_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Add whitespace container around control bar for better visual spacing
        top_control_bar_container = ft.Container(
            content=self.top_control_bar,
            padding=ft.Padding(top=10, left=0, right=0, bottom=0),
        )

        # Initialize controls list with control bar and SubRuleGroupControlBar
        controls = [
            top_control_bar_container,
            SubRuleGroupControlBar(self),
        ]

        for group_index, subgroup in enumerate(match_groups):
            subgroup_match_mode: Optional[str] = subgroup.get("match", None)
            subgroup_rights_block: dict = subgroup.get("rights", {})
            subgroup_groups_block: dict = subgroup.get("groups", {})
            assert subgroup_match_mode is not None

            subgroup_expansion_tile = SubRuleGroupEditArea(
                self,
                group_index + 1,
                subgroup_match_mode,
                subgroup_groups_block,
                subgroup_rights_block,
            )

            controls.append(subgroup_expansion_tile)

        super().__init__(
            title=_("Rule Group #{index}").format(
                index=index + 1,
            ),
            subtitle=_("Mode: {mode}").format(mode=self._get_display_mode()),
            expanded=not index,
            expand=True,
            expand_loose=True,
            align=ft.Alignment.TOP_CENTER,
            ref=ref,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.SURFACE_CONTAINER_HIGHEST),
            controls=controls,
        )

    def _get_display_mode(self) -> str:
        """Get user-friendly display name for match mode"""
        return _("All (AND)") if self.match_mode == "all" else _("Any (OR)")

    async def on_match_mode_changed(self, event: ft.Event[ft.Dropdown]):
        self.match_mode = event.data
        self.subtitle = _("Mode: {mode}").format(mode=self._get_display_mode())
        self.update()
        
        # Sync data to parent editor immediately
        self.parent_edit_section.sync_data_to_parent()

    async def on_delete_button_click(self, event: ft.Event[ft.IconButton]):
        # Remove this rule group from the parent collection
        parent_column = self.parent_edit_section.collection_areas_column
        parent_column.controls.remove(self)

        # Reindex remaining rule groups by counting only SubRuleGroupCollectionArea instances
        rule_group_index = 0
        for control in parent_column.controls:
            if isinstance(control, SubRuleGroupCollectionArea):
                control.index = rule_group_index
                control.title = _("Rule Group #{index}").format(index=rule_group_index + 1)
                rule_group_index += 1

        parent_column.update()
        
        # Sync data to parent editor immediately
        self.parent_edit_section.sync_data_to_parent()

    @property
    def dict_data(self) -> list[dict[str, Any]]:
        assert type(self.controls) == list
        data: list[dict[str, Any]] = []

        for control in self.controls:
            if isinstance(control, SubRuleGroupEditArea):
                data.append(control.dict_data)
            # Skip control bars - they're not data

        return data


class VisualRuleEditorEditSection(ft.Column):
    def __init__(
        self,
        parent_editor: "VisualRuleEditor",
        access_type: str,
        ref: ft.Ref | None = None,
    ):
        super().__init__(ref=ref, expand=True, expand_loose=True)
        self.page: ft.Page
        self.parent_editor = parent_editor
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.scroll = ft.ScrollMode.AUTO
        self.access_type = access_type  # "read", "write", "move", "manage"

        self.collection_areas_column = CollectionAreasColumn(self)
        self.controls = [self.collection_areas_column]

    async def load_rules(self):
        # clear existing controls but preserve the control bar
        control_bar = None
        for control in self.collection_areas_column.controls:
            if isinstance(control, CollectionAreasControlBar):
                control_bar = control
                break

        self.collection_areas_column.controls.clear()

        async def parse_sub_rules(
            match_mode: str, match_groups: list[dict], index
        ) -> SubRuleGroupCollectionArea:

            return SubRuleGroupCollectionArea(
                index,
                match_mode,
                match_groups,
                self,
            )

        rules: list[dict] = self.parent_editor.edited_rule_data.get(
            self.access_type, []
        )

        for index, rule in enumerate(rules):
            match_mode = rule.get("match", None)
            match_groups = rule.get("match_groups", [])
            assert match_mode is not None

            # get ExpansionTile for this rule
            new_rule_tile = await parse_sub_rules(match_mode, match_groups, index)
            self.collection_areas_column.controls.append(new_rule_tile)

        # Re-add the control bar at the end
        if control_bar:
            self.collection_areas_column.controls.append(control_bar)

        self.update()

    def did_mount(self):
        super().did_mount()
        self.page.run_task(self.load_rules)

    def sync_data_to_parent(self):
        """Sync current edit section data to parent editor immediately"""
        self.parent_editor.edited_rule_data[self.access_type] = self.dict_data

    def will_unmount(self):
        super().will_unmount()
        self.sync_data_to_parent()

    @property
    def dict_data(self) -> list[dict[str, Any]]:
        data: list[dict[str, Any]] = []

        for control in self.collection_areas_column.controls:
            if isinstance(control, SubRuleGroupCollectionArea):
                data.append(
                    {
                        "match": control.match_mode,
                        "match_groups": control.dict_data,
                    }
                )
            # Skip CollectionAreasControlBar - it's not data

        return data


class VisualRuleEditorNavigationRail(ft.NavigationRail):
    def __init__(self, parent_editor: "VisualRuleEditor", ref: ft.Ref | None = None):
        super().__init__(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=400,
            group_alignment=0.0,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.PAGEVIEW_OUTLINED,
                    selected_icon=ft.Icons.PAGEVIEW,
                    label=_("Read"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.EDIT_OUTLINED),
                    selected_icon=ft.Icon(ft.Icons.EDIT),
                    label=_("Write"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.DRIVE_FILE_MOVE_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.DRIVE_FILE_MOVE),
                    label=_("Move"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.MANAGE_ACCOUNTS_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.MANAGE_ACCOUNTS),
                    label=_("Manage"),
                ),
            ],
            ref=ref,
        )
        self.parent_editor = parent_editor
        self.on_change = self.handle_navigation_change

    async def handle_navigation_change(self, event: ft.Event[ft.NavigationRail]):
        match self.selected_index:
            case 0:  # Read
                mode = "read"
            case 1:  # Write
                mode = "write"
            case 2:  # Move
                mode = "move"
            case 3:  # Manage
                mode = "manage"
            case _:
                raise ValueError("Invalid navigation index")

        self.parent_editor.current_edit_section_container.content = (
            VisualRuleEditorEditSection(self.parent_editor, mode)
        )
        self.update()
