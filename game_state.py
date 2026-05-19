# ── game_state.py
# Pure game logic: board, movement, undo, scoring, win/lose detection.
# No pygame drawing here – only state.

import random
from constants import (
    DEFAULT_BOARD, WIN_W, BOARD_TOP, BOARD_PX,
    MODE_CLASSIC, MODE_TARGET, MODE_TIME_ATTACK,
    TARGET_TILE_DEFAULT, TIME_ATTACK_SECONDS,
)
from data.persistence import (
    load_best, save_best, save_game, load_game,
    add_leaderboard_entry, record_game,
)


class GameState:
    def __init__(self, size=DEFAULT_BOARD, mode=MODE_CLASSIC,
                 target_tile=TARGET_TILE_DEFAULT,
                 time_budget=TIME_ATTACK_SECONDS):
        self.size         = size
        self.mode         = mode
        self.target_tile  = target_tile
        self.time_budget  = time_budget      # seconds (time-attack only)
        self.elapsed      = 0.0              # seconds (target-mode timer)

        self.matrix       = [[0]*size for _ in range(size)]
        self.score        = 0
        self.best         = load_best()
        self.moves        = 0
        self.game_over    = False
        self.won          = False
        self.win_shown    = False            # so win screen shows once
        self.undo_stack   = []               # list of (matrix_snap, score, moves, elapsed)

        # animation bookkeeping
        self.tile_scales  = [[1.0]*size for _ in range(size)]
        self.score_popups = []               # [x, y, value, alpha, dy]

        # merge events for this frame (consumed by renderer / particles)
        self.merge_events = []               # list of (row, col, value)

    # ─────────────────────────── persistence ───────────────────────────── #

    def save(self) -> bool:
        return save_game(
            matrix=self.matrix, size=self.size,
            score=self.score, moves=self.moves,
            mode=self.mode, elapsed=self.elapsed,
            target_tile=self.target_tile,
        )

    def load(self) -> bool:
        data = load_game()
        if data is None:
            return False
        self.size        = data["size"]
        self.matrix      = data["matrix"]
        self.score       = data["score"]
        self.moves       = data["moves"]
        self.mode        = data.get("mode",        MODE_CLASSIC)
        self.elapsed     = data.get("elapsed",     0.0)
        self.target_tile = data.get("target_tile", TARGET_TILE_DEFAULT)
        self.tile_scales = [[1.0]*self.size for _ in range(self.size)]
        self.game_over   = False
        self.won         = False
        self.win_shown   = False
        self.undo_stack  = []
        return True

    # ─────────────────────────── undo ──────────────────────────────────── #

    def push_undo(self):
        snap = [row[:] for row in self.matrix]
        self.undo_stack.append((snap, self.score, self.moves, self.elapsed))
        if len(self.undo_stack) > 10:
            self.undo_stack.pop(0)

    def pop_undo(self):
        if not self.undo_stack:
            return
        snap, sc, mv, el = self.undo_stack.pop()
        self.matrix      = [row[:] for row in snap]
        self.score       = sc
        self.moves       = mv
        self.elapsed     = el
        self.tile_scales = [[1.0]*self.size for _ in range(self.size)]
        self.game_over   = False
        self.won         = False

    # ─────────────────────────── tile helpers ──────────────────────────── #

    def empty_cells(self):
        return [(r, c) for r in range(self.size)
                for c in range(self.size) if self.matrix[r][c] == 0]

    def place_random(self):
        empties = self.empty_cells()
        if not empties:
            return
        r, c = random.choice(empties)
        self.matrix[r][c] = 4 if random.random() < 0.1 else 2
        self.tile_scales[r][c] = 0.1

    def highest_tile(self) -> int:
        return max(max(row) for row in self.matrix)

    # ─────────────────────────── movement ──────────────────────────────── #

    def _rotate_cw(self):
        n = self.size
        new = [[0]*n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                new[c][n-1-r] = self.matrix[r][c]
        self.matrix = new

    def _slide_left(self) -> tuple[bool, int, list]:
        """Returns (moved, points, merge_positions_in_rotated_coords)."""
        moved   = False
        points  = 0
        merges  = []   # (row, col, value) in current (possibly rotated) frame
        n       = self.size
        combo   = 0

        for r in range(n):
            row = [v for v in self.matrix[r] if v != 0]
            merged = []
            skip   = False
            for i in range(len(row)):
                if skip:
                    skip = False
                    continue
                if i+1 < len(row) and row[i] == row[i+1]:
                    val    = row[i] * 2
                    merged.append(val)
                    combo  += 1
                    bonus   = val * (1 + 0.1 * combo)
                    points += int(bonus)
                    merges.append((r, len(merged)-1, val))
                    skip = True
                else:
                    merged.append(row[i])
            merged += [0] * (n - len(merged))
            if merged != self.matrix[r]:
                moved = True
                for c, val in enumerate(merged):
                    if val and val != self.matrix[r][c]:
                        self.tile_scales[r][c] = 1.2
            self.matrix[r] = merged

        return moved, points, merges

    def move(self, direction: str) -> bool:
        rotations = {"left": 0, "up": 1, "right": 2, "down": 3}
        rot = rotations[direction]

        for _ in range(rot):
            self._rotate_cw()

        moved, pts, raw_merges = self._slide_left()

        # rotate merge positions back to screen coords
        self.merge_events = []
        for (rr, rc, val) in raw_merges:
            r2, c2 = rr, rc
            for _ in range((4 - rot) % 4):
                r2, c2 = c2, self.size-1-r2
            self.merge_events.append((r2, c2, val))

        for _ in range((4 - rot) % 4):
            self._rotate_cw()

        if moved:
            self.score += pts
            self.moves += 1
            if self.score > self.best:
                self.best = self.score
                save_best(self.best)
            self.place_random()

            # win detection
            if not self.won:
                ht = self.highest_tile()
                if (self.mode == MODE_TARGET and ht >= self.target_tile) or \
                   (self.mode == MODE_CLASSIC and ht >= 2048):
                    self.won      = True
                    self.game_over = True
                    self._finish_game()

            if not self.can_move():
                self.game_over = True
                self._finish_game()

            if pts > 0:
                self.score_popups.append(
                    [WIN_W//2, BOARD_TOP + BOARD_PX//2, pts, 255, -2.0]
                )

        return moved

    def _finish_game(self):
        record_game(self.score, self.highest_tile(), self.moves)
        extra = ""
        if self.mode == MODE_TARGET and self.won:
            m = int(self.elapsed) // 60
            s = int(self.elapsed) % 60
            extra = f"{m:02d}:{s:02d}"
        add_leaderboard_entry(self.score, self.mode, extra)

    def can_move(self) -> bool:
        n = self.size
        for r in range(n):
            for c in range(n):
                if self.matrix[r][c] == 0:
                    return True
                if c+1 < n and self.matrix[r][c] == self.matrix[r][c+1]:
                    return True
                if r+1 < n and self.matrix[r][c] == self.matrix[r+1][c]:
                    return True
        return False

    # ─────────────────────────── reset ─────────────────────────────────── #

    def reset(self, size=None, mode=None, target_tile=None, time_budget=None):
        if size         is not None: self.size        = size
        if mode         is not None: self.mode        = mode
        if target_tile  is not None: self.target_tile = target_tile
        if time_budget  is not None: self.time_budget = time_budget
        self.matrix       = [[0]*self.size for _ in range(self.size)]
        self.score        = 0
        self.moves        = 0
        self.elapsed      = 0.0
        self.game_over    = False
        self.won          = False
        self.win_shown    = False
        self.undo_stack   = []
        self.tile_scales  = [[1.0]*self.size for _ in range(self.size)]
        self.score_popups = []
        self.merge_events = []
        self.place_random()
        self.place_random()

    # ─────────────────────────── animation tick ────────────────────────── #

    def tick_animations(self, dt: float = 1/60):
        """dt in seconds."""
        n = self.size
        for r in range(n):
            for c in range(n):
                s = self.tile_scales[r][c]
                if s < 1.0:
                    self.tile_scales[r][c] = min(1.0, s + 0.08)
                elif s > 1.0:
                    self.tile_scales[r][c] = max(1.0, s - 0.06)

        alive = []
        for p in self.score_popups:
            p[1] += p[4]
            p[3] -= 6
            if p[3] > 0:
                alive.append(p)
        self.score_popups = alive

        # advance timers
        if not self.game_over:
            if self.mode == MODE_TARGET:
                self.elapsed += dt
            elif self.mode == MODE_TIME_ATTACK:
                self.elapsed += dt
                if self.elapsed >= self.time_budget:
                    self.elapsed   = self.time_budget
                    self.game_over = True
                    self._finish_game()