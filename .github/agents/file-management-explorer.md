---
name: CFMS File Management & Explorer Developer
description: Expert in file management operations, file explorer UI, file transfers, and directory management for CFMS Client NEXT.
---

## File Management Overview

The CFMS Client NEXT provides comprehensive file and directory management capabilities through a file explorer interface. The system supports hierarchical directory structures, file uploads/downloads, batch operations, and sorting/filtering.

## File Explorer Architecture

### Main Components

**FileManagerView** (`include/ui/controls/views/explorer.py`):
- Main container for the file explorer interface
- Manages current directory state
- Coordinates between UI components and controllers

**Key Sub-Components**:
```
FileManagerView
├── ExplorerTopBar          # Action buttons (upload, create dir, etc.)
├── FileSortBar             # Sorting controls
├── FilePathIndicator       # Breadcrumb navigation
└── FileListView            # File/directory listing
```

### Component Details

#### FilePathIndicator
**Location**: `include/ui/controls/views/explorer.py`

Breadcrumb-style path display showing current location:
```python
class FilePathIndicator(ft.Column):
    def __init__(self, display_root: Optional[str] = None):
        self.paths: list[str] = []  # Path segments
        
    def update_path(self):
        # Updates display: "/" + "/".join(self.paths)
        
    def go(self, path: str):
        # Navigate forward
        
    def back(self):
        # Navigate back
        
    def reset(self, new_root: Optional[str] = None):
        # Reset to root or new path
```

#### FileListView
**Location**: `include/ui/controls/views/explorer.py`

Scrollable list view displaying files and directories:
```python
class FileListView(ft.ListView):
    def __init__(self, parent_manager: "FileManagerView"):
        # State variables
        self.current_parent_id: str | None = None
        self.current_files_data: list[dict] = []
        self.current_directories_data: list[dict] = []
        
    def sort_files(self, sort_mode: SortMode, sort_order: SortOrder):
        # Sort and update display
```

**File/Directory Data Structure**:
```python
# File data
{
    "id": "file_id",
    "title": "filename.pdf",
    "size": 12345,                    # bytes
    "created_time": 1234567890.0,     # Unix timestamp
    "last_modified": 1234567890.0,    # Unix timestamp
    "uploader": "username",
    "sha256": "hash...",
}

# Directory data
{
    "id": "dir_id",
    "name": "dirname",
    "created_time": 1234567890.0,
    "last_modified": 1234567890.0,
    "parent_id": "parent_dir_id",
}
```

#### ExplorerTopBar
**Location**: `include/ui/controls/components/explorer/bar.py`

Action buttons for file operations:
- Upload files
- Create directory
- Refresh
- Additional actions (context-dependent)

#### FileSortBar
**Location**: `include/ui/controls/components/explorer/bar.py`

Sorting controls:
```python
class SortMode(Enum):
    BY_NAME = "name"
    BY_LAST_MODIFIED = "last_modified"
    BY_CREATED_AT = "created_at"
    BY_SIZE = "size"

class SortOrder(Enum):
    ASCENDING = "asc"
    DESCENDING = "desc"
```

## File Operations

### File Explorer Controller
**Location**: `include/controllers/explorer/itself.py`

Main controller handling file operations:
```python
class FileExplorerController:
    def __init__(self, view: "FileManagerView"):
        self.view = view
        self.app_config = AppConfig()
        
    async def action_upload(self, files: list[FilePickerFile])
    async def action_download(self, file_id: str, filename: str)
    async def action_delete_file(self, file_id: str)
    async def action_delete_directory(self, dir_id: str)
```

### Upload Operations

#### Single/Batch File Upload

**Function**: `action_upload()` in FileExplorerController

**Process**:
1. Create progress UI (ProgressBar + status Text)
2. Show batch upload dialog (if multiple files) or inline progress
3. Create upload tasks on server
4. Stream files using `batch_upload_file_to_server()`
5. Update progress for each file
6. Handle errors per-file (continues on error)
7. Refresh file list on completion

**Progress Tracking**:
```python
async for index, filename, current_size, file_size, exc in batch_upload_file_to_server(...):
    if exc:
        # Handle error for this file
        continue
    
    # Update progress
    progress_bar.value = current_size / file_size
    progress_info.value = f"{filename} ({current_size}/{file_size} bytes)"
```

**Error Handling**:
- `InvalidResponseError` with code 403: Permission denied
- Other `InvalidResponseError`: Show error message with code
- General exceptions: Display error and continue with next file

#### Upload Utility Functions
**Location**: `include/util/transfer.py`

