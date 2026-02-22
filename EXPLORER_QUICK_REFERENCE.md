# File Explorer Quick Reference Card

## 🗂️ Key Files at a Glance

| File | Purpose | Lines | Pattern |
|------|---------|-------|---------|
| `include/ui/controls/views/explorer.py` | Main view (FileManagerView, FileListView) | 283 | Declarative structure |
| `include/controllers/explorer/itself.py` | Main controller (FileExplorerController) | 858 | Imperative logic |
| `include/ui/util/file_controls.py` | ⚠️ **CRITICAL** - List rebuilder | 127 | Imperative rebuild |
| `include/ui/controls/components/explorer/tile.py` | FileTile, DirectoryTile | 247 | Declarative components |
| `include/ui/controls/components/explorer/bar.py` | Toolbars (Top, Selection, Sort) | 302 | Declarative components |
| `include/ui/controls/contextmenus/explorer.py` | Context menus | 301 | Declarative with permissions |
| `include/util/batch_operations.py` | Batch operations (delete/download/move) | - | Async generators |

## 🔑 Key Classes

```python
# Main View
FileManagerView(ft.Container)
  ├── FilePathIndicator(ft.Column)          # Breadcrumb
  ├── ExplorerTopBar(ft.Row)                # Action buttons
  ├── SelectionToolbar(ft.Row)              # Batch operations
  ├── FileSortBar(ft.Row)                   # Sort controls
  └── FileListView(ft.ListView)             # File list

# Controllers
Controller[T]                                # Generic base
  ├── FileExplorerController                # Main (858 lines)
  ├── FileContextMenuController             # File actions
  ├── DirectoryContextMenuController        # Directory actions
  └── FileSortBarController                 # Sorting

# Components (Two Modes)
Normal Mode:
  ├── FileContextMenu(ContextMenu2)         # With right-click menu
  └── DirectoryContextMenu(ContextMenu2)    # With right-click menu

Selection Mode:
  ├── FileTile(ft.ListTile)                 # With checkbox
  └── DirectoryTile(ft.ListTile)            # With checkbox
```

## 🎯 Critical Function

```python
# Location: include/ui/util/file_controls.py
def update_file_controls(view, folders, documents, parent_id):
    """⚠️ DESTROYS AND RECREATES ALL LIST WIDGETS"""
    view.controls = []          # Destroy all
    # Build parent button
    # Build directory items
    # Build file items
    view.update()               # Force refresh
```

**Called by**: Navigation, sorting, mode toggle, refresh  
**Problem**: No widget reuse, loses UI state

## 📊 State Management

```python
# FileListView State
current_parent_id: str | None
current_files_data: list[dict]              # From server
current_directories_data: list[dict]        # From server

# Selection State
selection_mode: bool = False
selected_file_ids: set[str] = set()
selected_directory_ids: set[str] = set()

# FileManagerView State
root_directory_id: str | None
current_directory_id: str | None
previous_directory_id: str | None
conn: ClientConnection
```

## 🔄 Data Flow

```
1. User Action
   ↓
2. Controller Method (async)
   ↓
3. get_directory(id, view) or do_request()
   ↓
4. WebSocket Request → Server
   ↓
5. Response: {folders: [...], documents: [...]}
   ↓
6. Store in view.current_*_data
   ↓
7. update_file_controls(view, folders, documents)
   ↓
8. Destroy all widgets (view.controls = [])
   ↓
9. Create new widgets from data
   ↓
10. view.update() → UI Refresh
```

## 🎨 Two Rendering Modes

### Normal Mode
```python
# Wrapped in ContextMenu2
for folder in folders:
    DirectoryContextMenu(
        directory_id=folder["id"],
        dir_name=folder["name"],
        ...
    )
```
- Right-click menus
- Star/favorite button
- Permission-filtered actions

### Selection Mode
```python
# Direct tiles with checkboxes
for folder in folders:
    DirectoryTile(
        directory_id=folder["id"],
        selection_mode=True,
        is_selected=folder["id"] in selected_ids,
        on_selection_changed=callback,
        ...
    )
```
- Checkboxes visible
- Batch operations toolbar
- Click toggles selection

## 🛡️ Permission System

```python
# Menu item definition
{
    "icon": ft.Icons.DELETE,
    "content": "Delete",
    "on_click": handler,
    "require": {"delete_document"}  # ← Checked at runtime
}

# Filtered by ContextMenu2._build_controls()
if item["require"].issubset(app_shared.user_permissions):
    # Show menu item
else:
    # Hide menu item
```

## 🔢 Batch Operations

