# Multi-Select and Batch Operations Implementation

## Overview

This document describes the complete implementation of multi-select functionality with batch download and delete operations for the CFMS Client NEXT file explorer.

## Features Implemented

### 1. Multi-Select Infrastructure

**FileListView** (`src/include/ui/controls/views/explorer.py`):
- Added `selection_mode: bool` flag to track selection mode state
- Added `selected_file_ids: set[str]` to track selected files
- Added `selected_directory_ids: set[str]` to track selected directories
- Methods:
  - `toggle_selection_mode(enabled: bool)` - Enable/disable selection mode
  - `select_all()` - Select all files and directories
  - `clear_selection()` - Clear all selections
  - `toggle_file_selection(file_id: str)` - Toggle individual file selection
  - `toggle_directory_selection(directory_id: str)` - Toggle individual directory selection
  - `get_selected_count() -> int` - Get total count of selected items

### 2. Selection Toolbar

**SelectionToolbar** (`src/include/ui/controls/components/explorer/bar.py`):
- New component that appears when selection mode is active
- Buttons:
  - **Select All** - Selects all items in current directory
  - **Clear** - Clears all selections
  - **Download** - Batch download selected items
  - **Delete** - Batch delete selected items
  - **Cancel** - Exit selection mode
- Dynamic selection count display (e.g., "5 items selected")
- Automatically updates count when selections change

### 3. Checkbox Support in Tiles

**FileTile** (`src/include/ui/controls/components/explorer/tile.py`):
- Added `selection_mode: bool` parameter
- Added `is_selected: bool` parameter
- Added `on_selection_changed: callable` callback
- Shows checkbox instead of file icon when in selection mode
- Clicking tile in selection mode toggles checkbox
- Checkbox changes trigger callback to update selection state

**DirectoryTile** (same file):
- Same functionality as FileTile
- Shows checkbox instead of folder icon in selection mode

### 4. UI Integration

**ExplorerTopBar** (`src/include/ui/controls/components/explorer/bar.py`):
- Added selection mode toggle button (checkbox icon)
- Toggle button:
  - Visible in normal mode
  - Hidden when selection mode is active
  - Icon: `ft.Icons.CHECKLIST`
  - Tooltip: "Select items"

**FileManagerView** (`src/include/ui/controls/views/explorer.py`):
- Added `selection_toolbar` component
- Integrated into view layout between top bar and divider
- Toolbar visibility controlled by selection mode state

**file_controls.py** (`src/include/ui/util/file_controls.py`):
- Updated `update_file_controls()` to support selection mode
- When `selection_mode=True`:
  - Creates tiles directly without context menus
  - Passes selection state and callbacks to tiles
  - Updates selection toolbar count on changes
- When `selection_mode=False`:
  - Uses normal context menu wrappers
  - Standard file/directory interaction

### 5. Batch Delete Operation

**FileExplorerController.action_batch_delete()** (`src/include/controllers/explorer/itself.py`):
- Shows confirmation dialog with item counts
- Uses `BatchDeleteConfirmDialog` for user confirmation
- Displays progress dialog during deletion
- Sequential processing with error handling
- Continues on per-item errors
- Collects and displays failures at end
- Refreshes directory after completion
- Exits selection mode automatically

**BatchDeleteConfirmDialog** (`src/include/ui/controls/dialogs/explorer.py`):
- Shows counts: "Delete 5 items (3 files, 2 directories)?"
- Warning: "This action cannot be undone."
- Delete/Cancel buttons
- Async wait for user confirmation

**batch_delete_items()** (`src/include/util/batch_operations.py`):
- Async generator yielding progress updates
- Deletes files first, then directories
- Yields: `(item_type, item_id, success, error_message)`
- Error handling per item
- Continues on failures

### 6. Batch Download Operation

**FileExplorerController.action_batch_download()** (`src/include/controllers/explorer/itself.py`):
- Prompts user to select download directory
- Shows progress dialog with current file being downloaded
- Downloads files and directories with structure preservation
- Error handling per file/directory
- Displays completion summary
- Exits selection mode automatically

**batch_download_items()** (`src/include/util/batch_operations.py`):
- Async generator for progress tracking
- Downloads individual files directly
- Recursively downloads directories maintaining structure
- Creates local directory structure matching server
- Yields: `(item_type, item_name, current_file, success, error_message)`
- Uses existing server API calls:
  - `download_document` - Get download task
  - `list_files` - List directory contents
  - `download_file_from_server` - Transfer file

## File Structure

