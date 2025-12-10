---
name: CFMS Localization & Internationalization Expert
description: Expert in internationalization (i18n) and localization (l10n) for CFMS Client NEXT, covering translation management, locale detection, gettext integration, and multi-language support.
---

## Internationalization Overview

CFMS Client NEXT uses **GNU gettext** for internationalization, supporting multiple languages with translation files. The system allows dynamic language switching and provides fallback to default language.

### Supported Languages

Currently supported:
- **Chinese (Simplified)**: `zh_CN` (default)
- **English**: `en` or `en_US`

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
├── en/
│   └── LC_MESSAGES/
│       ├── messages.po   # English translations
│       └── messages.mo   # Compiled English
└── zh_CN/
    └── LC_MESSAGES/
        ├── messages.po   # Chinese translations
        └── messages.mo   # Compiled Chinese
```

### Locale Path Configuration

**Location**: `include/constants.py`

```python
ROOT_PATH = Path(CONSTANT_FILE_ABSPATH).resolve().parent.parent
LOCALE_PATH = f"{ROOT_PATH}/include/ui/locale"
```

## Translation Management

### Translation Singleton

**Location**: `include/util/locale.py`

```python
_translation = None  # Global translation instance

def set_translation(language: str):
    """Set the global translation instance."""
    global _translation
    _translation = gettext.translation(
        "messages",
        localedir=LOCALE_PATH,
        languages=[language],
        fallback=True  # Fallback to default if language not found
    )

def get_translation():
    """Get the global translation instance."""
    global _translation
    if _translation is None:
        # Default to Chinese
        set_translation("zh_CN")
    return _translation
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
        app_config = AppConfig()
        preferred_language = app_config.preferences.get("settings", {}).get(
            "language", "zh_CN"
        )
        
        # Set environment variable for gettext
        os.environ["LANGUAGE"] = preferred_language
        
        # Set translation singleton
        set_translation(preferred_language)
        
    except Exception as e:
        warnings.warn(f"Failed to load language preferences: {e}")
        os.environ["LANGUAGE"] = "zh_CN"
    
    # Import UI components AFTER setting locale
    from include.ui.models.connect import ConnectToServerModel
    # ... other imports
```

**Critical**: UI imports must come **after** `set_translation()` to ensure all strings use the correct language.

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
find src -name "*.py" -exec pygettext -d messages -o src/include/ui/locale/messages.pot {} +
```

### 2. Update Translation Files

Update existing `.po` files with new strings:
```bash
# For each language
msgmerge --update \
         src/include/ui/locale/zh_CN/LC_MESSAGES/messages.po \
         src/include/ui/locale/messages.pot

msgmerge --update \
         src/include/ui/locale/en/LC_MESSAGES/messages.po \
         src/include/ui/locale/messages.pot
```

### 3. Translate

Edit `.po` files manually or with translation tools:

**Example `messages.po`**:
```po
# src/include/ui/locale/zh_CN/LC_MESSAGES/messages.po
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
# For each language
msgfmt src/include/ui/locale/zh_CN/LC_MESSAGES/messages.po \
       -o src/include/ui/locale/zh_CN/LC_MESSAGES/messages.mo

msgfmt src/include/ui/locale/en/LC_MESSAGES/messages.po \
       -o src/include/ui/locale/en/LC_MESSAGES/messages.mo
```

### 5. Test

- Change language preference in settings
- Restart application
- Verify all strings appear in correct language

## Language Settings UI

### Language Selection

**Settings Model** (`include/ui/models/settings/language.py`):
```python
@route("settings/language")
class LanguageSettingsModel(Model):
    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)
        
        app_config = AppConfig()
        current_lang = app_config.preferences.get("settings", {}).get(
            "language", "zh_CN"
        )
        
        self.language_dropdown = ft.Dropdown(
            label=_("Language"),
            value=current_lang,
            options=[
                ft.dropdown.Option("zh_CN", "简体中文 (Simplified Chinese)"),
                ft.dropdown.Option("en", "English"),
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
        app_config = AppConfig()
        new_language = self.language_dropdown.value
        
        # Update preference
        if "settings" not in app_config.preferences:
            app_config.preferences["settings"] = {}
        app_config.preferences["settings"]["language"] = new_language
        
        # Save to file
        with open(PREFERENCES_PATH, "w", encoding="utf-8") as f:
            yaml.dump(app_config.preferences, f, default_flow_style=False)
        
        # Show confirmation
        self.page.show_snack_bar(
            ft.SnackBar(content=ft.Text(_("Language preference saved")))
        )
```

### Dynamic Language Switching (Advanced)

For live language switching without restart:
```python
async def switch_language(new_language: str):
    """Switch language at runtime."""
    # Update translation
    set_translation(new_language)
    
    # Update environment
    os.environ["LANGUAGE"] = new_language
    
    # Rebuild all UI components
    # This is complex and may require page reload
    await page.clean_async()
    await initialize_ui()
```

**Note**: Full UI rebuild is complex. Recommend restart for language changes.

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
        ft.dropdown.Option("zh_CN", _("Simplified Chinese")),
        ft.dropdown.Option("en", _("English")),
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
    username_field.error_text = _("Username is required")
    username_field.update()

# Invalid format
if not is_valid_email(email):
    email_field.error_text = _("Invalid email format")
```

## Testing Translations

### Manual Testing

1. **Change Language**:
   ```python
   app_config = AppConfig()
   app_config.preferences["settings"]["language"] = "en"
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
    
    po_file = f"src/include/ui/locale/{language}/LC_MESSAGES/messages.po"
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
msggrep --statistics src/include/ui/locale/zh_CN/LC_MESSAGES/messages.po
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
           --output=src/include/ui/locale/fr/LC_MESSAGES/messages.po \
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
   msgfmt src/include/ui/locale/fr/LC_MESSAGES/messages.po \
          -o src/include/ui/locale/fr/LC_MESSAGES/messages.mo
   ```

6. **Add to Language Dropdown**:
   ```python
   ft.dropdown.Option("fr", _("Français (French)")),
   ```

7. **Test**:
   - Change language to French
   - Restart and verify

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
msgfmt messages.po -o messages.mo

# Check for missing translations
msgfmt --check messages.po

# Verify language code
echo $LANGUAGE
```

### Wrong Language Displayed

**Check**:
1. `AppConfig.preferences["settings"]["language"]` value
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