```python
# All return async generators
batch_delete_items(file_ids, directory_ids, cancel_event)
    # Yields: (type, id, success, error_msg)

batch_download_items(file_items, dir_items, save_path, cancel_event)
    # Yields: (type, name, current_file, success, error_msg)

batch_move_items(file_ids, directory_ids, target_id, cancel_event)
    # Yields: (type, id, success, error_msg)
```

**Features**: Progress tracking, cancellation, error collection

## 🎛️ Controller Actions

### FileExplorerController (Main)
```python
action_upload(files)                    # Upload files
action_directory_upload(root_path)      # Upload directory tree
action_batch_delete()                   # Delete selected
action_batch_download()                 # Download selected
action_batch_move()                     # Move selected
```

### FileContextMenuController
```python
action_open_file()                      # Download file
action_delete_file()                    # Delete file
action_rename_file()                    # Rename dialog
action_move_file()                      # Move dialog
action_authorize()                      # Permissions dialog
action_view_access_entries()            # View permissions
action_set_access_rules()               # Rule manager
action_upload_new_revision()            # Upload new version
action_view_revisions()                 # Revision history
action_open_document_info()             # Properties dialog
```

### DirectoryContextMenuController
```python
action_open_directory()                 # Navigate into
action_delete_directory()               # Delete directory
action_rename_directory()               # Rename dialog
action_move_directory()                 # Move dialog
action_authorize()                      # Permissions dialog
action_view_access_entries()            # View permissions
action_set_access_rules()               # Rule manager
action_open_directory_info()            # Properties dialog
```

## 🔧 Common Patterns

### Async Task Execution
```python
# From UI component
self.page.run_task(self.controller.action_method, args)
```

### Error Handling
```python
response = await do_request(action, data, username, token)
if response["code"] == 403:
    # Show AccessDeniedDialog or AccessDeniedView
elif response["code"] != 200:
    # Show error snackbar
```

### Progress Dialog
```python
from include.ui.controls.dialogs.wait import wait

@wait("operation_name")
async def action_method(self):
    async for current, total in operation():
        # Progress tracked by decorator
        pass
```

### Visibility Toggle
```python
self.component.visible = False
self.other_component.visible = True
self.component.update()
self.other_component.update()
```

## 📦 Import Patterns

```python
# Standard imports
import flet as ft
from typing import TYPE_CHECKING
from include.classes.shared import AppShared
from include.controllers.base import Controller
from include.util.locale import get_translation

# Circular import prevention
if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileListView

# Localization
t = get_translation()
_ = t.gettext
```

## ⚠️ Known Issues

1. **Widget Destruction** - `update_file_controls()` destroys all on every update
2. **No Tests** - Zero test coverage
3. **Large Controller** - `itself.py` is 858 lines
4. **Manual State Sync** - Visibility flags manually toggled
5. **No Widget Pooling** - No reuse, creates new widgets each time
6. **Scroll Position Lost** - On refresh/sort/mode change

## 🎯 Quick Fix Locations

| Issue | File | Function/Class |
|-------|------|----------------|
| Widget destruction | `file_controls.py` | `update_file_controls()` |
| Large controller | `explorer/itself.py` | `FileExplorerController` |
| Manual visibility | `explorer/bar.py` | Various toolbar methods |
| State management | `views/explorer.py` | `FileListView`, `FileManagerView` |

## 📝 Quick Commands

```bash
# Find explorer files
cd src && find . -path "*explorer*" -name "*.py"

# Count lines in main controller
wc -l include/controllers/explorer/itself.py

# Search for update_file_controls usage
grep -r "update_file_controls" --include="*.py"

# Find all controllers
find . -path "*/controllers/*.py" -type f
```

## 🚀 Refactoring Priorities

1. ⭐⭐⭐ Add unit tests
2. ⭐⭐⭐ Extract `update_file_controls()` to class method
3. ⭐⭐ Split `FileExplorerController` into smaller controllers
4. ⭐⭐ Implement widget pooling
5. ⭐ Add state preservation for scroll position
6. ⭐ Document imperative patterns

---

**Pattern Summary**: Imperative-heavy hybrid with declarative components  
**Critical Function**: `update_file_controls()` in `file_controls.py`  
**Main Controller**: `FileExplorerController` (858 lines)  
**Test Coverage**: 0% ❌

**For detailed documentation, see**:
- `EXPLORER_STRUCTURE_ANALYSIS.md` - Complete analysis
- `EXPLORER_COMPONENT_DIAGRAM.md` - Visual diagrams  
- `EXPLORER_ANALYSIS_SUMMARY.md` - Executive summary
