"""
Translation and localization utilities.

This module provides a delegating translation proxy that allows runtime
switching of language translations without restarting the application.
"""

import gettext
import threading

from include.constants import LOCALE_PATH

__all__ = ["create_translation", "set_translation", "get_translation"]


class DelegatingTranslation(gettext.NullTranslations):
    """
    Singleton translation proxy that delegates calls to an internal real translation.
    
    This class allows for runtime switching of translations by replacing the
    internal translation object. Subsequent constructions return the same instance.
    
    Thread-safe singleton implementation ensures consistent translation behavior
    across the application.
    """

    _instance = None
    _singleton_lock = threading.Lock()

    def __new__(cls, real=None):
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, real=None):
        """
        Initialize or update the translation proxy.
        
        Args:
            real: Optional translation object to use. If provided on re-initialization,
                  replaces the current translation.
        """
        # Initialize only once; if re-initialized with a new real, update it
        if getattr(self, "_initialized", False):
            if real is not None:
                self.set_real(real)
            return

        super().__init__()
        self._lock = threading.RLock()
        self._real = real or gettext.NullTranslations()
        self._initialized = True

    def set_real(self, real):
        """
        Replace the internal real translation object.
        
        Args:
            real: New translation object to use
        """
        with self._lock:
            self._real = real or gettext.NullTranslations()

    def get_real(self):
        """
        Return the current internal real translation object.
        
        Returns:
            The current translation object
        """
        with self._lock:
            return self._real

    # Delegate common gettext API methods explicitly
    def gettext(self, message):
        """Translate message."""
        with self._lock:
            return self._real.gettext(message)

    def ngettext(self, msgid1, msgid2, n):
        """Translate message with plural forms."""
        with self._lock:
            return self._real.ngettext(msgid1, msgid2, n)

    # Legacy aliases for compatibility
    def ugettext(self, message):
        """Legacy alias for gettext."""
        with self._lock:
            return getattr(self._real, "ugettext", self._real.gettext)(message)

    def ungettext(self, singular, plural, n):
        """Legacy alias for ngettext."""
        with self._lock:
            return getattr(self._real, "ungettext", self._real.ngettext)(
                singular, plural, n
            )

    def install(self, names=("gettext", "_")):
        """Install translation functions into builtins."""
        with self._lock:
            return getattr(self._real, "install", lambda *_: None)(names)


def create_translation(language: str = "en", fallback: bool = True):
    """
    Create gettext translation instance for the specified language.

    Args:
        language: Language code (e.g., 'en', 'zh_CN'). Defaults to 'en'.
        fallback: Whether to fallback to NullTranslations if language not found.
                  Defaults to True.

    Returns:
        A gettext translation instance for the specified language.
    """
    translation = gettext.translation(
        "client",
        localedir=LOCALE_PATH,
        languages=[language],
        fallback=fallback,
    )
    return translation


def set_translation(language: str = "en", fallback: bool = True):
    """
    Set the global translation to a specific language.
    
    This updates the singleton DelegatingTranslation instance with a new
    language translation.
    
    Args:
        language: Language code (e.g., 'en', 'zh_CN'). Defaults to 'en'.
        fallback: Whether to fallback to NullTranslations if language not found.
                  Defaults to True.
    """
    translation = create_translation(language, fallback)
    delegating_translation = DelegatingTranslation()
    delegating_translation.set_real(translation)


def get_translation():
    """
    Get the singleton translation instance.
    
    Returns:
        The global DelegatingTranslation singleton instance.
    """
    return DelegatingTranslation()
