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
import threading

from include.constants import LOCALE_PATH

__all__ = ["create_translation"]


class DelegatingTranslation(gettext.NullTranslations):
    """
    Singleton translation proxy that delegates calls to an internal real translation.
    Subsequent constructions return the same instance. Passing `real` to the
    constructor will replace the current internal real translation.
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
        # initialize only once; if re-initialized with a new real, update it
        if getattr(self, "_initialized", False):
            if real is not None:
                self.set_real(real)
            return

        super().__init__()
        self._lock = threading.RLock()
        self._real = real or gettext.NullTranslations()
        self._initialized = True

    def set_real(self, real):
        """Replace the internal real translation object."""
        with self._lock:
            self._real = real or gettext.NullTranslations()

    def get_real(self):
        """Return the current internal real translation object."""
        with self._lock:
            return self._real

    # Delegate common gettext API methods explicitly
    def gettext(self, message):
        with self._lock:
            return self._real.gettext(message)

    def ngettext(self, msgid1, msgid2, n):
        with self._lock:
            return self._real.ngettext(msgid1, msgid2, n)

    # ugettext / ungettext are legacy aliases in some environments; delegate if present
    def ugettext(self, message):
        with self._lock:
            return getattr(self._real, "ugettext", self._real.gettext)(message)

    def ungettext(self, singular, plural, n):
        with self._lock:
            return getattr(self._real, "ungettext", self._real.ngettext)(
                singular, plural, n
            )

    # Delegate install so using this proxy is transparent
    def install(self, names=("gettext", "_")):
        with self._lock:
            return getattr(self._real, "install", lambda *_: None)(names)

    # # Fallback: forward any other attribute access to the real translation object
    # def __getattr__(self, name):
    #     # Called only if attribute not found on this proxy instance
    #     real = self.get_real()
    #     return getattr(real, name)


def create_translation(language: str = "en", fallback: bool = True):
    """
    Create gettext translation instance for the specified language.

    Args:
        language: Language code (e.g., 'en', 'zh_CN'). Defaults to 'en'.

    Returns:
        A gettext translation instance
    """

    translation = gettext.translation(
        "client",
        localedir=LOCALE_PATH,
        languages=[language],
        fallback=fallback,
    )
    return translation


def set_translation(language: str = "en", fallback: bool = True):
    translation = create_translation(language, fallback)
    delegating_translation = DelegatingTranslation()
    delegating_translation.set_real(translation)


def get_translation():
    return DelegatingTranslation()
