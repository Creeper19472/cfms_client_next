# FileBrowserDialog - Unified File and Directory Browser

## Overview

The `FileBrowserDialog` provides a unified, configurable interface for browsing and selecting files and/or directories in the CFMS Client NEXT application. It replaces three previous separate implementations with a single flexible component.

## Location

`src/include/ui/controls/dialogs/file_browser.py`

## Replaced Implementations

This unified dialog replaces:
1. The original `DocumentSelectorDialog` implementation (~296 lines)
2. The original `DirectorySelectorDialog` implementation (~275 lines) 
3. The original `MoveDialog` implementation (~361 lines)

## Features

- **Flexible Mode Selection**: Choose to show files only, directories only, or both
- **File Filtering**: Optional custom filter function for files (e.g., image files only)
- **Directory Exclusion**: Exclude specific directories from display (e.g., prevent moving into self)
- **Optional Selection Button**: Show a "Select Here" button for selecting the current directory
- **Breadcrumb Navigation**: Display current path with navigation stack
- **Async Loading**: Asynchronous directory loading with progress indicators
- **Async Wait Pattern**: Support for awaiting user selection

## Usage Examples

### Example 1: Image Document Selector

Select image documents for avatar setting:

```python
from include.ui.controls.dialogs.document_selector import DocumentSelectorDialog

def on_document_selected(document_id: str, document_name: str):
    print(f"Selected: {document_name} (ID: {document_id})")

selector = DocumentSelectorDialog(on_select_callback=on_document_selected)
page.show_dialog(selector)
```

### Example 2: Directory Selector

Select a target directory for batch operations:

```python
from include.ui.controls.dialogs.explorer import DirectorySelectorDialog

selector = DirectorySelectorDialog(
    file_listview=file_manager_view,
    excluded_directory_ids=["dir1", "dir2"],  # Exclude these directories
)

page.show_dialog(selector)

# Wait for selection
target_dir = await selector.wait_for_selection()
if target_dir:
    print(f"Selected directory: {target_dir}")
```

### Example 3: Move Dialog

Move documents or directories to a new location:

```python
from include.ui.controls.dialogs.contextmenu.move import MoveDialog

move_dialog = MoveDialog(
    object_type="document",  # or "directory"
    object_id="doc123",
    file_listview=file_list_view,
)

page.show_dialog(move_dialog)
```

### Example 4: Custom File Browser

Create a custom browser with specific requirements:

```python
from include.ui.controls.dialogs.file_browser import FileBrowserDialog

def pdf_filter(filename: str) -> bool:
    """Only show PDF files."""
    return filename.lower().endswith('.pdf')

def on_select(item_id: str, item_name: str, item_type: str):
    print(f"Selected {item_type}: {item_name}")

browser = FileBrowserDialog(
    title="Select PDF Document",
    on_select_callback=on_select,
    initial_directory_id=None,  # Start at root
    mode="files",  # Only show files
    file_filter=pdf_filter,
    show_select_button=False,
)

page.show_dialog(browser)
```

## Configuration Options

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | str | "Browse Files and Directories" | Dialog title |
| `on_select_callback` | Callable | None | Callback(item_id, item_name, item_type) when item selected |
| `initial_directory_id` | str \| None | None | Starting directory (None = root) |
| `mode` | str | "both" | Selection mode: "files", "directories", or "both" |
| `file_filter` | Callable | None | Function(filename) -> bool to filter files |
| `excluded_directory_ids` | list[str] | [] | Directory IDs to exclude from display |
| `show_select_button` | bool | False | Show button to select current directory |
| `select_button_text` | str | "Select Here" | Text for select button |
| `select_button_icon` | ft.IconData | ft.Icons.CHECK_CIRCLE | Icon for select button |
| `show_breadcrumb` | bool | True | Show breadcrumb path (only shows when path can be fully constructed) |
| `ref` | ft.Ref | None | Flet reference |
| `visible` | bool | True | Initial visibility |

### Mode Options

- **`"files"`**: Show only files (and navigation controls)
- **`"directories"`**: Show only directories (folders)
- **`"both"`**: Show both files and directories (default)

### Breadcrumb Display Behavior

The breadcrumb path indicator (`show_breadcrumb`) has intelligent display logic to ensure accuracy:

