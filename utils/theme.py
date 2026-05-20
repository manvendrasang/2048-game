# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring

from constants import THEME_DARK, THEME_LIGHT

_current = "dark"

def set_theme(name: str):
    global _current
    if name in ("dark", "light"):
        _current = name

def toggle() -> str:
    global _current
    _current = "light" if _current == "dark" else "dark"
    return _current

def get() -> dict:
    return THEME_DARK if _current == "dark" else THEME_LIGHT

def name() -> str:
    return _current