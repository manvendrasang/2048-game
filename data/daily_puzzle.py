# pylint: disable=missing-module-docstring, missing-function-docstring, redefined-outer-name

import random
from datetime import datetime, date, timedelta

DAILY_RESET_HOUR = 0   # midnight local time

_DESCRIPTIONS = [
    "Goal: score as high as possible before the board fills up. No undo, no save.",
    "Goal: reach the highest tile you can before running out of moves.",
    "Goal: chain as many merges as possible for a high score. Board ends when full.",
    "Goal: maximize your score. The puzzle ends when no moves remain.",
    "Goal: get the highest tile possible. Merging earns bonus combo points.",
    "Goal: score beats progress — aim for big merges over big tiles.",
    "Goal: play until the board is full. Your final score is recorded.",
    "Goal: every tile must find a partner. Score as high as you can.",
    "Goal: no time limit, no undo — just you, the tiles, and the score.",
    "Goal: think carefully. The board ends when no merges are possible.",
    "Goal: build toward 2048 and beyond. Score matters most today.",
    "Goal: use combo merges to multiply your score. No second chances.",
    "Goal: the puzzle ends when the board fills. Leave no tile behind.",
    "Goal: achieve the highest score possible before moves run out.",
    "Goal: plan your merges — chain reactions earn the most points.",
    "Goal: reach the furthest tile you can before the board locks up.",
    "Goal: every move counts. Score is final when the board is full.",
    "Goal: maximize points through smart merges. No undo allowed.",
    "Goal: how far can you go? Push for the highest tile and score.",
    "Goal: one shot, one board, one score. Make every move count.",
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
