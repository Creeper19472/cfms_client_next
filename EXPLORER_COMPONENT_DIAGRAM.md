# File Explorer Component Architecture Diagram

## Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                          HomeModel (Route)                          │
│                     include/ui/models/home.py                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ contains
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FileManagerView                                │
│                  (ft.Container - Main View)                         │
│              include/ui/controls/views/explorer.py                  │
│                                                                     │
│  Properties:                                                        │
│  • root_directory_id: str | None                                   │
│  • current_directory_id: str | None                                │
│  • controller: FileExplorerController                              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              content: ft.Column                             │  │
│  │  ┌───────────────────────────────────────────────────────┐ │  │
│  │  │ 1. Title Text: "File Management"                      │ │  │
│  │  ├───────────────────────────────────────────────────────┤ │  │
│  │  │ 2. FilePathIndicator (Breadcrumb)                     │ │  │
│  │  ├───────────────────────────────────────────────────────┤ │  │
│  │  │ 3. ExplorerTopBar (Action Buttons)                    │ │  │
│  │  ├───────────────────────────────────────────────────────┤ │  │
│  │  │ 4. SelectionToolbar (When selection mode active)      │ │  │
│  │  ├───────────────────────────────────────────────────────┤ │  │
│  │  │ 5. Divider                                            │ │  │
│  │  ├───────────────────────────────────────────────────────┤ │  │
│  │  │ 6. ProgressRing (Loading indicator)                   │ │  │
│  │  ├───────────────────────────────────────────────────────┤ │  │
│  │  │ 7. FileSortBar (Sort controls)                        │ │  │
│  │  ├───────────────────────────────────────────────────────┤ │  │
│  │  │ 8. FileListView (File/folder list)                    │ │  │
│  │  │    OR AccessDeniedView (On permission error)          │ │  │
│  │  └───────────────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Breakdown

### 1. FilePathIndicator (Breadcrumb Navigation)
```
┌─────────────────────────────────────┐
│   FilePathIndicator (ft.Column)     │
│                                     │
│   Display: /path/to/current/folder │
│                                     │
│   Methods:                          │
│   • go(path) - Navigate forward     │
│   • back() - Navigate backward      │
│   • reset(root) - Reset to root     │
└─────────────────────────────────────┘
```

### 2. ExplorerTopBar (Action Toolbar)
```
┌────────────────────────────────────────────────────────────────┐
│                    ExplorerTopBar (ft.Row)                     │
│  include/ui/controls/components/explorer/bar.py                │
├────────────────────────────────────────────────────────────────┤
│  [Upload] [Upload Dir] [New Folder] [Refresh] [Search] [Select]│
│                                               [Open Folder] →   │
│                                                                │
│  Actions:                                                      │
│  • Upload files                                               │
│  • Upload directory tree                                      │
│  • Create new directory                                       │
│  • Refresh current view                                       │
│  • Search documents                                           │
│  • Toggle selection mode                                      │
│  • Open directory by ID                                       │
└────────────────────────────────────────────────────────────────┘
```

### 3. SelectionToolbar (Batch Operations)
```
┌────────────────────────────────────────────────────────────────┐
│              SelectionToolbar (ft.Row)                         │
│  Visible only in selection mode                                │
├────────────────────────────────────────────────────────────────┤
│  [3 items selected] | [Select All] [Clear] |                  │
│  [Download] [Move] [Delete] | [Cancel]                        │
│                                                                │
│  Features:                                                     │
│  • Dynamic selection count                                    │
│  • Batch operations on selected items                         │
│  • Select all / Clear selection                               │
└────────────────────────────────────────────────────────────────┘
```

### 4. FileSortBar (Sort Controls)
```
┌────────────────────────────────────────────────────────────────┐
│                  FileSortBar (ft.Row)                          │
│  Controller: FileSortBarController                             │
├────────────────────────────────────────────────────────────────┤
│  Sort by: [Name ▼] [↑]                                        │
│                                                                │
│  Options:                                                      │
│  • Name (A-Z, Z-A)                                           │
│  • Created at                                                 │
│  • Last Modified                                              │
│  • Size                                                       │
│  • Type                                                       │
│                                                                │
│  Triggers: Calls file_listview.sort_files()                   │
└────────────────────────────────────────────────────────────────┘
```

