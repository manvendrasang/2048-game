# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate, unused-argument
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring, unused-import, superfluous-parens

import os
import json
from datetime import datetime

DATA_DIR     = os.path.join(os.path.dirname(__file__))
LEADER_FILE  = os.path.join(DATA_DIR, "leaderboard.json")
STATS_FILE   = os.path.join(DATA_DIR, "stats.json")
SAVES_FILE   = os.path.join(DATA_DIR, "saves.json")   # 10-slot
BEST_FILE    = os.path.join(DATA_DIR, "best.txt")

MAX_LEADERS  = 5
MAX_SLOTS    = 10

# Best score
def load_best() -> int:
    try:
        with open(BEST_FILE, encoding="utf-8") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0
def save_best(score: int):
    try:
        with open(BEST_FILE, "w", encoding="utf-8") as f:
            f.write(str(score))
    except (FileNotFoundError, ValueError):
        pass

#  Leaderboard
def load_leaderboard() -> list:
    try:
        with open(LEADER_FILE, encoding="utf-8") as f:
            entries = json.load(f)
        # back-fill missing fields so old saves never crash
        for e in entries:
            e.setdefault("board_size", 4)
            e.setdefault("extra", "")
            e.setdefault("date", "")
        return entries
    except (FileNotFoundError, ValueError):
        return []
def save_leaderboard(entries: list):
    try:
        with open(LEADER_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
    except (FileNotFoundError, ValueError):
        pass
def load_leaderboard_by_mode(mode: str | None) -> list:
    """Return top-5 entries filtered by mode. None = all modes."""
    entries = load_leaderboard()
    if mode is None:
        return entries
    return [e for e in entries if e.get("mode") == mode][:MAX_LEADERS]
def add_leaderboard_entry(score: int, mode: str, extra: str = "",
                        board_size: int = 4):
    entries = load_leaderboard()
    entry = {
        "score":      score,
        "mode":       mode,
        "extra":      extra,
        "board_size": board_size,
        "date":       datetime.now().strftime("%m/%d %H:%M"),
    }
    entries.append(entry)
    entries.sort(key=lambda e: e["score"], reverse=True)
    entries = entries[:MAX_LEADERS]
    save_leaderboard(entries)
    return entries

#  Stats
def load_stats() -> dict:
    defaults = {"games_played": 0, "total_score": 0,
                "highest_tile": 0, "total_moves": 0}
    try:
        with open(STATS_FILE, encoding="utf-8") as f:
            data = json.load(f)
            for k, v in defaults.items():
                data.setdefault(k, v)
            return data
    except (FileNotFoundError, ValueError):
        return defaults
def save_stats(stats: dict):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
    except (FileNotFoundError, ValueError):
        pass
def record_game(score: int, highest_tile: int, moves: int):
    stats = load_stats()
    stats["games_played"]  += 1
    stats["total_score"]   += score
    stats["total_moves"]   += moves
    if highest_tile > stats["highest_tile"]:
        stats["highest_tile"] = highest_tile
    save_stats(stats)


#  10-slot save system
def _load_saves() -> list:
    """Return list of MAX_SLOTS dicts (None-like empty slots have 'empty': True)."""
    try:
        with open(SAVES_FILE, encoding="utf-8") as f:
            data = json.load(f)
        # ensure exactly MAX_SLOTS entries
        while len(data) < MAX_SLOTS:
            data.append(None)
        return data[:MAX_SLOTS]
    except (FileNotFoundError, ValueError):
        return [None] * MAX_SLOTS
def _write_saves(slots: list):
    try:
        with open(SAVES_FILE, "w", encoding="utf-8") as f:
            json.dump(slots, f, indent=2)
    except (FileNotFoundError, ValueError) as e:
        print("Save failed:", e)
def get_save_slots() -> list:
    """Return list of MAX_SLOTS items. Empty slots are None."""
    return _load_saves()
def save_to_slot(slot: int, matrix, size, score, moves,
                mode, elapsed, target_tile) -> bool:
    """Save game state into slot (0-indexed). Overwrites if occupied."""
    if not (0 <= slot < MAX_SLOTS):
        return False
    slots = _load_saves()
    slots[slot] = {
        "matrix":      matrix,
        "size":        size,
        "score":       score,
        "moves":       moves,
        "mode":        mode,
        "elapsed":     elapsed,
        "target_tile": target_tile,
        "date":        datetime.now().strftime("%m/%d %H:%M"),
    }
    _write_saves(slots)
    return True
def load_from_slot(slot: int) -> dict | None:
    """Load game state from slot (0-indexed). Returns None if empty."""
    if not (0 <= slot < MAX_SLOTS):
        return None
    slots = _load_saves()
    return slots[slot]
def delete_slot(slot: int):
    """Clear a save slot."""
    if not (0 <= slot < MAX_SLOTS):
        return
    slots = _load_saves()
    slots[slot] = None
    _write_saves(slots)


#  Legacy single-file load (migration)
# If old savedata.json exists, offer it as slot-0 on first run.
_LEGACY_SAVE = os.path.join(DATA_DIR, "savedata.json")
def migrate_legacy_save():
    if not os.path.exists(_LEGACY_SAVE):
        return
    slots = _load_saves()
    if slots[0] is not None:
        return   # slot 0 already occupied
    try:
        with open(_LEGACY_SAVE, encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("date", "legacy")
        slots[0] = data
        _write_saves(slots)
        os.rename(_LEGACY_SAVE, _LEGACY_SAVE + ".migrated")
    except (FileNotFoundError, ValueError):
        pass