**`batch_upload_file_to_server()`**:
```python
async def batch_upload_file_to_server(
    app_config: AppConfig,
    directory_id: str,
    files: list[FilePickerFile]
) -> AsyncIterator[tuple[int, str, int, int, Optional[Exception]]]:
    # Yields: (index, filename, bytes_uploaded, total_bytes, exception)
```

**Features**:
- Creates server upload tasks automatically
- Uploads files sequentially
- Calculates SHA256 hash for verification
- Reports progress chunk-by-chunk
- Yields exceptions without stopping iteration

**`upload_file_to_server()`**:
```python
async def upload_file_to_server(
    client: ClientConnection,
    task_id: str,
    file_path: str
) -> AsyncIterator[tuple[int, int]]:
    # Yields: (bytes_uploaded, total_bytes)
```

Low-level upload function handling the binary transfer protocol.

### Download Operations

#### File Download

**Function**: `download_file_from_server()` in `include/util/transfer.py`

```python
async def download_file_from_server(
    client: ClientConnection,
    task_id: str,
    save_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
)
```

**Features**:
- Supports AES-encrypted downloads
- Progress callbacks for UI updates
- SHA256 verification
- Temporary file with atomic rename on success

**Process**:
1. Request download task from server
2. Receive file metadata (size, encryption info)
3. Stream file in chunks
4. Decrypt if encrypted (AES-256-CBC)
5. Write to temporary file
6. Verify hash
7. Rename to final destination

**Error Handling**:
- `FileSizeMismatchError`: Downloaded size ≠ expected size
- `FileHashMismatchError`: SHA256 hash mismatch
- Generic exceptions: Clean up temp file

### Directory Operations

#### Create Directory

**Dialog**: `CreateDirectoryDialog` (`include/ui/controls/dialogs/explorer.py`)
**Controller**: `CreateDirectoryDialogController` (`include/controllers/dialogs/directory.py`)

**Process**:
1. Show dialog with text field for directory name
2. Validate name (non-empty, valid characters)
3. Call `create_directory()` utility
4. Refresh parent directory listing
5. Close dialog

**Utility Function** (`include/util/create.py`):
```python
async def create_directory(
    parent_id: str,
    name: str,
    app_config: AppConfig
) -> Response:
    response = await do_request_2(
        action="create_directory",
        data={"parent_id": parent_id, "name": name}
    )
    return response
```

#### Open/Navigate Directory

**Dialog**: `OpenDirectoryDialog` (for special directory operations)
**Controller**: `OpenDirectoryDialogController`

**Navigation**:
```python
# In FileManagerView
async def load_directory(self, directory_id: str):
    # Update current_directory_id
    self.current_directory_id = directory_id
    
    # Fetch directory contents
    response = await do_request_2(
        action="list_files",
        data={"directory_id": directory_id}
    )
    
    # Update FileListView
    files = response.data.get("files", [])
    directories = response.data.get("directories", [])
    
    # Update UI
    update_file_controls(listview, files, directories, directory_id)
```

#### Delete Directory

**Confirmation**: Typically shows a confirmation dialog before deletion

**Request**:
```python
response = await do_request_2(
    action="delete_directory",
    data={"directory_id": dir_id}
)

if response.code == 200:
    # Refresh parent directory
elif response.code == 403:
    # Permission denied
elif response.code == 400:
    # Directory not empty or other constraint
```

### File Information

#### File Tiles/Cards

**Location**: `include/controllers/explorer/tile.py`

Display individual file/directory items in the list:
- File icon (based on type)
- Filename
- Metadata (size, upload date, uploader)
- Context menu trigger

#### Context Menus

**Location**: `include/ui/controls/contextmenus/explorer.py`

Right-click menu for files/directories:
```python
# File context menu
- Download
- Get Info
- Share (if permissions allow)
- Delete
- Rename

# Directory context menu
- Open
- Create Subdirectory
- Delete
- Rename
```

## File Sorting and Filtering

### Sorting Implementation

**Location**: `FileListView.sort_files()` in `include/ui/controls/views/explorer.py`

```python
def sort_files(
    self,
    sort_mode: SortMode = SortMode.BY_NAME,
    sort_order: SortOrder = SortOrder.ASCENDING,
):
    # Deep copy data
    _working_files_data = deepcopy(self.current_files_data)
    _working_directories_data = deepcopy(self.current_directories_data)
    
    # Define key functions
    match sort_mode:
        case SortMode.BY_NAME:
            dir_key = lambda x: x["name"].lower()
            file_key = lambda x: x["title"].lower()
        case SortMode.BY_LAST_MODIFIED:
            dir_key = file_key = lambda x: x.get("last_modified", 0)
        case SortMode.BY_CREATED_AT:
            dir_key = file_key = lambda x: x.get("created_time", 0)
        case SortMode.BY_SIZE:
            dir_key = file_key = lambda x: x.get("size", 0)
    
    # Sort
    _working_directories_data.sort(
        key=dir_key,
        reverse=(sort_order == SortOrder.DESCENDING)
    )
    _working_files_data.sort(
        key=file_key,
        reverse=(sort_order == SortOrder.DESCENDING)
    )
    
    # Update UI
    update_file_controls(
        self,
        _working_files_data,
        _working_directories_data,
        self.current_parent_id
    )
```

