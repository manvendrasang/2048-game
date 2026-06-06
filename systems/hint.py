# pylint: disable=missing-function-docstring, missing-module-docstring, unused-import, consider-using-enumerate

import copy
import math


DIRECTIONS = ["left", "right", "up", "down"]

_ROTATION_MAP = {"left": 0, "right": 2, "down": 1, "up": 3}


def _rotate_cw(matrix: list[list[int]], n: int) -> list[list[int]]:
    new = [[0]*n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            new[c][n-1-r] = matrix[r][c]
    return new


def _slide_left_score(matrix: list[list[int]], n: int) -> tuple[bool, int, list[list[int]]]:
    """Slide left on a copy. Returns (moved, score, new_matrix)."""
    moved  = False
    points = 0
    new_m  = []
    for r in range(n):
        row = [v for v in matrix[r] if v != 0]
        merged, skip = [], False
        for i in range(len(row)):
            if skip:
                skip = False
                continue
            if i+1 < len(row) and row[i] == row[i+1]:
                val = row[i] * 2
                merged.append(val)
                points += val
                skip = True
            else:
                merged.append(row[i])
        merged += [0] * (n - len(merged))
        if merged != matrix[r]:
            moved = True
        new_m.append(merged)
    return moved, points, new_m


def _simulate(matrix: list[list[int]], direction: str, n: int) -> tuple[bool, float]:
    """
    Simulate a move. Returns (moved, heuristic_score).
    Heuristic: merge_points × 2 + empty_cells × 20 + corner_bonus.
    """
    rot = _ROTATION_MAP[direction]
    m   = copy.deepcopy(matrix)

    for _ in range(rot):
        m = _rotate_cw(m, n)

    moved, pts, m = _slide_left_score(m, n)

    for _ in range((4 - rot) % 4):
        m = _rotate_cw(m, n)

    if not moved:
        return False, -1.0

    # Count empty cells after move
    empties = sum(1 for r in range(n) for c in range(n) if m[r][c] == 0)

    # Reward for largest tile being in a corner
    max_val     = max(m[r][c] for r in range(n) for c in range(n))
    corners     = [m[0][0], m[0][n-1], m[n-1][0], m[n-1][n-1]]
    corner_bonus = 50 if max_val in corners else 0

    # Reward for keeping large tiles along edges
    edge_bonus = 0
    for r in range(n):
        for c in range(n):
            val = m[r][c]
            if val >= max_val // 2 and (r == 0 or r == n-1 or c == 0 or c == n-1):
                edge_bonus += val // 8

    score = pts * 2 + empties * 20 + corner_bonus + edge_bonus
    return True, float(score)


def best_direction(matrix: list[list[int]], n: int) -> str | None:
    """Return the best direction string, or None if no moves possible."""
    best_dir   = None
    best_score = -1.0
    for d in DIRECTIONS:
        moved, score = _simulate(matrix, d, n)
        if moved and score > best_score:
            best_score = score
            best_dir   = d
    return best_dir


# Arrow geometry helpers — used by the renderer
_ARROW_OFFSETS = {
    "left":  (-1,  0),
    "right": ( 1,  0),
    "up":    ( 0, -1),
    "down":  ( 0,  1),
}

def arrow_direction_vec(direction: str) -> tuple[int, int]:
    return _ARROW_OFFSETS.get(direction, (0, 0))
