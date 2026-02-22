# Explorer Package Documentation

## Package Overview

The `include.ui.controls.explorer` package contains all file explorer UI components for CFMS Client NEXT. This package was created to consolidate explorer-related code that was previously scattered across multiple directories.

## Package Structure

```
include/ui/controls/explorer/
├── __init__.py              # Package initialization
├── view.py                  # Main explorer views
├── file_controls.py         # File control utilities
├── path.py                  # Path navigation utilities
├── contextmenus.py          # Context menu implementations
└── components/              # Sub-components
    ├── __init__.py
    ├── bar.py               # Toolbar components
    ├── tile.py              # List tile components
    └── access_denied.py     # Access denied view
```

## Core Modules

### view.py
**Purpose**: Main explorer view components

**Classes**:
- `FilePathIndicator` - Displays and manages the current directory path
- `FileListView` - ListView for displaying files and directories
- `FileManagerView` - Main container for the file explorer

**Usage**:
```python
from include.ui.controls.explorer.view import FileManagerView, FileListView

# Create a file manager view
file_manager = FileManagerView(parent_model=home_model)
```

### file_controls.py
**Purpose**: Utilities for updating and managing file list controls

**Functions**:
- `update_file_controls(view, folders, documents, parent_id)` - Updates the file list view with new data

**Usage**:
```python
from include.ui.controls.explorer.file_controls import update_file_controls

update_file_controls(
    view=file_listview,
    folders=directories_data,
    documents=files_data,
    parent_id=current_parent_id
)
```

### path.py
**Purpose**: Path navigation and file operations

**Functions**:
- `get_directory(id, view, fallback, _raise_on_error, _set_new_root)` - Loads and displays a directory
- `get_document(id, filename, page)` - Downloads a file

**Usage**:
```python
from include.ui.controls.explorer.path import get_directory, get_document

# Navigate to a directory
await get_directory(directory_id, file_listview)

# Download a file
await get_document(file_id, filename, page)
```

### contextmenus.py
**Purpose**: Context menu implementations for files and directories

**Classes**:
- `FileContextMenu` - Context menu for file operations
- `DirectoryContextMenu` - Context menu for directory operations

**Usage**:
```python
from include.ui.controls.explorer.contextmenus import FileContextMenu

# Context menus are created internally by update_file_controls()
```

## Component Modules

### components/bar.py
**Purpose**: Toolbar and action bar components

**Classes**:
- `ExplorerTopBar` - Main toolbar with action buttons
- `FileSortBar` - Sorting controls
- `SelectionToolbar` - Toolbar for batch operations

**Usage**:
```python
from include.ui.controls.explorer.components.bar import ExplorerTopBar

top_bar = ExplorerTopBar(parent_view=file_manager)
```

### components/tile.py
**Purpose**: List tile components for files and directories

**Classes**:
- `FileTile` - List tile for file items
- `DirectoryTile` - List tile for directory items

**Usage**:
```python
from include.ui.controls.explorer.components.tile import FileTile, DirectoryTile

file_tile = FileTile(
    filename="document.pdf",
    file_id="123",
    size=1024,
    last_modified=1234567890,
    starred=False
)
```

### components/access_denied.py
**Purpose**: View displayed when directory access is denied

**Classes**:
- `AccessDeniedView` - Full-screen access denied message

**Usage**:
```python
from include.ui.controls.explorer.components.access_denied import AccessDeniedView

# Created internally by FileManagerView when access is denied
access_denied = AccessDeniedView(parent_manager=file_manager, reason="...")
```

## Common Usage Patterns

### Loading a Directory
```python
from include.ui.controls.explorer.path import get_directory

# Basic usage
success = await get_directory(directory_id, file_listview)

# With fallback
success = await get_directory(
    id=directory_id,
    view=file_listview,
    fallback=parent_directory_id,
    _raise_on_error=True
)
```

### Updating the File List
```python
from include.ui.controls.explorer.file_controls import update_file_controls

# Update with new data
update_file_controls(
    view=file_listview,
    folders=[{"id": "123", "name": "Documents", ...}],
    documents=[{"id": "456", "title": "file.pdf", ...}],
    parent_id=current_parent_id
)
```