- **At root**: Always shows "/" (complete path known)
- **Started from root, then navigated**: Shows constructed path like "/folder1/folder2" (complete path known from navigation history)
- **Opened in subdirectory**: Shows "(current directory)" for all locations (incomplete path - only current location known, not full path from root)
  - This applies even when navigating deeper from the subdirectory
  - Example: Open in `/unknown/path/` → navigate to `folder3` → still shows "(current directory)" because we don't know the full path is `/unknown/path/folder3/`

This prevents showing inaccurate path information when the dialog is opened directly in a subdirectory. The dialog tracks whether it started from root to determine if it can show complete paths.

## Architecture

### Class Hierarchy

```
AlertDialog (Flet base)
    └── FileBrowserDialog (unified base)
            ├── DocumentSelectorDialog (image file selector)
            ├── DirectorySelectorDialog (directory picker)
            └── MoveDialog (move operation dialog)
```

### Key Methods

#### Public Methods

- **`did_mount()`**: Called when dialog is mounted; loads initial directory
- **`disable_interactions()`**: Disable UI during async operations
- **`enable_interactions()`**: Re-enable UI after async operations
- **`wait_for_selection()`**: Async method to wait for user selection

#### Internal Methods

- **`load_directory(directory_id)`**: Load and display directory contents
- **`navigate_to_directory(dir_id, dir_name)`**: Navigate into subdirectory
- **`go_to_parent_click(event)`**: Navigate to parent directory
- **`go_to_root_button_click(event)`**: Navigate to root
- **`select_file(file_id, file_name)`**: Handle file selection
- **`select_here_button_click(event)`**: Handle directory selection

## Extending FileBrowserDialog

To create a specialized dialog, extend `FileBrowserDialog`:

```python
class MyCustomDialog(FileBrowserDialog):
    def __init__(self, custom_param, **kwargs):
        # Configure parent with appropriate settings
        super().__init__(
            title="My Custom Browser",
            mode="files",
            file_filter=my_filter_function,
            **kwargs
        )
        
        # Add custom behavior
        self.custom_param = custom_param
    
    def select_file(self, file_id: str, file_name: str):
        # Override to add custom behavior
        # ... custom logic ...
        super().select_file(file_id, file_name)
```

## Migration Guide

### From Old DocumentSelectorDialog

**Before:**
```python
dialog = DocumentSelectorDialog(on_select_callback=callback)
```

**After:** (No change - wrapper provides backward compatibility)
```python
dialog = DocumentSelectorDialog(on_select_callback=callback)
```

### From Old DirectorySelectorDialog

**Before:**
```python
dialog = DirectorySelectorDialog(
    file_listview=view,
    excluded_directory_ids=excluded
)
target = await dialog.wait_for_selection()
```

**After:** (No change - extends FileBrowserDialog directly)
```python
dialog = DirectorySelectorDialog(
    file_listview=view,
    excluded_directory_ids=excluded
)
target = await dialog.wait_for_selection()
```

### From Old MoveDialog

**Before:**
```python
dialog = MoveDialog(
    object_type="document",
    object_id="123",
    file_listview=view
)
```

**After:** (No change - extends FileBrowserDialog)
```python
dialog = MoveDialog(
    object_type="document",
    object_id="123",
    file_listview=view
)
```

## Benefits

1. **Code Reusability**: ~600 lines of duplicated code eliminated
2. **Maintainability**: Single source of truth for browser logic
3. **Consistency**: All dialogs share the same UI/UX patterns
4. **Extensibility**: Easy to create new specialized browsers
5. **Testing**: One component to test instead of three

## Implementation Details

### Directory Loading

The dialog loads directory contents asynchronously using the `do_request` API:

```python
response = await do_request(
    action="list_directory",
    data={"folder_id": directory_id},
    username=self.app_shared.username,
    token=self.app_shared.token,
)
```

### Navigation Stack

A breadcrumb navigation stack tracks the path:

```python
self.navigation_stack: list[tuple[Optional[str], str]] = []
# Format: [(directory_id, directory_name), ...]
```

### Selection Patterns

Two patterns are supported:

1. **Callback Pattern**: Provide `on_select_callback`
2. **Async Wait Pattern**: Use `wait_for_selection()` with `selection_event`

## Future Enhancements

Potential improvements:
- Search functionality within directories
- Sort order customization (by name, date, size)
- Multi-selection support
- Favorites/bookmarks
- Recent locations history
- Grid view option

## See Also

- `AlertDialog` base class: `src/include/ui/controls/dialogs/base.py`
- File utilities: `src/include/ui/util/file_controls.py`
- Path utilities: `src/include/ui/util/path.py`