### 5. FileListView (Dynamic Content Area)
```
┌────────────────────────────────────────────────────────────────┐
│               FileListView (ft.ListView)                       │
│  Controller: FileListViewController                            │
│  include/ui/controls/views/explorer.py                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  State:                                                        │
│  • current_parent_id: str | None                              │
│  • current_files_data: list[dict]                             │
│  • current_directories_data: list[dict]                       │
│  • selection_mode: bool                                       │
│  • selected_file_ids: set[str]                                │
│  • selected_directory_ids: set[str]                           │
│                                                                │
│  Controls (Dynamically Generated):                            │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ [Parent Dir] <...>                                       │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ 📁 Folder 1                    Created: 2024-01-01   ⭐  │ │
│  │ 📁 Folder 2                    Created: 2024-01-02       │ │
│  │ 📄 Document 1.pdf    1.5 MB    Modified: 2024-01-03   ⭐ │ │
│  │ 📄 Document 2.docx   2.3 MB    Modified: 2024-01-04      │ │
│  │ 📄 Document 3.xlsx   0.8 MB    Modified: 2024-01-05      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  SELECTION MODE:                                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ ☑ Folder 1                     Created: 2024-01-01       │ │
│  │ ☐ Folder 2                     Created: 2024-01-02       │ │
│  │ ☑ Document 1.pdf    1.5 MB    Modified: 2024-01-03      │ │
│  │ ☐ Document 2.docx   2.3 MB    Modified: 2024-01-04      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  Methods:                                                      │
│  • sort_files(mode, order)                                    │
│  • toggle_selection_mode(enabled)                             │
│  • select_all() / clear_selection()                           │
│  • toggle_file_selection(id) / toggle_directory_selection(id) │
│  • get_selected_count() -> int                                │
└────────────────────────────────────────────────────────────────┘
```

## List Item Components

### Normal Mode: Context Menu Wrappers

#### FileContextMenu Structure
```
┌─────────────────────────────────────────────────────────────┐
│          FileContextMenu (ContextMenu2)                     │
│     include/ui/controls/contextmenus/explorer.py            │
│     Controller: FileContextMenuController                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         FileTile (ft.ListTile)                        │ │
│  │  include/ui/controls/components/explorer/tile.py      │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │ 📄  Document Name                           ⭐  │  │ │
│  │  │     Size: 1.5 MB                                │  │ │
│  │  │     Modified: 2024-01-01 10:30:00               │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Right-click Menu:                                          │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 🗑️  Delete              (require: delete_document)    │ │
│  │ ✏️  Rename              (require: rename_document)    │ │
│  │ 📤  Move                (require: move)               │ │
│  │ ─────────────────────────────────────────────────────│ │
│  │ 🔒  Authorize           (require: manage_access)      │ │
│  │ 📋  View access entries (require: view_access_entries)│ │
│  │ ⚙️  Set permissions     (require: set_access_rules)  │ │
│  │ ─────────────────────────────────────────────────────│ │
│  │ 📤  Upload new version                                │ │
│  │ 🕐  View Revisions      (require: list_revisions)    │ │
│  │ ─────────────────────────────────────────────────────│ │
│  │ ℹ️  Properties                                        │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Events:                                                    │
│  • Left-click: Open/download file                          │
│  • Right-click: Show context menu                          │
│  • Hover: Show star button                                 │
└─────────────────────────────────────────────────────────────┘
```

#### DirectoryContextMenu Structure
```
┌─────────────────────────────────────────────────────────────┐
│       DirectoryContextMenu (ContextMenu2)                   │
│     include/ui/controls/contextmenus/explorer.py            │
│     Controller: DirectoryContextMenuController              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │       DirectoryTile (ft.ListTile)                     │ │
│  │  include/ui/controls/components/explorer/tile.py      │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │ 📁  Folder Name                             ⭐  │  │ │
│  │  │     Created: 2024-01-01 10:30:00                │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Right-click Menu:                                          │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 🗑️  Delete              (require: delete_directory)   │ │
│  │ ✏️  Rename              (require: rename_directory)   │ │
│  │ 📤  Move                (require: move)               │ │
│  │ ─────────────────────────────────────────────────────│ │
│  │ 🔒  Authorize           (require: manage_access)      │ │
│  │ 📋  View Access Entries (require: view_access_entries)│ │
│  │ ⚙️  Set Permissions     (require: set_access_rules)  │ │
│  │ ─────────────────────────────────────────────────────│ │
│  │ ℹ️  Properties                                        │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Events:                                                    │
│  • Left-click: Navigate into directory                     │
│  • Right-click: Show context menu                          │
│  • Hover: Show star button                                 │
└─────────────────────────────────────────────────────────────┘
```

### Selection Mode: Checkbox Tiles