### Sorting Files
```python
from include.classes.ui.enum import SortMode, SortOrder

# Sort files by name ascending
file_listview.sort_files(
    sort_mode=SortMode.BY_NAME,
    sort_order=SortOrder.ASCENDING
)

# Sort files by size descending
file_listview.sort_files(
    sort_mode=SortMode.BY_SIZE,
    sort_order=SortOrder.DESCENDING
)
```

### Selection Mode
```python
# Enable selection mode
file_listview.toggle_selection_mode(True)

# Select all items
file_listview.select_all()

# Get selected count
count = file_listview.get_selected_count()

# Clear selections
file_listview.clear_selection()

# Disable selection mode
file_listview.toggle_selection_mode(False)
```

## Integration with Controllers

Controllers should import from the explorer package:

```python
# In controllers/explorer/itself.py
from include.ui.controls.explorer.path import get_directory
from include.ui.controls.explorer.view import FileManagerView

# In controllers/explorer/tile.py
from include.ui.controls.explorer.path import get_directory, get_document
from include.ui.controls.explorer.contextmenus import FileContextMenu, DirectoryContextMenu
```

## TYPE_CHECKING Imports

To avoid circular dependencies, use TYPE_CHECKING imports:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from include.ui.controls.explorer.view import FileListView
    from include.ui.controls.explorer.view import FileManagerView
```

## Migration Guide

If you have old code using the previous import paths, update them as follows:

### Old Imports → New Imports

```python
# OLD
from include.ui.controls.views.explorer import FileManagerView
from include.ui.util.path import get_directory
from include.ui.util.file_controls import update_file_controls
from include.ui.controls.contextmenus.explorer import FileContextMenu
from include.ui.controls.components.explorer.bar import ExplorerTopBar
from include.ui.controls.components.explorer.tile import FileTile

# NEW
from include.ui.controls.explorer.view import FileManagerView
from include.ui.controls.explorer.path import get_directory
from include.ui.controls.explorer.file_controls import update_file_controls
from include.ui.controls.explorer.contextmenus import FileContextMenu
from include.ui.controls.explorer.components.bar import ExplorerTopBar
from include.ui.controls.explorer.components.tile import FileTile
```

## Dependencies

The explorer package depends on:
- `flet` (UI framework)
- `include.classes.shared.AppShared` (application state)
- `include.ui.util.notifications` (user notifications)
- `include.util.requests` (server communication)
- `include.controllers.explorer.*` (business logic)

## Architecture Notes

### Separation of Concerns
- **Views** (`view.py`): UI structure and layout
- **Controllers** (`include.controllers.explorer.*`): Business logic
- **Utilities** (`file_controls.py`, `path.py`): Helper functions
- **Components** (`components/`): Reusable UI elements

### State Management
State is managed by:
1. `FileListView` - Current file list state, selection state
2. `FileManagerView` - Current directory, root directory
3. `AppShared` - Global application state

### Event Flow
1. User interaction → Component event handler
2. Event handler → Controller action (via `page.run_task()`)
3. Controller → Server request (via `do_request()`)
4. Controller → Update view (via utility functions)
5. View updates → UI refresh

## Testing Considerations

When testing explorer functionality:
1. Mock `AppShared` for application state
2. Mock `do_request()` for server communication
3. Use `FileListView` directly for unit tests
4. Use `FileManagerView` for integration tests

## Future Enhancements

Potential improvements:
- [ ] Add drag-and-drop file upload support
- [ ] Implement virtual scrolling for large directories
- [ ] Add file preview functionality
- [ ] Implement breadcrumb navigation
- [ ] Add keyboard shortcuts for common operations
- [ ] Implement directory tree view

## Related Documentation

- Main UI documentation: `docs/UI_ARCHITECTURE.md`
- Controller patterns: `docs/CONTROLLER_PATTERNS.md`
- State management: `docs/STATE_MANAGEMENT.md`

## Questions?

For questions about this package, see:
- `REFACTORING_SUMMARY.md` - High-level overview of the refactoring
- `REFACTORING_CHANGES.md` - Detailed file-by-file changes
- Source code comments in individual modules
