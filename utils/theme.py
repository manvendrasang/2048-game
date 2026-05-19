# ── utils/theme.py
# Holds the active theme and lets any module query it.

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