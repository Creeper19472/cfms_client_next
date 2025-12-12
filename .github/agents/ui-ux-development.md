---
name: CFMS Client UI/UX Developer
description: Expert in developing user interfaces using the Flet framework for CFMS Client NEXT, covering UI components, views, models, navigation, and layout patterns.
---

## Flet Framework Overview

CFMS Client NEXT is built on **Flet** (version ≥0.70.0.dev6671), a Python framework that enables building interactive multi-platform applications using Flutter-based controls. The UI is entirely declarative and follows a component-based architecture.

### Flet-Model Library Integration
The application uses the `flet-model` library for routing and view management:
- **Models**: Route handlers with lifecycle management
- **Router**: Navigation and route management
- **Decorators**: `@route()` decorator for defining routes

## UI Directory Structure

```
include/ui/
├── constants.py              # UI-related constants
├── controls/                 # Reusable UI components
│   ├── buttons/
│   │   └── upgrade.py        # FloatingUpgradeButton
│   ├── components/           # Complex composite components
│   │   ├── about.py          # About page component
│   │   ├── homepage.py       # HomeView, HomeNavigationBar
│   │   ├── rulemanager.py    # Rule management UI
│   │   ├── explorer/         # File explorer components
│   │   │   ├── bar.py        # ExplorerTopBar, FileSortBar
│   │   │   └── ...
│   │   ├── visualmgr/        # Visual management components
│   │   └── wizards/          # Setup wizards
│   ├── contextmenus/
│   │   ├── explorer.py       # File explorer context menus
│   │   └── management.py     # Management context menus
│   ├── dialogs/              # Dialog implementations
│   │   ├── base.py           # AlertDialog base class
│   │   ├── explorer.py       # Explorer-related dialogs
│   │   ├── upgrade.py        # Update dialogs
│   │   ├── wait.py           # Progress/wait dialogs
│   │   ├── whatsnew.py       # Changelog dialogs
│   │   ├── dev.py            # Developer tools dialog
│   │   ├── admin/            # Admin-specific dialogs
│   │   ├── selection/        # Selection dialogs
│   │   └── contextmenu/      # Context menu dialogs
│   ├── menus/                # Menu implementations
│   │   ├── base.py           # Base menu classes
│   │   ├── explorer.py       # File explorer menus
│   │   └── admin/            # Admin menus
│   ├── views/                # Main view components
│   │   ├── connect.py        # Connection view
│   │   ├── login.py          # Login view
│   │   ├── explorer.py       # File explorer view
│   │   ├── more.py           # More/settings view
│   │   └── admin/            # Admin views
│   └── placeholder.py        # Placeholder components
├── models/                   # Route models (Flet-Model)
│   ├── connect.py            # @route("connect")
│   ├── login.py              # @route("login")
│   ├── home.py               # @route("home")
│   ├── manage.py             # Management routes
│   ├── about.py              # About page route
│   ├── debugging.py          # Debug view route
│   ├── settings/             # Settings page routes
│   │   ├── overview.py       # Settings overview
│   │   ├── connection.py     # Connection settings
│   │   ├── language.py       # Language settings
│   │   └── safety.py         # Safety settings
│   └── wizards/
│       └── welcome.py        # Welcome wizard
└── util/                     # UI utility functions
    ├── file_controls.py      # File list UI helpers
    ├── group_controls.py     # Group UI helpers
    ├── notifications.py      # Snackbar/notification helpers
    ├── user_controls.py      # User UI helpers
    ├── path.py               # Path display utilities
    ├── quotes.py             # Quote generation
    └── route.py              # Route utilities
```

## UI Architecture Patterns

### 1. Model-View-Controller Pattern

**Models** (`include/ui/models/`):
- Decorated with `@route()` to define URL routes
- Extend `flet_model.Model` base class
- Configure layout properties (alignment, padding, spacing)
- Define `controls` list for view content
- Can set `appbar`, `navigation_bar`, `floating_action_button`

Example:
```python
@route("connect")
class ConnectToServerModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment = ft.CrossAxisAlignment.CENTER
    padding = 20
    spacing = 10
    
    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)
        self.appbar = ft.AppBar(title=ft.Text("Title"))
        self.controls = [MyView()]
        
    def post_init(self) -> None:
        # Called after initialization
        pass
```

