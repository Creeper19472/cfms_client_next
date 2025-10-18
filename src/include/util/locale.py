"""
Copyright 2025 Creeper19472

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import gettext
import os

__all__ = ["get_translation", "SUPPORTED_LANGUAGES"]

# Supported languages
SUPPORTED_LANGUAGES = {
    "zh_CN": "中文",
    "en": "English",
}

_current_translation = None


def get_translation(language: str = "zh_CN"):
    """
    Get gettext translation instance for the specified language.
    
    Args:
        language: Language code (e.g., 'en', 'zh_CN'). Defaults to 'zh_CN'.
        
    Returns:
        A gettext translation instance
    """
    global _current_translation
    
    try:
        # Try to load the specified language
        translation = gettext.translation(
            "client",
            localedir="ui/locale",
            languages=[language],
        )
        _current_translation = translation
        return translation
    except FileNotFoundError:
        # Fallback to default (Chinese) if translation file not found
        translation = gettext.translation(
            "client",
            localedir="ui/locale",
            fallback=True,
        )
        _current_translation = translation
        return translation


def get_current_translation():
    """Get the currently active translation instance."""
    global _current_translation
    if _current_translation is None:
        return get_translation()
    return _current_translation