#### FileTile (Selection Mode)
```
┌─────────────────────────────────────────────────────────────┐
│              FileTile (ft.ListTile)                         │
│     include/ui/controls/components/explorer/tile.py         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ☑  Document Name                                 ⭐  │  │
│  │    Size: 1.5 MB                                      │  │
│  │    Modified: 2024-01-01 10:30:00                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Properties:                                                │
│  • selection_mode: bool = True                             │
│  • is_selected: bool                                       │
│  • on_selection_changed: Callable[[str, bool], None]      │
│                                                             │
│  Events:                                                    │
│  • Tile click: Toggle checkbox                             │
│  • Checkbox change: Update selection state                 │
│  • Star button: Add/remove from favorites                  │
└─────────────────────────────────────────────────────────────┘
```

#### DirectoryTile (Selection Mode)
```
┌─────────────────────────────────────────────────────────────┐
│           DirectoryTile (ft.ListTile)                       │
│     include/ui/controls/components/explorer/tile.py         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ☐  Folder Name                                   ⭐  │  │
│  │    Created: 2024-01-01 10:30:00                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Properties:                                                │
│  • selection_mode: bool = True                             │
│  • is_selected: bool                                       │
│  • on_selection_changed: Callable[[str, bool], None]      │
│                                                             │
│  Events:                                                    │
│  • Tile click: Toggle checkbox                             │
│  • Checkbox change: Update selection state                 │
│  • Star button: Add/remove from favorites                  │
└─────────────────────────────────────────────────────────────┘
```

## Controller Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Controller[T] (Generic Base)              │
│             include/controllers/base.py                     │
│                                                             │
│  Properties:                                                │
│  • control: T (generic type)                               │
│  • app_shared: AppShared (singleton)                       │
└────────────────────┬────────────────────────────────────────┘
                     │ inherits
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
┌─────────────┐ ┌────────────┐ ┌────────────────────────────┐
│FileSortBar  │ │FileList    │ │  FileExplorerController    │
│Controller   │ │View        │ │  (Main Controller)         │
│             │ │Controller  │ │  858 lines                 │
│             │ │            │ │                            │
│Manages:     │ │Manages:    │ │Manages:                    │
│• Sort mode  │ │• ListView  │ │• File upload               │
│• Sort order │ │  state     │ │• Directory upload          │
│             │ │            │ │• Batch operations:         │
│             │ │            │ │  - Delete                  │
│             │ │            │ │  - Download                │
│             │ │            │ │  - Move                    │
│             │ │            │ │• Progress dialogs          │
│             │ │            │ │• Error handling            │
└─────────────┘ └────────────┘ └────────────────────────────┘

┌────────────────────────────────┐ ┌──────────────────────────────┐
│  FileContextMenuController     │ │ DirectoryContextMenuController│
│                                │ │                              │
│  Actions:                      │ │  Actions:                    │
│  • Open file                   │ │  • Open directory            │
│  • Delete file                 │ │  • Delete directory          │
│  • Rename file                 │ │  • Rename directory          │
│  • Move file                   │ │  • Move directory            │
│  • Authorize                   │ │  • Authorize                 │
│  • View access entries         │ │  • View access entries       │
│  • Set access rules            │ │  • Set access rules          │
│  • Upload new revision         │ │  • Open directory info       │
│  • View revisions              │ │                              │
│  • Open document info          │ │                              │
└────────────────────────────────┘ └──────────────────────────────┘
```

## Data Flow Diagram

### Loading Directory Contents

```
User Action                 Controller                Utility Function
─────────────────────────────────────────────────────────────────────

[User navigates to folder]
        │
        ▼
    page.run_task()
        │
        ▼
FileExplorerController.action_...()
        │                             (Async)
        ▼
    await get_directory(id, view)  ───────────────┐
        │                                         │
        │                                         ▼
        │                         1. Hide content (progress ring)
        │                         2. do_request("list_directory")
        │                         3. Receive response:
        │                            {
        │                              "folders": [...],
        │                              "documents": [...],
        │                              "parent_id": "..."
        │                            }
        │                         4. Store in view:
        │                            • current_files_data
        │                            • current_directories_data
        │                            • current_parent_id
        │                         5. Call update_file_controls()
        │                                      │
        ├─────────────────────────────────────┘
        │
        ▼
update_file_controls(view, folders, documents, parent_id)
        │
        ├── 1. Clear view.controls = []
        │
        ├── 2. Add parent directory button (if applicable)
        │
        ├── 3. Check selection mode:
        │   │
        │   ├── if selection_mode:
        │   │   ├── Create DirectoryTile (with checkbox)
        │   │   └── Create FileTile (with checkbox)
        │   │
        │   └── else:
        │       ├── Create DirectoryContextMenu
        │       └── Create FileContextMenu
        │
        ├── 4. Extend view.controls with created widgets
        │
        └── 5. view.update() ──────────► UI Refresh
