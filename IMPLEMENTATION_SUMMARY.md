# File Overwrite Feature Implementation Summary

## Overview
This implementation adds user interaction logic for handling file name conflicts when uploading files to the server. When a file with the same name already exists, the user is prompted to decide whether to overwrite, skip, or cancel the operation.

## Implementation Details

### 1. Conflict Detection (409 Response)
When `create_document` returns a 409 status code, the server includes:
- `type`: Either "document" or "directory"
- `id`: The ID of the existing object (only if user has read access)

### 2. Decision Logic
The implementation follows these rules:

#### Can Overwrite
- ✅ Conflict type is "document"
- ✅ Conflict ID is provided (user has read access)
- ✅ Callback function is available

When all conditions are met, the user is shown a confirmation dialog with three options:
1. **Overwrite**: Uploads a new version using `upload_document` request
2. **Skip**: Skips this file and continues with the next
3. **Cancel**: Stops the entire upload operation

#### Cannot Overwrite (Treated as Error)
- ❌ Conflict type is "directory" (cannot overwrite a directory with a file)
- ❌ Conflict ID is empty (user lacks read access to the existing object)
- ❌ No callback function provided

In these cases, the conflict is treated as a regular error and reported to the user.

### 3. Modified Components

#### A. `FileOverwriteConfirmDialog` (New)
**File**: `src/include/ui/controls/dialogs/explorer.py`

A new dialog class that:
- Displays the filename and asks for user action
- Provides three buttons: Overwrite, Skip, Cancel
- Uses an asyncio.Event to wait for user choice
- Returns the choice via `wait_for_choice()` method

```python
async def wait_for_choice(self) -> str | None:
    """Wait for the user to make a choice and return it."""
    await self.choice_event.wait()
    return self.user_choice  # 'overwrite', 'skip', or None
```

#### B. `batch_upload_file_to_server` (Modified)
**File**: `src/include/util/transfer.py`

Enhanced to handle 409 responses:
- Added `on_conflict_callback` parameter (optional async function)
- Detects 409 responses and extracts conflict type and ID
- Calls the callback if conditions are met
- Processes user choice:
  - **Overwrite**: Calls `upload_document` instead of `create_document`
  - **Skip**: Breaks the retry loop for this file
  - **Cancel**: Raises InvalidResponseError to stop all uploads

```python
async def batch_upload_file_to_server(
    app_shared: AppShared,
    directory_id: Optional[str],
    files: list[FilePickerFile],
    max_size: int = 1024**2 * 4,
    max_retries: int = 3,
    on_conflict_callback=None,  # NEW PARAMETER
):
```

#### C. `FileExplorerController.action_upload` (Modified)
**File**: `src/include/controllers/explorer/itself.py`

Updated to provide conflict callback:
- Defines `on_conflict` async function that shows the dialog
- Passes callback to `batch_upload_file_to_server`
- Handles user cancellation gracefully

```python
async def on_conflict(filename: str, conflict_type: str, conflict_id: str) -> str | None:
    """Handle file conflict by showing a dialog to the user."""
    confirm_dialog = FileOverwriteConfirmDialog(
        filename=filename,
        existing_id=conflict_id,
    )
    self.control.page.show_dialog(confirm_dialog)
    choice = await confirm_dialog.wait_for_choice()
    return choice
```

#### D. `FileExplorerController.action_directory_upload` (Modified)
**File**: `src/include/controllers/explorer/itself.py`

Updated to handle 409 responses directly:
- Checks response code for 409
- Validates conflict type and ID
- Shows confirmation dialog
- Calls `upload_document` if user chooses to overwrite
- Properly handles skip and cancel actions

### 4. Server API Usage

#### `create_document` Request
Used to create a new document:
```python
response = await do_request_2(
    action="create_document",
    data={
        "title": filename,
        "folder_id": directory_id,
        "access_rules": {},
    },
    username=app_shared.username,
    token=app_shared.token,
)
```