**Sort Keys**:
- **BY_NAME**: Alphabetical (case-insensitive)
- **BY_LAST_MODIFIED**: Most/least recently modified
- **BY_CREATED_AT**: Newest/oldest
- **BY_SIZE**: Largest/smallest

## Batch Operations

### Batch Upload Dialog

**Location**: `include/ui/controls/dialogs/explorer.py`

```python
class BatchUploadFileAlertDialog(AlertDialog):
    def __init__(self, progress_column, stop_event: asyncio.Event):
        # progress_column contains ProgressBar + status Text
        # stop_event allows user to cancel operation
```

**Features**:
- Progress bar for overall progress
- Status text showing current file
- Stop button to cancel remaining uploads
- Error list for failed uploads

### Upload Directory

**Dialog**: `UploadDirectoryAlertDialog`

Supports uploading entire directory structures:
1. Build directory tree from local filesystem
2. Create corresponding directories on server
3. Upload all files maintaining structure
4. Show hierarchical progress

**Utility**: `build_directory_tree()` (`include/util/path.py`)

## Path Utilities

### Path Manipulation
**Location**: `include/util/path.py`

Functions for working with file paths and directory structures:
- `build_directory_tree()`: Recursively build tree from filesystem
- Path normalization and validation

### UI Path Display
**Location**: `include/ui/util/path.py`

Functions for displaying paths in UI:
- Breadcrumb generation
- Path truncation for long paths
- Icon selection based on path/file type

## File Type Handling

### File Icons
Based on file extension or MIME type:
- Documents: PDF, DOCX, TXT
- Images: PNG, JPG, SVG
- Archives: ZIP, RAR, 7Z
- Code: PY, JS, HTML, CSS
- Default: Generic file icon

### File Preview (Future)
Structure supports adding preview functionality:
- Image preview
- PDF preview
- Text file preview

## Permissions and Access Control

### Permission Checking

Files and directories have associated permissions:
```python
# User permissions (from AppConfig)
user_permissions = app_config.user_permissions

# Common permissions
if "file_upload" in user_permissions:
    # Show upload button
    
if "file_delete" in user_permissions:
    # Show delete option
    
if "directory_create" in user_permissions:
    # Show create directory button
```

### Error Handling for Permissions

```python
if response.code == 403:
    send_error(page, _("Permission denied: You don't have access to this resource"))
    return
```

## Best Practices

1. **Always Show Progress**: Use progress bars for uploads/downloads
2. **Verify Hashes**: Always verify SHA256 after transfers
3. **Handle Errors Gracefully**: Show user-friendly error messages
4. **Refresh After Operations**: Reload directory listing after create/delete
5. **Use Batch Operations**: For multiple files, use batch upload
6. **Sort Data Copies**: Never mutate original data; work with deep copies
7. **Clean Up Resources**: Close file handles, remove temp files on error
8. **Check Permissions**: Before showing UI elements, check user permissions
9. **Atomic Renames**: Use temp file + rename for downloads
10. **Async Operations**: All file I/O must be async

## Error Messages

### Common Error Scenarios

**Upload Errors**:
- "Upload failed: No permission to upload files" (403)
- "Upload failed: File too large" (400)
- "Upload failed: Hash mismatch" (custom)

**Download Errors**:
- "Download failed: File not found" (404)
- "Download failed: No permission to download" (403)
- "Download failed: Hash verification failed"

**Directory Errors**:
- "Cannot create directory: Name already exists" (400)
- "Cannot delete directory: Directory not empty" (400)
- "Permission denied: Cannot access directory" (403)

## Testing File Operations

### Manual Testing Checklist
- [ ] Upload single file (small < 1MB)
- [ ] Upload large file (> 10MB) - verify progress
- [ ] Upload multiple files (batch) - verify per-file progress
- [ ] Download file - verify hash
- [ ] Create directory
- [ ] Navigate into/out of directories
- [ ] Delete file
- [ ] Delete directory (empty)
- [ ] Sort by name, date, size (ascending/descending)
- [ ] Error handling (no permission, file not found)
- [ ] Connection loss during upload (should retry)

### Edge Cases
- Zero-byte files
- Files with special characters in names
- Very long filenames
- Nested directory structures (deep hierarchies)
- Simultaneous uploads
- Network interruption during transfer
