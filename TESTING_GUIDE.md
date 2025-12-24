# Testing Guide for File Overwrite Feature

This guide describes how to test the file overwrite interaction feature.

## Prerequisites

1. **Running CFMS Server**: You need a working CFMS server instance
2. **Client Configuration**: Client must be connected to the server
3. **Test Files**: Prepare some test files for uploading

## Test Scenarios

### Scenario 1: Normal Upload (No Conflict)
**Purpose**: Verify normal upload still works

**Steps**:
1. Navigate to a directory in the file explorer
2. Upload a file that doesn't exist on the server
3. **Expected**: File uploads successfully without any dialog

**Result**: ✅ Should work normally, no changes to existing behavior

---

### Scenario 2: File Conflict with Read Access - Choose Overwrite
**Purpose**: Test the overwrite functionality

**Steps**:
1. Upload a file (e.g., "test.pdf") to a directory
2. Upload the same file again (same name, possibly different content)
3. **Expected**: Dialog appears with title "File Already Exists"
4. Dialog message: "A file named 'test.pdf' already exists. Do you want to overwrite it?"
5. Click "Overwrite" button
6. **Expected**: File uploads as a new version

**Verification**:
- File should be updated on the server
- Version history should show a new version
- No error messages

**Result**: ✅ File should be overwritten successfully

---

### Scenario 3: File Conflict with Read Access - Choose Skip
**Purpose**: Test skipping a conflicting file

**Steps**:
1. Upload multiple files, where one has a conflict (e.g., "file1.pdf", "existing.pdf", "file3.pdf")
2. When dialog appears for "existing.pdf", click "Skip"
3. **Expected**: Upload continues with "file3.pdf"

**Verification**:
- "existing.pdf" is not updated
- "file1.pdf" and "file3.pdf" are uploaded successfully
- No error messages for skipped file

**Result**: ✅ Conflicting file skipped, others uploaded

---

### Scenario 4: File Conflict with Read Access - Choose Cancel
**Purpose**: Test cancelling the entire upload operation

**Steps**:
1. Upload multiple files, where one has a conflict
2. When dialog appears, click "Cancel"
3. **Expected**: All remaining uploads are stopped

**Verification**:
- Upload dialog closes
- Files after the conflict are not uploaded
- No error messages

**Result**: ✅ Upload operation cancelled cleanly

---

### Scenario 5: File Conflict Without Read Access
**Purpose**: Test behavior when user lacks read access to existing file

**Server Setup**:
- Create a file owned by another user
- Ensure test user has no read permission on it
- Ensure test user can write to the parent directory

**Steps**:
1. Try to upload a file with the same name as the inaccessible file
2. **Expected**: Error message, no dialog

**Verification**:
- No dialog appears
- Error message: "Failed to create document 'filename': [server message]"
- Upload fails gracefully

**Result**: ✅ Error reported, no dialog shown

---

### Scenario 6: Directory Name Conflict
**Purpose**: Test behavior when a directory has the same name

**Steps**:
1. Create a directory named "reports"
2. Try to upload a file named "reports.pdf" to the parent directory
3. **Expected**: Error message, no dialog

**Verification**:
- No dialog appears (cannot overwrite directory with file)
- Error message indicating the conflict
- Upload fails gracefully

**Result**: ✅ Error reported, no overwrite option

---

### Scenario 7: Batch Upload with Mixed Scenarios
**Purpose**: Test complex scenario with multiple files and conflicts

**Steps**:
1. Prepare files: "new1.pdf", "existing1.pdf" (already on server), "new2.pdf", "existing2.pdf" (already on server)
2. Upload all four files at once
3. For "existing1.pdf" dialog, choose "Overwrite"
4. For "existing2.pdf" dialog, choose "Skip"
5. **Expected**: 
   - "new1.pdf" uploads normally
   - "existing1.pdf" overwrites
   - "new2.pdf" uploads normally
   - "existing2.pdf" skips

**Verification**:
- Final state: 3 files uploaded successfully (new1, existing1, new2)
- 1 file skipped (existing2)
- Batch upload dialog shows correct progress

**Result**: ✅ Mixed scenario handled correctly

---

### Scenario 8: Directory Upload with Conflict
**Purpose**: Test directory upload conflict handling

**Steps**:
1. Create a directory structure locally:
   ```
   mydir/
     ├── file1.txt
     ├── file2.txt (already exists on server)
     └── subdir/
         └── file3.txt
   ```
