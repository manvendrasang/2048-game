# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring, redefined-outer-name

import random
from datetime import date

def _seed_for_date(d: date) -> int:
    return int(d.strftime("%Y%m%d"))
def generate_daily_board(size: int = 4, target_date: date = None) -> list[list[int]]:
    """Return a size×size starting matrix seeded by date."""
    if target_date is None:
        target_date = date.today()
    rng = random.Random(_seed_for_date(target_date))
    matrix = [[0] * size for _ in range(size)]
    empties = [(r, c) for r in range(size) for c in range(size)]
    # Place 2 starting tiles (same logic as normal game but deterministic)
    for _ in range(2):
        if not empties:
            break
        idx      = rng.randrange(len(empties))
        r, c     = empties.pop(idx)
        matrix[r][c] = 4 if rng.random() < 0.1 else 2
    return matrix
def daily_date_str(target_date: date = None) -> str:
    if target_date is None:
        target_date = date.today()
    return target_date.strftime("%B %d, %Y")
def daily_puzzle_number() -> int:
    """Sequential puzzle number starting from 2025-01-01."""
    from datetime import date
    epoch = date(2025, 1, 1)
    return (date.today() - epoch).days + 1