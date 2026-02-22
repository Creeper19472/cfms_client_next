---
name: CFMS Localization & Internationalization Expert
description: Expert in internationalization (i18n) and localization (l10n) for CFMS Client NEXT, covering translation management, locale detection, gettext integration, and multi-language support.
---

## Internationalization Overview

CFMS Client NEXT uses **GNU gettext** for internationalization, supporting multiple languages with translation files. The system allows dynamic language switching and provides fallback to default language.

### Supported Languages

Currently supported:
- **Chinese (Simplified)**: `zh_CN` (default)
- **English**: `en` (fallback; uses `NullTranslations` if no `.mo` file found)

Translation files located in: `include/ui/locale/`

## Gettext Architecture

### Translation System Components

1. **Translation Files** (`.po` and `.mo`):
   - `.pot`: Portable Object Template (source for translators)
   - `.po`: Portable Object (human-readable translations)
   - `.mo`: Machine Object (compiled binary for runtime)

2. **Directory Structure**:
```
include/ui/locale/
├── messages.pot          # Translation template
└── zh_CN/
    └── LC_MESSAGES/
        ├── client.po     # Chinese translations
        └── client.mo     # Compiled Chinese
```

Note: The gettext domain is `"client"` (not `"messages"`), so the files are named `client.po` / `client.mo`.

### Locale Path Configuration

**Location**: `include/constants.py`

```python
ROOT_PATH = Path(CONSTANT_FILE_ABSPATH).resolve().parent.parent
LOCALE_PATH = f"{ROOT_PATH}/include/ui/locale"
```

## Translation Management

### Translation Singleton

**Location**: `include/util/locale.py`

The translation system uses a `DelegatingTranslation` singleton proxy that supports live language switching at runtime:

```python
class DelegatingTranslation(gettext.NullTranslations):
    """Singleton translation proxy that delegates to an internal real translation."""
    # Thread-safe singleton; delegates gettext/ngettext calls to internal real translation

def create_translation(language: str = "en", fallback: bool = True):
    """Create a gettext translation for the given language."""
    return gettext.translation(
        "client",                # domain name
        localedir=LOCALE_PATH,
        languages=[language],
        fallback=fallback,
    )

def set_translation(language: str = "en", fallback: bool = True):
    """Update the global DelegatingTranslation to a new language."""
    translation = create_translation(language, fallback)
    DelegatingTranslation().set_real(translation)

def get_translation():
    """Get the singleton DelegatingTranslation instance."""
    return DelegatingTranslation()
```

**Usage Pattern**:
```python
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

# In code
message = _("Hello, World!")
formatted = _("Welcome, {username}").format(username=user)
```

### Initialization in main.py

**Application Startup** (`main.py`):
```python
async def main(page: ft.Page):
    # Load language preference
    try:
        preferred_language = (
            AppShared().preferences.get("settings", {}).get("language", "zh_CN")
        )
        
        # Set environment variable for gettext
        os.environ["LANGUAGE"] = preferred_language
        
        # Set translation singleton
        set_translation(preferred_language)
        
    except Exception as e:
        warnings.warn(f"Failed to load language preferences: {e}", RuntimeWarning)
        os.environ["LANGUAGE"] = "zh_CN"
    
    # Import UI components AFTER setting locale
    from include.ui.models.connect import ConnectToServerModel
    # ... other imports
```

**Critical**: UI imports must come **after** `set_translation()` to ensure all strings use the correct language.

## Dynamic Language Switching

Because `get_translation()` returns a `DelegatingTranslation` proxy singleton, language can be changed at runtime without restarting:

```python
# Switch language at runtime
set_translation("en")  # All subsequent _() calls use English

# All existing references to get_translation() automatically pick up the new language
# because they delegate through the same singleton proxy
```

Existing `t = get_translation()` references do **not** need to be updated — they will automatically use the new translation since they hold a reference to the singleton proxy.

## Using Translations in Code

