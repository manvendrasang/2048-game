# pylint: disable=missing-module-docstring, missing-function-docstring, global-statement, invalid-name, redefined-outer-name

from constants import THEME_DARK, THEME_LIGHT, THEME_HIGH_CONTRAST

_current = "dark"

_THEMES = {
    "dark":          THEME_DARK,
    "light":         THEME_LIGHT,
    "high_contrast": THEME_HIGH_CONTRAST,
}

_CYCLE_ORDER = ["dark", "light", "high_contrast"]


def set_theme(name: str):
    global _current
    if name in _THEMES:
        _current = name


def toggle() -> str:
    """Cycle dark -> light -> high_contrast -> dark."""
    global _current
    idx = _CYCLE_ORDER.index(_current) if _current in _CYCLE_ORDER else 0
    _current = _CYCLE_ORDER[(idx + 1) % len(_CYCLE_ORDER)]
    return _current


def get() -> dict:
    return _THEMES.get(_current, THEME_DARK)


def name() -> str:
    return _current


def is_high_contrast() -> bool:
    return _current == "high_contrast"