**Views** (`include/ui/controls/views/`):
- Extend Flet controls (ft.Column, ft.Container, etc.)
- Contain layout and UI structure
- Often reference a controller for business logic

**Controllers** (`include/controllers/`):
- Extend `BaseController[T]` where T is the view type
- Handle user interactions and business logic
- Access AppConfig singleton for state

### 2. Component Composition

Complex UI components are built by composing simpler Flet controls:

```python
class FileListView(ft.ListView):
    def __init__(self, parent_manager: "FileManagerView", ref=None, visible=True):
        super().__init__(ref=ref, visible=visible, expand=True)
        self.parent_manager = parent_manager
        
        # Component-specific state
        self.current_parent_id: str | None = None
        self.current_files_data: list[dict] = []
```

### 3. Dialog Pattern

All dialogs extend `AlertDialog` base class from `include/ui/controls/dialogs/base.py`:

```python
class CreateDirectoryDialog(AlertDialog):
    def __init__(self, parent_manager, ref=None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.controller = CreateDirectoryDialogController(self)
        
        self.title = ft.Text(_("Create Directory"))
        self.content = ft.Column([...])
        self.actions = [submit_button, cancel_button]
        
    def disable_interactions(self):
        # Disable UI during async operations
        
    def enable_interactions(self):
        # Re-enable UI after async operations
```

**Dialog Interaction Pattern**:
1. Show progress ring and disable inputs during async operations
2. Use `yield` in async event handlers to update UI incrementally
3. Call controller methods via `page.run_task()` for long operations
4. Use `page.show_dialog()` and `dialog.close()` for display

### 4. Navigation Patterns

**Route Navigation**:
```python
# Push new route
await self.page.push_route("/connect")
await self.page.push_route(self.page.route + "/settings")

# Current route
current_route = self.page.route
```

**Tab Navigation** (BottomNavigationBar):
```python
class HomeNavigationBar(ft.NavigationBar):
    def __init__(self, parent_view, views):
        self.parent_view = parent_view
        self.views = views
        
        destinations = [
            ft.NavigationBarDestination(icon=ft.Icons.FOLDER, label="Files"),
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.MORE_HORIZ, label="More"),
        ]
        super().__init__(destinations=destinations, on_change=self.on_tab_change)
```

## Key UI Components

### File Explorer (`FileManagerView`)
Located in `include/ui/controls/views/explorer.py`:

**Components**:
- `FilePathIndicator`: Breadcrumb-style path display
- `FileListView`: Scrollable list of files and directories
- `ExplorerTopBar`: Action buttons (upload, create, etc.)
- `FileSortBar`: Sorting controls

**Features**:
- File/directory listing with sorting (by name, date, size)
- File upload/download with progress tracking
- Context menus for files and directories
- Drag-and-drop support (where available)
- Batch operations

### Home Navigation
Located in `include/ui/controls/components/homepage.py`:

**Structure**:
- `HomeView`: Central home page content
- `HomeNavigationBar`: Bottom navigation between Files, Home, More
- Uses tab-based navigation to switch between views

### Dialogs

**Common Dialog Types**:
1. **Alert Dialogs**: Simple OK/Cancel confirmations
2. **Progress Dialogs**: Show progress rings during operations
3. **Form Dialogs**: Input forms (CreateDirectoryDialog, etc.)
4. **Selection Dialogs**: Choice/picker dialogs

**Example - Progress Dialog Pattern**:
```python
class BatchUploadFileAlertDialog(AlertDialog):
    def __init__(self, progress_column, stop_event):
        super().__init__()
        self.title = ft.Text(_("Uploading Files"))
        self.content = progress_column  # Contains ProgressBar + Text
        self.actions = [
            ft.TextButton(_("Stop"), on_click=self.stop_upload)
        ]
```

## Layout and Styling

### Theme Configuration (main.py)
```python
page.theme_mode = ft.ThemeMode.DARK
page.theme = ft.Theme(
    scrollbar_theme=ft.ScrollbarTheme(thickness=0.0),
    snackbar_theme=ft.SnackBarTheme(
        show_close_icon=True,
        behavior=ft.SnackBarBehavior.FLOATING,
    ),
    font_family="Source Han Serif SC Regular",
)

# Gradient background
page.decoration = ft.BoxDecoration(
    gradient=ft.LinearGradient(
        begin=ft.Alignment.TOP_LEFT,
        end=ft.Alignment.BOTTOM_RIGHT,
        colors=["#10162c", "#0c2749", "#0f0f23", "#1a1a2e"],
        tile_mode=ft.GradientTileMode.MIRROR,
    )
)
```

