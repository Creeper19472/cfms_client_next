# Multi-Select Feature - Quick Reference

## How to Use (User Perspective)

### Entering Selection Mode
1. Click the **checkbox icon** button in the file explorer toolbar
2. All file and directory icons change to checkboxes
3. Selection toolbar appears below the main toolbar

### Selecting Items
- Click on any file or directory tile to toggle selection
- Or click the checkbox directly
- Selected items show a checked checkbox

### Selection Actions

**Select All**
- Button in selection toolbar
- Selects all files and directories in current directory

**Clear Selection**
- Button in selection toolbar
- Deselects all items

**Download Selected**
- Button in selection toolbar
- Prompts to choose download location
- Downloads all selected items maintaining directory structure
- Shows progress dialog

**Delete Selected**
- Button in selection toolbar
- Shows confirmation dialog with counts
- Deletes all selected items sequentially
- Shows progress dialog
- Lists any errors

**Cancel**
- Button in selection toolbar
- Exits selection mode
- Clears all selections

### Selection Count
- Displayed in toolbar: "5 items selected"
- Updates automatically as you select/deselect

## API Reference (Developer)

### FileListView Methods

```python
def toggle_selection_mode(self, enabled: bool):
    """Enable or disable selection mode."""
    
def select_all(self):
    """Select all files and directories."""
    
def clear_selection(self):
    """Clear all selections."""
    
def toggle_file_selection(self, file_id: str):
    """Toggle selection state of a file."""
    
def toggle_directory_selection(self, directory_id: str):
    """Toggle selection state of a directory."""
    
def get_selected_count(self) -> int:
    """Get total count of selected items."""
```

### FileExplorerController Methods

```python
async def action_batch_delete(self):
    """Handle batch delete of selected files and directories."""

async def action_batch_download(self):
    """Handle batch download of selected files and directories."""
```

### Utility Functions

```python
# In src/include/util/batch_operations.py

async def batch_delete_items(
    app_shared: AppShared,
    file_ids: list[str],
    directory_ids: list[str],
) -> AsyncIterator[tuple[str, str, bool, Optional[str]]]:
    """
    Delete multiple files and directories.
    
    Yields: (item_type, item_id, success, error_message)
    """

async def batch_download_items(
    app_shared: AppShared,
    file_items: list[dict],
    directory_items: list[dict],
    save_root_path: str,
) -> AsyncIterator[tuple[str, str, str, bool, Optional[str]]]:
    """
    Download multiple files and directories with structure preservation.
    
    Yields: (item_type, item_name, current_file, success, error_message)
    """
```

## Component Reference

### SelectionToolbar
**Location**: `src/include/ui/controls/components/explorer/bar.py`

```python
class SelectionToolbar(ft.Row):
    """Toolbar that appears when items are selected in the file explorer."""
    
    # Buttons
    self.select_all_button
    self.clear_selection_button
    self.download_button
    self.delete_button
    self.cancel_button
    
    # Info display
    self.selection_info  # "5 items selected"
    
    # Methods
    def update_selection_count(self, count: int)
```

### BatchDeleteConfirmDialog
**Location**: `src/include/ui/controls/dialogs/explorer.py`

```python
class BatchDeleteConfirmDialog(AlertDialog):
    """Dialog to confirm batch deletion of files and directories."""
    
    async def wait_for_confirmation(self) -> bool:
        """Wait for user confirmation and return True if confirmed."""
```

### FileTile / DirectoryTile
**Location**: `src/include/ui/controls/components/explorer/tile.py`

New parameters:
```python
selection_mode: bool = False
is_selected: bool = False
on_selection_changed: Optional[Callable[[str, bool], None]] = None
```

## State Variables

### FileListView
```python
self.selection_mode: bool = False
self.selected_file_ids: set[str] = set()
self.selected_directory_ids: set[str] = set()
```

## Event Flow

### Entering Selection Mode
```
User clicks toggle button
  ↓
ExplorerTopBar.on_selection_toggle_click()
  ↓
FileListView.toggle_selection_mode(True)
  ↓
update_file_controls() regenerates tiles with checkboxes
  ↓
SelectionToolbar becomes visible
```

### Selecting an Item
```
User clicks tile/checkbox
  ↓
Tile.on_tile_click_selection_mode() or on_checkbox_change()
  ↓
on_selection_changed(item_id, is_selected) callback
  ↓
FileListView.selected_*_ids updated
  ↓
SelectionToolbar.update_selection_count() called
```

### Batch Delete
```
User clicks "Delete" button
  ↓
SelectionToolbar.on_delete_click()
  ↓
FileExplorerController.action_batch_delete()
  ↓
BatchDeleteConfirmDialog shown
  ↓
User confirms
  ↓
_execute_batch_delete() processes items
  ↓
Progress dialog shows status
  ↓
batch_delete_items() deletes sequentially
  ↓
Directory refreshed, selection mode exited
```

### Batch Download
```
User clicks "Download" button
  ↓
SelectionToolbar.on_download_click()
  ↓
FileExplorerController.action_batch_download()
  ↓
User selects download directory
  ↓
Progress dialog shown
  ↓
batch_download_items() downloads with structure preservation
  ↓
Completion message shown, selection mode exited
```

## Error Handling Patterns

### In Batch Operations
```python
try:
    # Attempt operation
    response = await do_request(...)
    if response.get("code") == 200:
        yield (type, id, True, None)  # Success
    else:
        error = format_error(response)
        yield (type, id, False, error)  # Failure with error
except Exception as e:
    yield (type, id, False, str(e))  # Exception
```

### In UI
```python
# Collect errors
if not success:
    failed += 1
    error_column.controls.append(ft.Text(error_msg))

# Show summary
if failed > 0:
    # Keep dialog open with error list
    progress_dialog.actions = [ok_button]
else:
    # Auto-close on success
    progress_dialog.open = False
```

## Testing Commands

```bash
# Syntax check
cd /home/runner/work/cfms_client_next/cfms_client_next
python -m py_compile src/include/util/batch_operations.py

# Run all checks
python -m py_compile src/include/**/*.py

# Check for specific function
grep -n "async def action_batch_delete" src/include/controllers/explorer/itself.py
```

## Common Customizations

### Add New Batch Operation
1. Add button to SelectionToolbar
2. Add handler method to FileExplorerController
3. Create utility function in batch_operations.py if needed
4. Use same error handling pattern

### Modify Selection UI
Edit `src/include/ui/controls/components/explorer/tile.py`:
- Change checkbox position
- Modify selection indicator
- Add selection count badge

### Change Operation Behavior
Edit `src/include/util/batch_operations.py`:
- Modify delete order (directories first)
- Add parallel processing
- Change error handling strategy

## Keyboard Shortcuts (Future)
Not yet implemented, but structure supports:
- Ctrl+A → select_all()
- Delete key → action_batch_delete()
- Escape → toggle_selection_mode(False)

## Related Documentation
- [BATCH_OPERATIONS_IMPLEMENTATION.md](./BATCH_OPERATIONS_IMPLEMENTATION.md) - Full implementation details
- [MULTI_SELECT_SUMMARY.md](./MULTI_SELECT_SUMMARY.md) - Implementation summary
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Overall system architecture
