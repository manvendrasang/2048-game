# pylint: disable=missing-module-docstring, missing-function-docstring, redefined-outer-name

import random
from datetime import datetime, date, timedelta

DAILY_RESET_HOUR = 0   # midnight local time

_DESCRIPTIONS = [
    "A fresh start — use the open space wisely.",
    "Two seeds planted. Where will they grow?",
    "The board is nearly empty. Build your tower.",
    "Start small, think big — today's puzzle begins.",
    "Patience is key. Every tile has a purpose.",
    "A blank canvas. Make your first moves count.",
    "Simple beginnings often lead to great tiles.",
    "The journey to 2048 starts with two tiles.",
    "Don't rush — the board rewards careful thinking.",
    "Every great run starts exactly like this one.",
    "Today's challenge: turn two tiles into glory.",
    "A quiet board hides infinite possibilities.",
    "Think three moves ahead from the very start.",
    "Two tiles, endless paths — choose wisely.",
    "The clock is reset. A new puzzle awaits.",
    "Begin again. Today's board is uniquely yours.",
    "Corners first — or do you have another plan?",
    "Let the tiles guide you somewhere unexpected.",
    "A new day, a new grid, a new opportunity.",
    "From two tiles, can you reach the golden 2048?",
]


def get_puzzle_date() -> date:
    """The current puzzle date — changes at DAILY_RESET_HOUR each day."""
    now = datetime.now()
    if now.hour < DAILY_RESET_HOUR:
        return now.date() - timedelta(days=1)
    return now.date()


def _seed_for_date(d: date) -> int:
    return int(d.strftime("%Y%m%d"))


def generate_daily_board(size: int = 4, target_date: date = None) -> list[list[int]]:
    if target_date is None:
        target_date = get_puzzle_date()
    rng    = random.Random(_seed_for_date(target_date))
    matrix = [[0] * size for _ in range(size)]
    empties = [(r, c) for r in range(size) for c in range(size)]
    for _ in range(2):
        if not empties:
            break
        idx      = rng.randrange(len(empties))
        r, c     = empties.pop(idx)
        matrix[r][c] = 4 if rng.random() < 0.1 else 2
    return matrix


def get_daily_description(target_date: date = None) -> str:
    if target_date is None:
        target_date = get_puzzle_date()
    rng = random.Random(_seed_for_date(target_date) + 1)   # offset seed so desc != board
    return rng.choice(_DESCRIPTIONS)


def daily_date_str(target_date: date = None) -> str:
    if target_date is None:
        target_date = get_puzzle_date()
    return target_date.strftime("%B %d, %Y")


def daily_puzzle_number() -> int:
    epoch = date(2025, 1, 1)
    return (get_puzzle_date() - epoch).days + 1


def seconds_until_next_puzzle() -> int:
    """Seconds remaining until the next puzzle unlocks."""
    now     = datetime.now()
    next_dt = datetime.combine(
        now.date() + timedelta(days=1),
        datetime.min.time().replace(hour=DAILY_RESET_HOUR)
    )
    if now.hour < DAILY_RESET_HOUR:
        next_dt = datetime.combine(
            now.date(),
            datetime.min.time().replace(hour=DAILY_RESET_HOUR)
        )
    return max(0, int((next_dt - now).total_seconds()))
