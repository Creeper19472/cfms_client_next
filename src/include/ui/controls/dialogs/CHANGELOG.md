# CFMS Client NEXT - Changelog

This document contains the release history and changelog for CFMS Client NEXT.

---
## v0.5.5
**Released on:** 2026-02-07

**Title:** Avatar Customization

This version introduces the ability to display and modify user avatars, and 
optimizes the login interface display.

---
## v0.5.4
**Released on:** 2026-02-06

**Title:** Improved UI for Denied Attempts

This version introduces a more aesthetically pleasing UI for when access is 
denied and fixes some issues.

### Fixed
- All operations with explicit permission requirements in the context menu 
now have the necessary restrictions to prevent them from appearing in the 
user interface of unauthorized users.
- Dividers appearing at the beginning or end of the context menu will be 
automatically removed, and multiple adjacent dividers will be automatically 
reduced to one.

---
## v0.5.3
**Released on:** 2026-02-04

**Title:** Batch Move Function

This version introduces a batch move feature.

### Improved
- Batch delete operations now support interruption.
- All batch operations now share a single progress dialog implementation, 
improving code reusability.

---
## v0.5.2
**Released on:** 2026-02-04

**Title:** UI Behaviour Fix

This version corrects an issue with the UI when accessing directories, ensuring 
the address tooltip only updates upon successful access. Additionally, it adds 
address tooltip updates to the search navigation section.

### Known issues
- After quickly navigating to a directory, and then performing other directory 
switching operations, the leftmost side of the address bar may display two 
forward slashes (instead of one).

---
## v0.5.1
**Released on:** 2026-02-04

**Title:** Multiple Selection Feature

This version adds support for multi-option items and is compatible with 
server-side protocols version 7.

---
## v0.5.0
**Released on:** 2026-02-03

**Title:** Revision Management Feature

This version adds the ability to manage revisions.

### Improved
- Added separator lines for the options in the document's right-click menu.
- When renaming a document or directory, if the name is not actually changed, 
no request is sent to the server, thus avoiding error messages.

### Fixed
- Fixed an issue where the automatic version checker's checking 
strategy did not match user preferences, and corrects the version comparison 
logic.

---
## v0.4.16
**Released on:** 2026-02-02

**Title:** Renaming Interface Improvement

This version introduces a minor optimization to the renaming interface, so that 
the original name of the object now appears in the text box and can be selected 
in full, making it easier for users to make changes.

---
## v0.4.15
**Released on:** 2026-01-11

**Title:** Update Translations

This version translates some previously untranslated strings.

---
## v0.4.14
**Released on:** 2026-01-10

**Title:** Enhanced Upgrade Check

This version includes patch updates and improvements.

---
## v0.4.13
**Released on:** 2026-01-10

**Title:** Separate Task Lists

This version adjusts the way the transfer task list is stored, so that each user 
at each server address has their own independent storage file.

---
## v0.4.12
**Released on:** 2026-01-10

**Title:** Patch release

This version includes patch updates and improvements.

---
## v0.4.11
**Released on:** 2026-01-10

**Title:** Enhanced UI

This version makes minor adjustments to some UI elements and corrects an issue 
with the "Open" button displaying completed tasks. The file download location 
has also been changed; on mobile devices, it has now been moved back to the 
app's internal storage. To access downloaded files, please use the button 
within the app.

---
## v0.4.10
**Released on:** 2026-01-08

**Title:** Channel Selector For Updates

This version includes patch updates and improvements.

---
## v0.4.9
**Released on:** 2026-01-08

**Title:** Improve Open Button Display

This version enables open button for desktop environments.

---
## v0.4.8
**Released on:** 2026-01-05

**Title:** Patch release

This version includes patch updates and improvements.

---
## v0.4.7
**Released on:** 2025-12-30

**Title:** Translations

This version includes patch updates and improvements.

---
## v0.4.6
**Released on:** 2025-12-28

**Title:** Fix Rule Editor

This version fixes the issue where the rule editor's content wasn't being 
updated in a timely manner.

---
## v0.4.5
**Released on:** 2025-12-28

**Title:** Patch release

This version includes patch updates and improvements.

---
## v0.4.4
**Released on:** 2025-12-28

**Title:** Patch release

This version includes patch updates and improvements.

---
## v0.4.3
**Released on:** 2025-12-27

**Title:** Patch release

