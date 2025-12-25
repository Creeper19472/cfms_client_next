# File Overwrite Dialog Enhancement

## Overview

The `FileOverwriteConfirmDialog` has been enhanced to display detailed information about existing files when a file upload conflict occurs. This feature provides users with important context before deciding whether to overwrite an existing file.

## Features

### Lazy Loading
- Dialog displays immediately with basic information
- File details load asynchronously in the background
- Progress ring indicates loading state

### Displayed Information
When a file with duplicate name is detected, the dialog shows:
1. **File Size** - Formatted in Bytes/KB/MB with a document icon
2. **Last Modified Date** - When the file was last updated
3. **Created Date** - When the file was originally created

### User Experience
- **Smooth Animation**: Details fade in with a 300ms ease-in-out animation
- **Error Handling**: Graceful fallback if details cannot be loaded
- **Consistent UI**: Follows existing Flet patterns and styling
- **Icon-coded Information**: Each detail has a color-coded icon for quick visual identification

## User Actions

The dialog provides three options:
1. **Overwrite** - Replace the existing file with the new one
2. **Skip** - Skip uploading this file and continue
3. **Cancel** - Cancel the entire upload operation

## Technical Implementation

### API Integration
- Uses existing `get_document_info` API endpoint
- Requests document ID from server
- Parses response for size, dates, and other metadata

### Architecture Pattern
Follows the established Flet-Model pattern:
- `did_mount()` lifecycle hook for initialization
- Async generator with `yield` for incremental UI updates
- Animation configuration using `animate_opacity`
- Proper error handling and fallback states

### File Size Formatting
Automatically formats file sizes for readability:
- 0-1023 bytes: "X Bytes"
- 1KB-1023KB: "X.XX KB"
- 1MB+: "X.XX MB"

## Usage

The dialog is automatically shown when uploading files that conflict with existing files. Users will see it during:
- Single file uploads
- Batch file uploads
- Directory uploads

## Code Location

`src/include/ui/controls/dialogs/explorer.py` - `FileOverwriteConfirmDialog` class

## Dependencies

- `flet` - UI framework
- `include.classes.config.AppShared` - Authentication and configuration
- `include.util.requests.do_request` - API communication
- `datetime` - Date formatting

## Translation Support

All user-facing strings are wrapped with `_()` for internationalization:
- Dialog title
- Loading message
- File size label
- Date labels
- Error messages
- Action button labels

Translations will be automatically picked up when translation files are regenerated.
