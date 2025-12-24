# Translation Strings for File Overwrite Feature

This document lists the new translation strings that need to be added for the file overwrite interaction feature.

## New Strings Added to Code

The following strings need to be extracted and translated:

### Dialog Title
- **msgid**: `"File Already Exists"`
- **Context**: Title of the confirmation dialog when a file with the same name already exists on the server
- **English**: `File Already Exists`
- **Chinese (Simplified)**: `文件已存在`

### Dialog Content
- **msgid**: `'A file named "{filename}" already exists. Do you want to overwrite it?'`
- **Context**: Message shown to user when a file conflict is detected
- **English**: `A file named "{filename}" already exists. Do you want to overwrite it?`
- **Chinese (Simplified)**: `名为"{filename}"的文件已存在。是否覆盖？`
- **Note**: `{filename}` is a placeholder that will be replaced with the actual filename

### Button Labels
- **msgid**: `"Overwrite"`
- **Context**: Button to confirm overwriting the existing file
- **English**: `Overwrite`
- **Chinese (Simplified)**: `覆盖`

- **msgid**: `"Skip"`
- **Context**: Button to skip uploading this file and continue with the next one
- **English**: `Skip`
- **Chinese (Simplified)**: `跳过`

## Extraction and Compilation Steps

To add these translations to the project:

1. **Extract strings** from Python files:
   ```bash
   cd /home/runner/work/cfms_client_next/cfms_client_next
   find src -name "*.py" -exec pygettext -d messages -o src/include/ui/locale/messages.pot {} +
   ```

2. **Update existing translation files**:
   ```bash
   msgmerge --update src/include/ui/locale/zh_CN/LC_MESSAGES/client.po src/include/ui/locale/messages.pot
   msgmerge --update src/include/ui/locale/en/LC_MESSAGES/client.po src/include/ui/locale/messages.pot
   ```

3. **Manually edit the .po files** to add translations for the new strings

4. **Compile the translations**:
   ```bash
   msgfmt src/include/ui/locale/zh_CN/LC_MESSAGES/client.po -o src/include/ui/locale/zh_CN/LC_MESSAGES/client.mo
   msgfmt src/include/ui/locale/en/LC_MESSAGES/client.po -o src/include/ui/locale/en/LC_MESSAGES/client.mo
   ```

## Feature Overview

The file overwrite feature adds user interaction when uploading a file that already exists on the server:

1. When `create_document` returns a 409 (Conflict) response, the system checks:
   - Is the conflict type "document"? (not "directory")
   - Do we have the ID of the existing document?

2. If both conditions are met, a dialog is shown with three options:
   - **Overwrite**: Upload as a new version using `upload_document` request
   - **Skip**: Skip this file and continue with the next one
   - **Cancel**: Stop the entire upload operation

3. If the conditions aren't met (no ID or conflict is a directory), it's treated as an error.

## Files Modified

- `src/include/ui/controls/dialogs/explorer.py`: Added `FileOverwriteConfirmDialog` class
- `src/include/util/transfer.py`: Modified `batch_upload_file_to_server` to handle 409 responses and call conflict callback
- `src/include/controllers/explorer/itself.py`: Updated both `action_upload` and `action_directory_upload` methods to handle conflicts
