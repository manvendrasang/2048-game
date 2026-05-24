# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate, unused-argument, broad-exception-caught
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring, unused-import, superfluous-parens, unspecified-encoding

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



def load_best() -> int:
    try:
        with open(BEST_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return 0


def save_best(score: int):
    try:
        with open(BEST_FILE, "w") as f:
            f.write(str(score))
    except Exception:
        pass



def load_leaderboard() -> list:
    try:
        with open(LEADER_FILE) as f:
            entries = json.load(f)
        # back-fill missing fields so old saves never crash
        for e in entries:
            e.setdefault("board_size", 4)
            e.setdefault("extra", "")
            e.setdefault("date", "")
        return entries
    except Exception:
        return []


def save_leaderboard(entries: list):
    try:
        with open(LEADER_FILE, "w") as f:
            json.dump(entries, f, indent=2)
    except Exception:
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



def load_stats() -> dict:
    defaults = {"games_played": 0, "total_score": 0,
                "highest_tile": 0, "total_moves": 0}
    try:
        with open(STATS_FILE) as f:
            data = json.load(f)
            for k, v in defaults.items():
                data.setdefault(k, v)
            return data
    except Exception:
        return defaults


def save_stats(stats: dict):
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception:
        pass





def _load_saves() -> list:
    """Return list of MAX_SLOTS dicts (None-like empty slots have 'empty': True)."""
    try:
        with open(SAVES_FILE) as f:
            data = json.load(f)
        # ensure exactly MAX_SLOTS entries
        while len(data) < MAX_SLOTS:
            data.append(None)
        return data[:MAX_SLOTS]
    except Exception:
        return [None] * MAX_SLOTS


def _write_saves(slots: list):
    try:
        with open(SAVES_FILE, "w") as f:
            json.dump(slots, f, indent=2)
    except Exception as e:
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


# If old savedata.json exists, offer it as slot-0 on first run.
_LEGACY_SAVE = os.path.join(DATA_DIR, "savedata.json")

def migrate_legacy_save():
    if not os.path.exists(_LEGACY_SAVE):
        return
    slots = _load_saves()
    if slots[0] is not None:
        return   # slot 0 already occupied
    try:
        with open(_LEGACY_SAVE) as f:
            data = json.load(f)
        data.setdefault("date", "legacy")
        slots[0] = data
        _write_saves(slots)
        os.rename(_LEGACY_SAVE, _LEGACY_SAVE + ".migrated")
    except Exception:
        pass



CHALLENGE_FILE = os.path.join(DATA_DIR, "challenges.json")


def load_challenge_progress() -> dict:
    """Returns dict keyed by challenge id (str) → {stars, best_moves, completed}."""
    try:
        with open(CHALLENGE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_challenge_result(cid: int, stars: int, moves: int):
    """Save result only if it's better than what's stored."""
    prog = load_challenge_progress()
    key  = str(cid)
    prev = prog.get(key, {"stars": 0, "best_moves": 9999, "completed": False})
    prog[key] = {
        "stars":      max(prev["stars"], stars),
        "best_moves": min(prev["best_moves"], moves) if stars > 0 else prev["best_moves"],
        "completed":  stars > 0 or prev["completed"],
    }
    try:
        with open(CHALLENGE_FILE, "w") as f:
            json.dump(prog, f, indent=2)
    except Exception:
        pass


# Daily puzzle
import os as _os
DAILY_FILE = _os.path.join(DATA_DIR, "daily.json")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def load_daily_record() -> dict:
    """Returns dict keyed by date string → {score, moves, completed}."""
    try:
        with open(DAILY_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_daily_result(score: int, moves: int, highest_tile: int) -> dict:
    """Save today's result. Returns the saved entry."""
    records = load_daily_record()
    date    = today_str()
    entry   = {
        "score":        score,
        "moves":        moves,
        "highest_tile": highest_tile,
        "completed":    True,
        "date":         date,
    }
    records[date] = entry
    try:
        with open(DAILY_FILE, "w") as f:
            json.dump(records, f, indent=2)
    except Exception:
        pass
    return entry


def get_today_result() -> dict | None:
    """Returns today's result dict if already played, else None."""
    records = load_daily_record()
    return records.get(today_str())


def get_daily_streak() -> int:
    """Count consecutive days played ending today or yesterday."""
    from datetime import date, timedelta
    records = load_daily_record()
    streak  = 0
    day     = date.today()
    while True:
        if day.strftime("%Y-%m-%d") in records:
            streak += 1
            day -= timedelta(days=1)
        else:
            break
    return streak


# Achievements
ACHIEVE_FILE = os.path.join(DATA_DIR, "achievements.json")


def load_unlocked_achievements() -> set:
    try:
        with open(ACHIEVE_FILE) as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_unlocked_achievements(unlocked: set):
    try:
        with open(ACHIEVE_FILE, "w") as f:
            json.dump(sorted(unlocked), f, indent=2)
    except Exception:
        pass


def check_and_unlock_achievements() -> list[str]:
    """Run all achievement checks. Returns list of newly unlocked IDs."""
    from data.achievements import ALL_ACHIEVEMENTS
    stats    = load_stats()
    ch_prog  = load_challenge_progress()
    daily    = load_daily_record()
    unlocked = load_unlocked_achievements()
    newly    = []
    for ach in ALL_ACHIEVEMENTS:
        if ach["id"] in unlocked:
            continue
        try:
            if ach["check"](stats, ch_prog, daily):
                unlocked.add(ach["id"])
                newly.append(ach["id"])
        except Exception:
            pass
    if newly:
        save_unlocked_achievements(unlocked)
    return newly


def record_game(score: int, highest_tile: int, moves: int):
    stats = load_stats()
    stats["games_played"] += 1
    stats["total_score"]  += score
    stats["total_moves"]  += moves
    if highest_tile > stats.get("highest_tile", 0):
        stats["highest_tile"] = highest_tile
    if score > stats.get("best_single", 0):
        stats["best_single"] = score
    save_stats(stats)