2. Upload the directory
3. When conflict dialog appears for "file2.txt", choose "Overwrite"
4. **Expected**: Directory tree created, file2.txt overwritten

**Verification**:
- All directories created
- file1.txt and file3.txt uploaded
- file2.txt overwritten with new version
- No errors

**Result**: ✅ Directory upload with conflict handled

---

### Scenario 9: Network Error During Overwrite
**Purpose**: Test error handling during upload_document request

**Steps**:
1. Upload file with conflict
2. Choose "Overwrite"
3. Simulate network interruption (disconnect server or client)
4. **Expected**: Error message, retry mechanism activates

**Verification**:
- Error reported to user
- Retry happens automatically (up to max_retries)
- If retries exhausted, clear error message shown

**Result**: ✅ Network errors handled gracefully

---

### Scenario 10: Malformed Server Response
**Purpose**: Test defensive checks against bad server responses

**This would require server modification or mocking**

**Test Cases**:
- 409 response missing "type" field → should show error
- 409 response missing "id" field → should show error
- 200 response missing "task_data" → should show error with clear message
- 200 response with empty "task_id" → should show error with clear message

**Result**: ✅ All defensive checks prevent KeyError

---

## Expected UI Behavior

### Dialog Appearance
- **Title**: "File Already Exists"
- **Message**: "A file named '{filename}' already exists. Do you want to overwrite it?"
- **Buttons**: 
  - "Overwrite" (primary action)
  - "Skip" (secondary action)
  - "Cancel" (dismissive action)
- **Modal**: Yes (user must choose)

### Progress Display
- During batch upload, progress bar continues updating
- File count updates: "[2/5] 1.5 MB/2.0 MB"
- Skipped files don't show in progress
- Errors accumulate in error column

### Error Messages
Examples of error messages that should appear:
- "Upload failed: No permission to upload files" (403)
- "Failed to create document 'file.pdf': File already exists" (409 without ID)
- "Failed to create document 'file.pdf': Name conflicts with directory" (409 type=directory)
- "Internal error: Missing task_id for file 'file.pdf'" (malformed response)

## Localization Testing

After translations are added:

1. Change language to English
2. Verify all dialog text appears in English
3. Change language to Chinese
4. Verify all dialog text appears in Chinese
5. Verify placeholders like {filename} are replaced correctly

**Strings to verify**:
- ✅ "File Already Exists"
- ✅ "A file named \"{filename}\" already exists. Do you want to overwrite it?"
- ✅ "Overwrite"
- ✅ "Skip"
- ✅ "Cancel" (already translated)
- ✅ "Internal error: Missing task_id for file \"{filename}\""

## Regression Testing

Verify these existing features still work:

1. ✅ Single file upload (no conflict)
2. ✅ Batch file upload (no conflicts)
3. ✅ Directory upload (no conflicts)
4. ✅ Upload progress display
5. ✅ Upload cancellation (via Cancel button)
6. ✅ Upload error handling (permissions, network issues)
7. ✅ Upload retry mechanism

## Performance Considerations

- Dialog should appear quickly (< 1 second)
- No blocking during file upload
- Large file uploads should show smooth progress
- Multiple conflicts should each show dialog sequentially

## Accessibility

- Dialog should be keyboard accessible
- Tab order: Overwrite → Skip → Cancel
- Enter key should trigger focused button
- Escape key should trigger Cancel

## Security Considerations

- ✅ User cannot overwrite files they don't have read access to
- ✅ User cannot overwrite directories
- ✅ Permissions checked on server side
- ✅ No information leak about existing files without read access

## Known Limitations

1. **Translation strings**: Need to be extracted and compiled before localization works
2. **Testing requirements**: Needs live server with proper 409 response implementation
3. **UI testing**: Best tested manually with real UI, not unit tests

## Success Criteria

The feature is working correctly if:

1. ✅ Normal uploads work without any changes
2. ✅ Conflicts are detected and user is prompted
3. ✅ Overwrite successfully uploads new version
4. ✅ Skip successfully bypasses conflicting file
5. ✅ Cancel stops all remaining uploads
6. ✅ Errors are handled gracefully with clear messages
7. ✅ No KeyError or unhandled exceptions
8. ✅ Backward compatibility maintained
9. ✅ All defensive checks work correctly
10. ✅ UI is responsive and user-friendly