This version includes patch updates and improvements.

---
## v0.4.2
**Released on:** 2025-12-26

**Title:** Introducing Search Function

This version adds a search function for the file explorer,
allowing users to search for files and directories.

Need server-side support.

---
## v0.4.1
**Released on:** 2025-12-26

**Title:** Force-IPv4 Options

This version allows users to force a connection to a remote address using the 
IPv4 protocol to bypass IPv6 blocking issues.

This version also fixes an issue with changelog parsing, ensuring that a 
paragraph of text is correctly treated as a single line.

---
## v0.4.0
**Released on:** 2025-12-25

**Title:** Minor release

This version adds various features for the client, including file overwriting 
logic, new group management context menus and so on.

A series of fixes has also been introduced.

**Note:** Starting with this version, enabling/disabling two-step verification 
will be temporarily disabled on mobile devices. This is due to a technical 
issue that is currently difficult to resolve. However, the application still 
supports login operations that require two-step verification.

---
## v0.3.4
**Released on:** 2025-12-24

**Title:** 2FA UI Improvements

This version adds extra user interface to allow users to use recovery codes 
(backup codes) instead.

---
## v0.3.3
**Released on:** 2025-12-24

**Title:** Introducing 2FA

This version adds 2FA support (only TOTP for now) for the client.

---
## v0.3.2
**Released on:** 2025-12-23

**Title:** Download Manager Service & UI Interface

This version introduces a new download manager service to handle multiple 
download tasks, making `Tasks` view usable.

A fix has also been introduced for an issue in file upload action.

---
## v0.3.1
**Released on:** 2025-12-23

**Title:** Add Auto-Update Service

This version adds a new architecture for background services and an 
auto-update service, enabling the software to automatically check for new 
updates and notify users.

---
## v0.3.0
**Released on:** 2025-12-22

**Title:** Minor release

This version includes minor updates and improvements.

---
## v0.2.40
**Released on:** 2025-12-22

**Title:** Patch release

This version includes patch updates and improvements.

---
## v0.2.39
**Released on:** 2025-12-12

**Title:** Patch release

This version includes patch updates and improvements.

---

## v0.2.38  
**Released on:** 2025-12-12

**Title:** Authorization Dialog Improvements

This version improved the UI logic of the authorization dialog, allowing users  
without `list_users` or `list_groups` permissions to specify entity without  
searching.

---

## v0.2.37  
**Released on:** 2025-12-12

**Title:** Authorize Dialogs & Improved CHANGELOG Parsing

This version adds a dialog box for granting permissions to specific entities  
and makes adjustments to the storage and parsing of changelogs.

---

## v0.2.36  
**Released on:** 2025-11-19

**Title:** Add to Favourites Button for Documents & Directories

This version adds an 'Add to Favourites' button for documents and directories.  
A variety of bug fixes and performance improvements have also been implemented.

---

## v0.2.33  
**Released on:** 2025-11-12

**Title:** User Management Context Menu Rewrite & PasswdDialog Improvements

This version rewrites the user management context menu, and added more options  
for PasswdDialog to enable sysops to have more control when resetting user  
passwords.

---

## v0.2.29  
**Released on:** 2025-11-07

**Title:** Bug fixes

This version fixes an issue that prevented re-connection logic from working.

---

## v0.2.27  
**Released on:** 2025-11-06

**Title:** Introduction of New Context Menu & Bug fixes

This version introduces a new context menu for items in the explorer, aiming  
to enhance user experience and fix the lasting bug that dialogs fail to be  
displayed in certain situations.

---

## v0.2.26  
**Released on:** 2025-11-05

**Title:** Bug fixes

This version modifies the root path detection logic, trying to fix i18n issues.

---

## v0.2.25  
**Released on:** 2025-11-04

**Title:** Bug fixes

This version adds a debugging interface accessible from the about page,  
allowing users to view detailed debug information. In addition, this version  
makes minor modifications to the exception handling logic for connection  
interruptions in an attempt to resolve the issue of reconnection failing to  
work.

---

## v0.2.24  
**Released on:** 2025-11-03

**Title:** Explorer Improvements & Bug fixes

This version adds the sorting function for the explorer, supporting various  
sorting modes. An issue in the about page is also fixed.

---

## v0.2.22  
**Released on:** 2025-11-02

**Title:** Refactor Code Structure & Bug fixes