**409 Response Format**:
```json
{
    "code": 409,
    "message": "File already exists",
    "data": {
        "type": "document",  // or "directory"
        "id": "abc123"       // or empty string if no read access
    }
}
```

#### `upload_document` Request
Used to upload a new version of an existing document:
```python
upload_response = await do_request_2(
    action="upload_document",
    data={
        "id": conflict_id,
    },
    username=app_shared.username,
    token=app_shared.token,
)
```

### 5. User Experience Flow

#### Scenario 1: File Exists, User Has Read Access
1. User uploads file "document.pdf"
2. Server returns 409 with type="document" and id="xyz789"
3. Dialog appears: "A file named 'document.pdf' already exists. Do you want to overwrite it?"
4. User clicks "Overwrite"
5. System calls `upload_document` with id="xyz789"
6. New version is uploaded successfully

#### Scenario 2: File Exists, User Lacks Read Access
1. User uploads file "secret.pdf"
2. Server returns 409 with type="document" and id="" (empty)
3. No dialog shown - treated as error
4. Error message: "Failed to create document 'secret.pdf': File already exists"

#### Scenario 3: Directory Exists with Same Name
1. User uploads file "reports.pdf"
2. Server returns 409 with type="directory" and id="dir123"
3. No dialog shown - cannot overwrite directory with file
4. Error message: "Failed to create document 'reports.pdf': Name conflicts with existing directory"

#### Scenario 4: User Skips File
1. User uploads multiple files
2. Conflict detected for "file2.pdf"
3. Dialog appears
4. User clicks "Skip"
5. System continues with "file3.pdf" without error

#### Scenario 5: User Cancels
1. User uploads multiple files
2. Conflict detected for "file2.pdf"
3. Dialog appears
4. User clicks "Cancel"
5. System stops all uploads and closes progress dialog

### 6. Error Handling

The implementation properly handles:
- Network errors during `upload_document` request
- Permission errors (403)
- Invalid server responses
- Connection failures with automatic retry
- User cancellation without leaving partial uploads

### 7. Backward Compatibility

The changes are backward compatible:
- `batch_upload_file_to_server` has `on_conflict_callback=None` as default
- If callback is not provided, 409 errors are treated as regular errors (original behavior)
- Existing code that doesn't pass the callback continues to work

## Testing Considerations

To fully test this feature, you would need:

1. **Server Setup**: A running CFMS server with file upload capabilities
2. **Test Cases**:
   - Upload file that doesn't exist (normal flow)
   - Upload file with same name as existing file (409 with ID)
   - Upload file with same name but no read access (409 without ID)
   - Upload file with same name as directory (409 with type="directory")
   - Test all three user choices (Overwrite, Skip, Cancel)
   - Test batch upload with mixed scenarios
   - Test directory upload with conflicts

3. **UI Testing**: Verify dialog appearance and responsiveness

## Translation Requirements

The following strings need to be translated:
- "File Already Exists" (dialog title)
- "A file named \"{filename}\" already exists. Do you want to overwrite it?" (dialog message)
- "Overwrite" (button)
- "Skip" (button)

See `TRANSLATION_STRINGS_NEEDED.md` for details on translation extraction and compilation.

## Code Review Checklist

✅ Handles 409 response code correctly
✅ Checks conflict type is "document"
✅ Checks conflict ID is provided
✅ Shows dialog only when overwrite is possible
✅ Implements all three user choices (Overwrite, Skip, Cancel)
✅ Uses `upload_document` request for overwriting
✅ Maintains backward compatibility
✅ Handles errors gracefully
✅ Works in both single and batch upload modes
✅ Works in directory upload mode
✅ Properly manages async operations
✅ Uses existing patterns (AlertDialog, asyncio.Event, do_request_2)
✅ Follows code style conventions
✅ Includes proper type hints
✅ Documents user-facing strings for translation