### Common Layout Patterns

**Centered Content**:
```python
vertical_alignment = ft.MainAxisAlignment.CENTER
horizontal_alignment = ft.CrossAxisAlignment.CENTER
```

**Responsive Sizing**:
```python
ft.Container(expand=True)           # Expand to fill available space
ft.Column(scroll=ft.ScrollMode.AUTO) # Enable scrolling
```

**Safe Areas** (Mobile):
```python
ft.SafeArea(ft.Container())  # Respects device notches/insets
```

## UI Utilities

### Notifications (`include/ui/util/notifications.py`)
```python
send_error(page, message)       # Show error snackbar
send_success(page, message)     # Show success snackbar
send_info(page, message)        # Show info snackbar
```

### File Controls (`include/ui/util/file_controls.py`)
```python
update_file_controls(listview, files_data, directories_data, parent_id)
# Updates file list view with new data
```

### Path Display (`include/ui/util/path.py`)
Utilities for displaying and manipulating path strings in UI.

## Async UI Updates

### Yielding in Event Handlers
Flet supports async generators for incremental UI updates:

```python
async def ok_button_click(self, event):
    yield self.disable_interactions()  # Update UI immediately
    
    # Do async work
    await some_async_operation()
    
    yield self.enable_interactions()   # Update UI again
```

### Running Background Tasks
For long-running operations:

```python
# In event handler
self.page.run_task(self.controller.long_operation, param1, param2)

# In controller
async def long_operation(self, param1, param2):
    # Do work
    # Update page when done
    await self.page.update_async()
```

## Localization in UI

All user-facing strings must be localized:

```python
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

# Usage
ft.Text(_("Hello World"))
ft.TextField(label=_("Username"))
self.title = ft.Text(_("Create Directory"))
```

Translation files are in `include/ui/locale/`:
- `en/LC_MESSAGES/` - English
- `zh_CN/LC_MESSAGES/` - Simplified Chinese
- `messages.pot` - Template for translators

## Mobile-Specific Considerations

### Permissions (`flet_permission_handler`)
```python
from flet_permission_handler import PermissionHandler

ph_service = PermissionHandler(page)
# Request permissions as needed
```

### Platform Detection
```python
if page.web:
    # Web-specific code
    await page.browser_context_menu.disable()
```

### File Pickers
```python
file_picker = ft.FilePicker()

# Use file picker
result = await file_picker.pick_files(allow_multiple=True)
```

## Best Practices

1. **State Management**: Keep state in models or AppConfig, not in UI controls
2. **Async Updates**: Always use async/await for I/O operations
3. **Update Calls**: Call `update()` after modifying control properties
4. **Refs**: Use `ft.Ref()` for accessing controls from event handlers
5. **Type Hints**: Specify event types: `ft.Event[ft.Button]`
6. **Localization**: Never hardcode UI strings; always use `_()`
7. **Responsive Design**: Use `expand=True` and proper alignment
8. **Error Handling**: Show user-friendly error messages via snackbars
9. **Progress Feedback**: Show progress indicators for long operations
10. **Accessibility**: Provide tooltips and proper labels

## Common UI Patterns

### Loading State
```python
async def load_data(self):
    self.progress_ring.visible = True
    self.content.visible = False
    self.update()
    
    data = await fetch_data()
    
    self.content.visible = True
    self.progress_ring.visible = False
    self.update()
```

### Form Validation
```python
async def submit_form(self, event):
    if not self.textfield.value:
        self.textfield.error = _("Field cannot be empty")
        self.update()
        return
    
    self.textfield.error = None
    # Continue with submission
```

### Context Menus
```python
menu_items = [
    ft.MenuItemButton(
        content=ft.Text(_("Download")),
        on_click=self.download_click,
    ),
    ft.MenuItemButton(
        content=ft.Text(_("Delete")),
        on_click=self.delete_click,
    ),
]
```

## Known UI Framework Issues

The `include/issues/` directory contains workarounds for known Flet bugs:
- Check this directory before assuming a UI bug is your code
- Contribute workarounds for newly discovered issues
- Document the Flet version where the issue was observed
