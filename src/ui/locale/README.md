# CFMS Client NEXT - Multilingual Support

This document describes the multilingual support system in CFMS Client NEXT.

## Supported Languages

- **Chinese (Simplified)** - `zh_CN` (Default)
- **English** - `en`

## Translation Files

Translation files are stored in `src/ui/locale/`:

```
src/ui/locale/
├── en/
│   └── LC_MESSAGES/
│       ├── client.po  (English translations)
│       └── client.mo  (Compiled binary)
└── zh_CN/
    └── LC_MESSAGES/
        ├── client.po  (Chinese translations)
        └── client.mo  (Compiled binary)
```

## How It Works

The application uses Python's `gettext` module for internationalization (i18n):

1. All user-facing strings are wrapped with the `_()` function
2. The `_()` function looks up translations in the compiled `.mo` files
3. If no translation is found, the original Chinese string is displayed

### Example

```python
import gettext

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext

# Usage
button_text = _("取消")  # Returns "Cancel" in English, "取消" in Chinese
```

## Changing the Language

### Method 1: Environment Variable (Recommended for Testing)

Set the `LANGUAGE` environment variable before running the application:

```bash
# For English
export LANGUAGE=en
uv run flet run

# For Chinese (default)
export LANGUAGE=zh_CN
uv run flet run
```

### Method 2: System Locale

The application will use your system's locale settings by default. If your system is set to English, the app will display in English.

### Method 3: Configuration File (Future)

A language setting will be added to the preferences file (`preferences.yaml`) to allow users to choose their preferred language from within the app.

## For Developers

### Adding New Translatable Strings

1. Wrap your string with `_()`:
   ```python
   message = _("新的消息")
   ```

2. Update the translation files:
   ```bash
   # Extract strings and regenerate .po files
   cd src
   python3 -c "
   # See the script in docs for extracting strings
   "
   ```

3. Compile the .po files to .mo:
   ```bash
   cd src
   python3 -c "
   import polib
   po = polib.pofile('ui/locale/en/LC_MESSAGES/client.po')
   po.save_as_mofile('ui/locale/en/LC_MESSAGES/client.mo')
   "
   ```

### Translation Coverage

Current translation coverage:
- Total strings: 149
- Translated to English: 139 (93%)
- Using Chinese as fallback: 10 (7%)

### Files Structure

- `.po` files: Human-readable translation source files
- `.mo` files: Compiled binary files used by the application (generated from .po)

The `.mo` files are excluded from git (via `.gitignore`) but should be compiled during the build process.

## Contributing Translations

To contribute translations:

1. Edit the appropriate `.po` file in `src/ui/locale/[language]/LC_MESSAGES/client.po`
2. Find entries with empty `msgstr` or fuzzy markers
3. Add your translation
4. Compile to `.mo` using the script above
5. Submit a pull request

## Notes

- The default language is Chinese (Simplified) as this is the original development language
- All code comments have been changed to English
- The translation system uses gettext, which is a widely-used standard for i18n
- F-strings with placeholders are supported: `_(f"上传完成，共计 {total_errors} 个错误。")`
