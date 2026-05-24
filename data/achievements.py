# pylint: disable=missing-module-docstring

ALL_ACHIEVEMENTS = [
    # Tile milestones
    {
        "id": "tile_128",
        "name": "Getting Started",
        "desc": "Reach the 128 tile",
        "icon": "🟡",
        "category": "tiles",
        "check": lambda s, cp, dr: s.get("highest_tile", 0) >= 128,
    },
    {
        "id": "tile_256",
        "name": "Quarter Way",
        "desc": "Reach the 256 tile",
        "icon": "🟠",
        "category": "tiles",
        "check": lambda s, cp, dr: s.get("highest_tile", 0) >= 256,
    },
    {
        "id": "tile_512",
        "name": "Halfway There",
        "desc": "Reach the 512 tile",
        "icon": "🔶",
        "category": "tiles",
        "check": lambda s, cp, dr: s.get("highest_tile", 0) >= 512,
    },
    {
        "id": "tile_1024",
        "name": "So Close",
        "desc": "Reach the 1024 tile",
        "icon": "🏅",
        "category": "tiles",
        "check": lambda s, cp, dr: s.get("highest_tile", 0) >= 1024,
    },
    {
        "id": "tile_2048",
        "name": "The Goal",
        "desc": "Reach the 2048 tile",
        "icon": "🏆",
        "category": "tiles",
        "check": lambda s, cp, dr: s.get("highest_tile", 0) >= 2048,
    },
    {
        "id": "tile_4096",
        "name": "Beyond the Limit",
        "desc": "Reach the 4096 tile",
        "icon": "💎",
        "category": "tiles",
        "check": lambda s, cp, dr: s.get("highest_tile", 0) >= 4096,
    },
    # Games played
    {
        "id": "games_1",
        "name": "First Game",
        "desc": "Complete your first game",
        "icon": "🎮",
        "category": "games",
        "check": lambda s, cp, dr: s.get("games_played", 0) >= 1,
    },
    {
        "id": "games_10",
        "name": "Regular Player",
        "desc": "Play 10 games",
        "icon": "🎯",
        "category": "games",
        "check": lambda s, cp, dr: s.get("games_played", 0) >= 10,
    },
    {
        "id": "games_50",
        "name": "Dedicated",
        "desc": "Play 50 games",
        "icon": "⭐",
        "category": "games",
        "check": lambda s, cp, dr: s.get("games_played", 0) >= 50,
    },
    {
        "id": "games_100",
        "name": "Centurion",
        "desc": "Play 100 games",
        "icon": "💯",
        "category": "games",
        "check": lambda s, cp, dr: s.get("games_played", 0) >= 100,
    },
    # Score milestones
    {
        "id": "score_1k",
        "name": "First Thousand",
        "desc": "Score 1,000 points in a single game",
        "icon": "📈",
        "category": "scores",
        "check": lambda s, cp, dr: s.get("best_single", 0) >= 1000,
    },
    {
        "id": "score_10k",
        "name": "Ten Thousand",
        "desc": "Score 10,000 points in a single game",
        "icon": "📊",
        "category": "scores",
        "check": lambda s, cp, dr: s.get("best_single", 0) >= 10000,
    },
    {
        "id": "score_50k",
        "name": "High Roller",
        "desc": "Score 50,000 points in a single game",
        "icon": "💰",
        "category": "scores",
        "check": lambda s, cp, dr: s.get("best_single", 0) >= 50000,
    },
    # Challenges
    {
        "id": "challenge_first",
        "name": "Challenge Accepted",
        "desc": "Complete your first challenge",
        "icon": "🎖️",
        "category": "challenges",
        "check": lambda s, cp, dr: any(
            v.get("completed") for v in cp.values()
        ),
    },
    {
        "id": "challenge_3star",
        "name": "Perfectionist",
        "desc": "Earn 3 stars on any challenge",
        "icon": "🌟",
        "category": "challenges",
        "check": lambda s, cp, dr: any(
            v.get("stars", 0) >= 3 for v in cp.values()
        ),
    },
    {
        "id": "challenge_all",
        "name": "Grand Champion",
        "desc": "Complete all 10 challenges",
        "icon": "👑",
        "category": "challenges",
        "check": lambda s, cp, dr: sum(
            1 for v in cp.values() if v.get("completed")
        ) >= 10,
    },
    # Daily
    {
        "id": "daily_first",
        "name": "Daily Devotee",
        "desc": "Complete your first daily puzzle",
        "icon": "📅",
        "category": "daily",
        "check": lambda s, cp, dr: len(dr) >= 1,
    },
    {
        "id": "daily_streak_7",
        "name": "Week Warrior",
        "desc": "Maintain a 7-day daily streak",
        "icon": "🔥",
        "category": "daily",
        "check": lambda s, cp, dr: _streak(dr) >= 7,
    },
    {
        "id": "daily_streak_30",
        "name": "Monthly Master",
        "desc": "Maintain a 30-day daily streak",
        "icon": "🌙",
        "category": "daily",
        "check": lambda s, cp, dr: _streak(dr) >= 30,
    },
    # Moves
    {
        "id": "moves_500",
        "name": "Busy Fingers",
        "desc": "Make 500 total moves",
        "icon": "👆",
        "category": "games",
        "check": lambda s, cp, dr: s.get("total_moves", 0) >= 500,
    },
]

CATEGORIES = ["tiles", "scores", "games", "challenges", "daily"]

CATEGORY_LABELS = {
    "tiles":      "Tile Milestones",
    "scores":     "Score Records",
    "games":      "Games Played",
    "challenges": "Challenges",
    "daily":      "Daily Puzzle",
}


def _streak(daily_records: dict) -> int:
    from datetime import date, timedelta
    streak = 0
    day    = date.today()
    while True:
        if day.strftime("%Y-%m-%d") in daily_records:
            streak += 1
            day -= timedelta(days=1)
        else:
            break
    return streak
