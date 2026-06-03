# pylint: disable=missing-function-docstring, missing-module-docstring, unused-variable

RANKS = [
    {"name": "Beginner",    "min_score": 0,        "color": (140, 140, 160), "icon": "🌱"},
    {"name": "Apprentice",  "min_score": 5_000,    "color": (100, 180, 100), "icon": "🌿"},
    {"name": "Challenger",  "min_score": 25_000,   "color": (100, 160, 220), "icon": "⚡"},
    {"name": "Expert",      "min_score": 75_000,   "color": (180, 120, 220), "icon": "🔮"},
    {"name": "Master",      "min_score": 200_000,  "color": (220, 160,  60), "icon": "🏅"},
    {"name": "Grandmaster", "min_score": 500_000,  "color": (237, 194,  46), "icon": "👑"},
]


def get_rank(total_score: int) -> dict:
    """Return the current rank dict for a given total score."""
    current = RANKS[0]
    for r in RANKS:
        if total_score >= r["min_score"]:
            current = r
        else:
            break
    return current


def get_next_rank(total_score: int) -> dict | None:
    """Return the next rank, or None if already Grandmaster."""
    for i, r in enumerate(RANKS):
        if total_score < r["min_score"]:
            return r
    return None


def rank_progress(total_score: int) -> float:
    """Return 0.0–1.0 progress toward the next rank."""
    current = get_rank(total_score)
    nxt     = get_next_rank(total_score)
    if nxt is None:
        return 1.0
    span = nxt["min_score"] - current["min_score"]
    done = total_score - current["min_score"]
    return max(0.0, min(1.0, done / span)) if span > 0 else 1.0
