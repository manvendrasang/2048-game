# ── data/persistence.py
# Handles all file I/O: leaderboard, stats, save/load, best score.

import os
import json
from datetime import datetime

DATA_DIR   = os.path.join(os.path.dirname(__file__))
LEADER_FILE = os.path.join(DATA_DIR, "leaderboard.json")
STATS_FILE  = os.path.join(DATA_DIR, "stats.json")
SAVE_FILE   = os.path.join(DATA_DIR, "savedata.json")
BEST_FILE   = os.path.join(DATA_DIR, "best.txt")

MAX_LEADERS = 5


# ── Best score
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


# ── Leaderboard  (top-5, stored as list of dicts)
def load_leaderboard() -> list:
    try:
        with open(LEADER_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def save_leaderboard(entries: list):
    try:
        with open(LEADER_FILE, "w") as f:
            json.dump(entries, f, indent=2)
    except Exception:
        pass


def add_leaderboard_entry(score: int, mode: str, extra: str = ""):
    """Add a new entry, keep top MAX_LEADERS sorted by score desc."""
    entries = load_leaderboard()
    entry = {
        "score": score,
        "mode":  mode,
        "extra": extra,                             # e.g. "02:14" for target time
        "date":  datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    entries.append(entry)
    entries.sort(key=lambda e: e["score"], reverse=True)
    entries = entries[:MAX_LEADERS]
    save_leaderboard(entries)
    return entries


# ── Stats
def load_stats() -> dict:
    defaults = {
        "games_played":  0,
        "total_score":   0,
        "highest_tile":  0,
        "total_moves":   0,
    }
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


def record_game(score: int, highest_tile: int, moves: int):
    stats = load_stats()
    stats["games_played"]  += 1
    stats["total_score"]   += score
    stats["total_moves"]   += moves
    if highest_tile > stats["highest_tile"]:
        stats["highest_tile"] = highest_tile
    save_stats(stats)


# ── Save / Load game state
def save_game(matrix, size, score, moves, mode, elapsed, target_tile) -> bool:
    try:
        data = {
            "matrix":       matrix,
            "size":         size,
            "score":        score,
            "moves":        moves,
            "mode":         mode,
            "elapsed":      elapsed,
            "target_tile":  target_tile,
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)
        return True
    except Exception as e:
        print("Save failed:", e)
        return False


def load_game() -> dict | None:
    try:
        with open(SAVE_FILE) as f:
            return json.load(f)
    except Exception:
        return None