### Basic Translation

**Simple Strings**:
```python
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

# In UI code
title = _("Connect to Server")
label = _("Username")
error = _("Invalid credentials")
```

### Formatted Strings

**String Formatting**:
```python
# With format()
message = _("Uploaded {count} files").format(count=5)

# With f-strings (not recommended for gettext)
# DON'T: f"Uploaded {count} files"  # Not extractable by gettext
# DO: _("Uploaded {count} files").format(count=count)

# Multiple placeholders
status = _("{current} of {total} completed").format(current=3, total=10)
```

### Plural Forms

**Using ngettext**:
```python
t = get_translation()
_ = t.gettext
n_ = t.ngettext

# Singular/plural handling
message = n_(
    "{count} file selected",
    "{count} files selected",
    count
).format(count=count)
```

**Plural Rules**:
- English: 1 is singular, else plural
- Chinese: No plural forms (same for all counts)
- Defined in `.po` file headers

### Context-Specific Translations

**Using pgettext** (if needed):
```python
# For ambiguous terms that translate differently
# "File" as noun
file_noun = pgettext("noun", "File")

# "File" as verb
file_verb = pgettext("verb", "File")
```

## Translation Workflow

### 1. Extract Strings

Extract translatable strings from Python code:
```bash
# From project root
xgettext --language=Python \
         --keyword=_ \
         --keyword=n_:1,2 \
         --output=src/include/ui/locale/messages.pot \
         --from-code=UTF-8 \
         src/**/*.py
```

Or using `pygettext`:
```bash
find src -name "*.py" -exec pygettext -d client -o src/include/ui/locale/messages.pot {} +
```

### 2. Update Translation Files

Update existing `.po` files with new strings:
```bash
# For Chinese (Simplified)
msgmerge --update \
         src/include/ui/locale/zh_CN/LC_MESSAGES/client.po \
         src/include/ui/locale/messages.pot
```

### 3. Translate

Edit `.po` files manually or with translation tools:

**Example `client.po`**:
```po
# src/include/ui/locale/zh_CN/LC_MESSAGES/client.po
msgid ""
msgstr ""
"Project-Id-Version: CFMS Client NEXT\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Language: zh_CN\n"
"Plural-Forms: nplurals=1; plural=0;\n"

msgid "Connect to Server"
msgstr "连接到服务器"

msgid "Username"
msgstr "用户名"

msgid "Password"
msgstr "密码"

msgid "{count} file selected"
msgid_plural "{count} files selected"
msgstr[0] "已选择 {count} 个文件"
```

**Translation Tools**:
- Poedit (GUI editor)
- Lokalize (KDE)
- Weblate (web-based)
- Manual editing (text editor)

### 4. Compile Translations

Compile `.po` to binary `.mo`:
```bash
# For Chinese (Simplified)
msgfmt src/include/ui/locale/zh_CN/LC_MESSAGES/client.po \
       -o src/include/ui/locale/zh_CN/LC_MESSAGES/client.mo
```

### 5. Test

- Change language preference in settings
- The `DelegatingTranslation` proxy allows switching at runtime (no restart required)
- Verify all strings appear in correct language

## Language Settings UI

### Language Selection

