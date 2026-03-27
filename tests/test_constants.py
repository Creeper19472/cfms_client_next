import os
import sys
import importlib

# Ensure 'src' is on sys.path so 'include' package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

constants = importlib.import_module("include.constants")


def test_app_version_exists_and_is_string():
    assert hasattr(constants, "APP_VERSION")
    assert isinstance(constants.APP_VERSION, str)
    assert constants.APP_VERSION != ""