```
src/include/
├── util/
│   └── batch_operations.py          (NEW) - Batch operation utilities
├── ui/
│   ├── controls/
│   │   ├── views/
│   │   │   └── explorer.py          (MODIFIED) - Added selection state
│   │   ├── components/explorer/
│   │   │   ├── bar.py               (MODIFIED) - Added SelectionToolbar
│   │   │   └── tile.py              (MODIFIED) - Added checkbox support
│   │   └── dialogs/
│   │       └── explorer.py          (MODIFIED) - Added BatchDeleteConfirmDialog
│   └── util/
│       └── file_controls.py         (MODIFIED) - Selection mode support
└── controllers/
    └── explorer/
        └── itself.py                 (MODIFIED) - Batch operation handlers
```

## Usage Flow

### Entering Selection Mode
1. User clicks checkbox icon button in ExplorerTopBar
2. `toggle_selection_mode(True)` called on FileListView
3. Selection toolbar becomes visible
4. All tiles re-render with checkboxes
5. Toggle button hides

### Selecting Items
1. User clicks checkbox or tile
2. Checkbox state changes
3. `on_selection_changed` callback fires
4. Selection ID added to/removed from selected_file_ids or selected_directory_ids
5. Selection toolbar count updates

### Batch Delete
1. User clicks "Delete" in selection toolbar
2. Confirmation dialog shows with counts
3. User confirms
4. Progress dialog shows deletion progress
5. Items deleted sequentially
6. Errors collected and displayed
7. Directory refreshes
8. Selection mode exits

### Batch Download
1. User clicks "Download" in selection toolbar
2. User selects download directory
3. Progress dialog shows current file
4. Files downloaded maintaining structure
5. Directories recursively processed
6. Completion summary shown
7. Selection mode exits

## Error Handling

### Batch Delete Errors
- Permission denied (403) - Shows error message
- Directory not empty (400) - Shows error message
- Other errors - Displays in error list
- Continues processing remaining items

### Batch Download Errors
- Failed to get task ID - Shows error message
- Download failure - Displays in error list
- Directory listing failure - Shows error message
- Continues with remaining items

## Key Design Decisions

1. **Selection State in FileListView**: Centralized state management makes it easy to track and update selections across the entire list.

2. **Checkbox in Leading Position**: Checkboxes replace icons (file/folder) in selection mode, providing clear visual feedback and large touch targets.

3. **Direct Tile Creation in Selection Mode**: Bypasses context menus to avoid conflicts between selection interaction and right-click menus.

4. **Sequential Operations**: Both delete and download process items sequentially rather than in parallel to:
   - Simplify progress tracking
   - Avoid server overload
   - Make error handling more predictable

5. **Auto-Exit Selection Mode**: After batch operations complete, automatically exit selection mode to return to normal browsing.

6. **Structure Preservation in Downloads**: Downloaded directories maintain their server structure locally, making it easy for users to understand the layout.

## Testing Checklist

- [ ] Enter/exit selection mode via toggle button
- [ ] Select individual files/directories by clicking tiles
- [ ] Select individual items via checkboxes
- [ ] Select all items
- [ ] Clear selection
- [ ] Selection count updates correctly
- [ ] Batch delete with mixed files and directories
- [ ] Batch delete with permission errors
- [ ] Batch download single files
- [ ] Batch download directories with nested structure
- [ ] Batch download mixed files and directories
- [ ] Error handling for failed deletions
- [ ] Error handling for failed downloads
- [ ] Selection mode exits after operations
- [ ] Directory refreshes after delete
- [ ] Progress dialogs display correctly
- [ ] Confirmation dialog shows correct counts

## Future Enhancements

1. **Copy/Move Operations**: Add batch copy/move to selection toolbar
2. **Partial Selection Indicator**: Show if parent directory items are partially selected
3. **Drag and Drop**: Support drag-drop of selected items
4. **Keyboard Shortcuts**: Ctrl+A for select all, Delete for delete, etc.
5. **Selection Persistence**: Remember selections when navigating directories
6. **Progress Cancellation**: Allow canceling batch operations mid-process
7. **Parallel Downloads**: Download multiple files simultaneously for faster batch downloads
8. **Archive Download**: Option to download selected items as a ZIP file

## Dependencies

No new dependencies added. Implementation uses existing utilities:
- `batch_upload_file_to_server` pattern for batch operations
- `do_request` / `do_request_2` for server communication
- `download_file_from_server` for file transfers
- `get_connection` for WebSocket connections
- Flet UI components for dialogs and controls

## Internationalization

All user-facing strings use `get_translation()` for i18n support:
- Selection toolbar button labels
- Progress messages
- Error messages
- Confirmation dialog text
- Completion summaries

Translation keys to add to locale files:
- "Select items"
- "Select All"
- "Clear"
- "Download"
- "Delete"
- "Cancel"
- "Confirm Delete"
- "Delete {count} items ({file_count} files, {dir_count} directories)?"
- "This action cannot be undone."
- "Deleting items..."
- "Downloading: {current_file}"
- "{count} items selected"
- And various error/progress messages