**Settings Model** (`include/ui/models/settings/language.py`):
```python
@route("settings/language")
class LanguageSettingsModel(Model):
    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)
        
        app_shared = AppShared()
        current_lang = app_shared.preferences.get("settings", {}).get(
            "language", "zh_CN"
        )
        
        self.language_dropdown = ft.Dropdown(
            label=_("Language"),
            value=current_lang,
            options=[
                ft.DropdownOption("zh_CN", "简体中文 (Simplified Chinese)"),
                ft.DropdownOption("en", "English"),
                # Add more languages here
            ],
            on_change=self.on_language_changed
        )
        
        self.restart_note = ft.Text(
            _("Language changes take effect after restarting the application"),
            size=12,
            color=ft.colors.GREY_500,
        )
        
        self.controls = [
            self.language_dropdown,
            self.restart_note,
        ]
    
    async def on_language_changed(self, e):
        app_shared = AppShared()
        new_language = self.language_dropdown.value
        
        # Update preference
        if "settings" not in app_shared.preferences:
            app_shared.preferences["settings"] = {}
        app_shared.preferences["settings"]["language"] = new_language
        
        # Save to file
        with open(PREFERENCES_PATH, "w", encoding="utf-8") as f:
            yaml.dump(app_shared.preferences, f, default_flow_style=False)
        
        # Show confirmation
        self.page.show_snack_bar(
            ft.SnackBar(content=ft.Text(_("Language preference saved")))
        )
```

### Dynamic Language Switching

The `DelegatingTranslation` proxy enables live language switching at runtime:
```python
# Switch language at runtime (no restart required)
set_translation("en")
os.environ["LANGUAGE"] = "en"

# All code using get_translation() will immediately use the new language
# because DelegatingTranslation is a singleton proxy
```

**Note**: While the translation system supports runtime switching, any UI strings already rendered need to be rebuilt/refreshed to show the new language. New dialogs/pages opened after switching will use the new language.

## Best Practices

### 1. Always Use Translation Functions

**Good**:
```python
button = ft.TextButton(_("Submit"))
error_text = ft.Text(_("File not found"))
```

**Bad**:
```python
button = ft.TextButton("Submit")  # Hardcoded English
error_text = ft.Text("文件未找到")  # Hardcoded Chinese
```

### 2. Provide Context

**Use descriptive strings**:
```python
# Good - clear context
label = _("Upload file")

# Bad - ambiguous
label = _("Upload")  # Upload what?
```

### 3. Keep Format Placeholders Named

**Good**:
```python
message = _("Welcome, {username}!").format(username=user)
```

**Bad**:
```python
message = _("Welcome, %s!") % user  # Harder for translators
```

### 4. Extract Plurals Properly

**Good**:
```python
message = n_(
    "{count} item",
    "{count} items",
    count
).format(count=count)
```

**Bad**:
```python
message = _("{count} item(s)").format(count=count)  # Unclear for translators
```

### 5. Document String Context

**Add comments for translators**:
```python
# Translators: This appears in the file upload dialog
upload_title = _("Select files to upload")

# Translators: {size} is file size in bytes, {limit} is the max allowed
error = _("File size {size} exceeds limit {limit}").format(
    size=file_size, limit=max_size
)
```

Comments starting with `# Translators:` will be extracted to `.pot` files.

## Common Translation Patterns

### UI Elements

```python
# Buttons
_("OK")
_("Cancel")
_("Submit")
_("Delete")
_("Download")
_("Upload")

# Labels
_("Username")
_("Password")
_("File Name")
_("Size")
_("Date Created")

# Placeholders
_("Enter username...")
_("Type to search...")
```

### Status Messages

```python
# Success
_("File uploaded successfully")
_("Settings saved")
_("Connection established")

# Errors
_("File not found")
_("Permission denied")
_("Connection failed")

# Progress
_("Uploading...")
_("Downloading...")
_("Processing {filename}...").format(filename=fname)
```

### Dialogs

```python
# Dialog titles
_("Confirm Deletion")
_("Upload File")
_("Settings")

# Dialog content
_("Are you sure you want to delete this file?")
_("This action cannot be undone.")
```

## Handling Flet Controls

### Control Labels

```python
# TextField
username_field = ft.TextField(
    label=_("Username"),
    hint_text=_("Enter your username"),
    helper_text=_("Must be at least 3 characters"),
)

# Dropdown
language_dropdown = ft.Dropdown(
    label=_("Language"),
    options=[
        ft.DropdownOption("zh_CN", _("Simplified Chinese")),
        ft.DropdownOption("en", _("English")),
    ]
)

# Checkbox
remember_checkbox = ft.Checkbox(
    label=_("Remember me"),
)
```