This version refactors the code structure of the file explorer, meanwhile  
adding a new section in the About page to display test build information.

What's more, this version improves the logic of making requests, adding retry  
attempts when network errors occur.

Some issues are found and pending to be fixed in future updates.

---

## v0.2.21  
**Released on:** 2025-11-01

**Title:** Bug fixes

This version corrects an issue where File Explorer still displayed the  
"Parent Directory" button when setting a new root directory via the "Jump To"  
function, causing inconsistencies with `FilePathIndicator` control.

---

## v0.2.20  
**Released on:** 2025-10-28

**Title:** Visual Rule Editor Improvements

This version improves the visual rule editor by ensuring that changes made in  
the visual editor are accurately reflected in the source code editor and vice  
versa.

Fixes:  
- Synchronization between visual and source code editors  
- Editor not updating when directly submitting changes from visual rule editor  
- Index error when adding new sub-rule groups  
- Assertion errors when checking the type of `controls`

---

## v0.2.17  
**Released on:** 2025-10-19

**Title:** Multilingual Support Added

This version adds multilingual support to the application, allowing users to  
switch between different languages according to their preferences.

---

## v0.2.16  
**Released on:** 2025-10-18

**Title:** Bug fixes

This version fixes a variety of issues.

---

## v0.2.15  
**Released on:** 2025-10-17

**Title:** Improved Code Structures

This version added Controllers to separate the UI and logic, improving code  
readability and maintainability.

---

## v0.2.14  
**Released on:** 2025-10-11

**Title:** Add Connection Settings

This version adds some new connection settings that allow you to adjust the  
configuration of the application using the proxy.

---

## v0.2.12  
**Released on:** 2025-10-10

**Title:** Major Feature Reintroduction Complete

Starting with this version, all the basic functionality that was already  
implemented in the old code branch has been reintroduced.

In addition to some silent features that are still waiting to be reintroduced,  
the following known issues are still waiting to be resolved:

- Significant lag when loading large amounts of data due to flet-datatable2  
- When different dialog boxes are switched, the latter dialog box may not be  
    displayed  
- Minor issues with the updater

---

## v0.2.11  
**Released on:** 2025-10-09

**Title:** Restoring Full Functionality of the Group Management Interface

This version completes the functionality of the user group management  
interface that was already available in previous code branches. At the same  
time, the storage structure of some codes has also been adjusted.

---

## v0.2.10  
**Released on:** 2025-10-08

**Title:** Re-introducing Group Management Interface & Improvements

This version reintroduces some features of the user group management  
interface and optimizes the updater logic so that it will check the local  
cache before starting to download the update package.

---

## v0.2.9  
**Released on:** 2025-10-07

**Title:** Re-introducing Features for Development & Bug Fixes

This version reintroduces several debugging features and resolves an issue  
where exiting the app with the back key on a mobile device would cause a  
crash on the next initial launch.

---

## v0.2.8  
**Released on:** 2025-10-06

**Title:** Bug fixes

This version fixes a typo in the code that caused the updater to refuse to  
check for updates in production environments. At the same time, new entrances  
to view historical release notes have been added to the "What's New" dialog  
and the "About" page to view past updates.

---

## v0.2.7  
**Released on:** 2025-10-06

**Title:** Bug fixes

This version fixes several issues with the app's built-in auto-updater, and  
now updates can be performed and displayed normally.

---

## v0.2.6  
**Released on:** 2025-10-06

**Title:** Bug fixes

This version corrects the application's compilation settings, which is  
expected to enable it to run on Android API 24 and above.

---

## v0.2.4  
**Released on:** 2025-10-05

**Title:** Bug fixes

This release introduces upstream fixes to the flet-open-file package, which  
is expected to resolve compilation failures that have persisted for the past  
few releases and make the updater experience smoother on mobile devices.

---

## v0.2.3  
**Released on:** 2025-10-05

**Title:** Re-introducing Management Interfaces

Starting from this version, the functionality of the management interface  
will be gradually reintroduced.

---

## v0.2.2  
**Released on:** 2025-10-04

**Title:** Introducing What's New Dialog

From now on, a What's New dialog will be displayed when the app is upgraded  
from older versions or newly installed.

---

## v0.2.0  
**Released on:** 2025-10-04

**Title:** Introducing The First Version of CFMS Client (NEXT)

This version re-implemented widely-used functions to give more convenience  
to developers.

---
