# pylint: disable=missing-function-docstring, missing-module-docstring, unspecified-encoding, broad-exception-caught, global-statement, protected-access, redefined-builtin

import os
import json

_DIR  = os.path.dirname(__file__)
_FILE = os.path.join(_DIR, "settings.json")

_DEFAULTS = {
    "theme":        "dark",
    "sfx_enabled":  True,
    "music_enabled": True,
    "sfx_volume":   0.8,
    "music_volume": 0.4,
}

_current: dict = dict(_DEFAULTS)


def load():
    """Load settings from disk. Missing keys fall back to defaults."""
    global _current
    try:
        with open(_FILE) as f:
            data = json.load(f)
        for k, v in _DEFAULTS.items():
            data.setdefault(k, v)
        _current = data
    except Exception:
        _current = dict(_DEFAULTS)


def save():
    """Write current settings to disk immediately."""
    try:
        with open(_FILE, "w") as f:
            json.dump(_current, f, indent=2)
    except Exception:
        pass


def get(key: str):
    return _current.get(key, _DEFAULTS.get(key))


def set(key: str, value):
    _current[key] = value
    save()


def apply_to_systems():
    """Apply loaded settings to sound/music/theme systems."""
    import systems.sound as sound
    import systems.music as music
    import utils.theme   as theme

    theme.set_theme(get("theme"))

    sound.set_volume(get("sfx_volume"))
    if not get("sfx_enabled"):
        sound._enabled = False

    music.set_volume(get("music_volume"))
    if not get("music_enabled"):
        music._enabled = False