### Error Messages

```python
# Field validation
if not username_field.value:
    username_field.error = _("Username is required")
    username_field.update()

# Invalid format
if not is_valid_email(email):
    email_field.error = _("Invalid email format")
```

## Testing Translations

### Manual Testing

1. **Change Language**:
   ```python
   app_shared = AppShared()
   app_shared.preferences["settings"]["language"] = "en"
   ```

2. **Restart Application**

3. **Verify**:
   - All UI elements in correct language
   - No untranslated strings
   - Formatting preserved
   - Plurals correct

### Automated Testing

**Check for missing translations**:
```python
def check_missing_translations(language: str):
    """Check for missing translations in a language."""
    import polib
    
    po_file = f"src/include/ui/locale/{language}/LC_MESSAGES/client.po"
    po = polib.pofile(po_file)
    
    missing = [entry.msgid for entry in po if not entry.msgstr]
    
    if missing:
        print(f"Missing translations in {language}:")
        for msg in missing:
            print(f"  - {msg}")
        return False
    
    return True
```

### Translation Coverage

**Check coverage**:
```bash
# Count total strings
msggrep --statistics src/include/ui/locale/messages.pot

# Count translated strings
msggrep --statistics src/include/ui/locale/zh_CN/LC_MESSAGES/client.po
```

## Adding a New Language

### Step-by-Step

1. **Create Language Directory**:
   ```bash
   mkdir -p src/include/ui/locale/fr/LC_MESSAGES
   ```

2. **Initialize Translation File**:
   ```bash
   msginit --input=src/include/ui/locale/messages.pot \
           --output=src/include/ui/locale/fr/LC_MESSAGES/client.po \
           --locale=fr_FR
   ```

3. **Edit `.po` File Header**:
   ```po
   "Language: fr_FR\n"
   "Plural-Forms: nplurals=2; plural=(n > 1);\n"
   ```

4. **Translate Strings**:
   - Use translation tool or text editor
   - Translate all `msgid` to `msgstr`

5. **Compile**:
   ```bash
   msgfmt src/include/ui/locale/fr/LC_MESSAGES/client.po \
          -o src/include/ui/locale/fr/LC_MESSAGES/client.mo
   ```

6. **Add to Language Dropdown**:
   ```python
   ft.DropdownOption("fr", _("Français (French)")),
   ```

7. **Test**:
   - Change language to French
   - Use `set_translation("fr")` or restart and verify

## Troubleshooting

### Strings Not Translated

**Possible causes**:
1. `.mo` file not compiled
2. Translation missing in `.po` file
3. Language code mismatch
4. `set_translation()` not called before imports

**Solutions**:
```bash
# Recompile .mo files
msgfmt client.po -o client.mo

# Check for missing translations
msgfmt --check client.po

# Verify language code
echo $LANGUAGE
```

### Wrong Language Displayed

**Check**:
1. `AppShared.preferences["settings"]["language"]` value
2. `os.environ["LANGUAGE"]` value
3. `.mo` file exists for language
4. Fallback working (should default to zh_CN)

### Format String Errors

**Problem**:
```python
# Error: KeyError if placeholder missing
_("Welcome {username}").format(user=user)  # Wrong key
```

**Solution**:
```python
# Match placeholder names
_("Welcome {username}").format(username=user)
```

### Plural Form Issues

**Problem**: Wrong plural form displayed

**Check** `.po` header:
```po
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
```

**Common plural forms**:
- English: `nplurals=2; plural=(n != 1);`
- Chinese: `nplurals=1; plural=0;`
- French: `nplurals=2; plural=(n > 1);`

## Future Enhancements

Potential improvements:
- Right-to-left (RTL) language support
- Date/time localization
- Number formatting localization
- Currency formatting
- Locale-specific sorting
- Translation management UI
- Crowdsourced translations
- Automatic translation updates