```

### Selection Mode Toggle

```
User Action                 Component               View Update
───────────────────────────────────────────────────────────────

[User clicks select button]
        │
        ▼
ExplorerTopBar.on_selection_toggle_click()
        │
        ├── 1. file_listview.toggle_selection_mode(True)
        │           │
        │           ├── Set selection_mode = True
        │           └── Call update_file_controls() ─────┐
        │                                                │
        ├── 2. selection_toolbar.visible = True         │
        │                                                │
        ├── 3. selection_toggle_button.visible = False  │
        │                                                │
        ├── 4. update() calls on components             │
        │                                                │
        └────────────────────────────────────────────────┼─►
                                                         │
                    ┌────────────────────────────────────┘
                    │
                    ▼
        update_file_controls() rebuilds list:
                    │
                    ├── Destroy all context menu wrappers
                    │
                    ├── Create DirectoryTile with checkboxes
                    │
                    ├── Create FileTile with checkboxes
                    │
                    └── Attach selection change callbacks
```

### Batch Operations Flow

```
User selects items          SelectionToolbar        Controller          Service
──────────────────────────────────────────────────────────────────────────────

[Check items]
    │
    ├── Tile.on_checkbox_change()
    │       │
    │       ├── Update is_selected
    │       └── Call on_selection_changed(id, selected)
    │                   │
    │                   └── Add/remove from selected_*_ids set
    │                       Update toolbar selection count
    │
[Click Download button]
    │
    ▼
SelectionToolbar.on_download_click()
    │
    ▼
FileExplorerController.action_batch_download()
    │
    ├── 1. Get selected IDs from view
    │
    ├── 2. Show BatchProgressDialog
    │
    ├── 3. Call batch_download_items() ────────────┐
    │       (async generator)                      │
    │                                               ▼
    │                               For each item:
    │                               ├── get_document()
    │                               └── Add to DownloadManagerService
    │                                          │
    │                                          ├── Queue download task
    │                                          ├── Yield progress
    │                                          └── Continue in background
    │
    ├── 4. Update progress dialog with each yield
    │
    ├── 5. Show completion message
    │
    └── 6. Exit selection mode
            │
            └── toggle_selection_mode(False)
                    │
                    └── Rebuild list without checkboxes
```

## Key Imperative Pattern: `update_file_controls()`

```
┌───────────────────────────────────────────────────────────────┐
│  update_file_controls(view, folders, documents, parent_id)    │
│  Location: include/ui/util/file_controls.py                   │
└───────────────────────────────────────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  view.controls = []           │  ⚠️ DESTROY ALL WIDGETS
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  Add parent button if needed  │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  if selection_mode:           │
            │    Build tiles with checkboxes│
            │  else:                        │
            │    Build context menu wrappers│
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  view.controls.extend([...])  │  ⚠️ CREATE NEW WIDGETS
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  view.update()                │  ⚠️ FORCE UI UPDATE
            └───────────────────────────────┘

Called by:
• get_directory() - After loading folder contents
• sort_files() - After sorting
• toggle_selection_mode() - Mode change
• select_all() / clear_selection() - Selection changes
• Refresh operations
```

## Permission-Based Rendering

```
┌────────────────────────────────────────────────────────┐
│            ContextMenu2._build_controls()              │
│         include/ui/controls/menus/base.py              │
└────────────────────────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────┐
        │  For each menu item in menu_items │
        └───────────────┬───────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────┐
        │  Check if "require" key exists    │
        └───────────────┬───────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────┐
        │  required_perms = item["require"] │
        │  user_perms = app_shared.         │
        │               user_permissions     │
        └───────────────┬───────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────┐
        │  if required_perms.issubset(      │
        │     user_perms):                  │
        │    ✅ Include menu item           │
        │  else:                            │
        │    ❌ Exclude menu item           │
        └───────────────────────────────────┘

Example:
{
  "icon": ft.Icons.DELETE,
  "content": "Delete",
  "on_click": handler,
  "require": {"delete_document"}  ← Checked against user permissions
}
```

---

**Legend:**
- 📁 Directory
- 📄 File/Document
- ⭐ Favorite/Starred
- ☑ Checked checkbox
- ☐ Unchecked checkbox
- ⚠️ Critical imperative operation
- ✅ Permission granted
- ❌ Permission denied
