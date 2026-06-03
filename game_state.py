# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring, consider-using-enumerate, unused-variable
# pylint: disable=multiple-statements, attribute-defined-outside-init

import random
import copy
from constants import (
    DEFAULT_BOARD, WIN_W, BOARD_TOP, BOARD_PX,
    MODE_CLASSIC, MODE_TARGET, MODE_TIME_ATTACK, MODE_CHALLENGE, MODE_DAILY,
    TARGET_TILE_DEFAULT, TIME_ATTACK_SECONDS,
)
from data.persistence import (
    load_best, save_best,
    save_to_slot, load_from_slot,
    add_leaderboard_entry, record_game,
)
from systems.slide_anim import SlideAnimSystem


class GameState:
    def __init__(self, size=DEFAULT_BOARD, mode=MODE_CLASSIC,
                target_tile=TARGET_TILE_DEFAULT,
                time_budget=TIME_ATTACK_SECONDS,
                challenge: dict | None = None):
        self.size         = size
        self.mode         = mode
        self.target_tile  = target_tile
        self.time_budget  = time_budget
        self.elapsed      = 0.0

        # challenge metadata (None when not in challenge mode)
        self.challenge        = challenge
        self.challenge_failed = False
        self.daily_finished   = False

        self.matrix       = [[0]*size for _ in range(size)]
        self.score        = 0
        self.best         = load_best()
        self.moves        = 0
        self.game_over    = False
        self.won          = False
        self.win_shown    = False
        self.undo_stack   = []
        self.undo_tokens  = 3     # refills on reset; 0 = no more undos

        self.tile_scales  = [[1.0]*size for _ in range(size)]
        self.score_popups = []
        self.merge_events = []
        self.slide_anim   = SlideAnimSystem()


    def save(self, slot: int) -> bool:
        return save_to_slot(
            slot=slot, matrix=self.matrix, size=self.size,
            score=self.score, moves=self.moves, mode=self.mode,
            elapsed=self.elapsed, target_tile=self.target_tile,
        )

    def load(self, slot: int) -> bool:
        data = load_from_slot(slot)
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


    def push_undo(self):
        snap = [row[:] for row in self.matrix]
        self.undo_stack.append((snap, self.score, self.moves, self.elapsed))
        if len(self.undo_stack) > 10:
            self.undo_stack.pop(0)

    def pop_undo(self) -> bool:
        """Returns True if undo was performed."""
        if not self.undo_stack or self.undo_tokens <= 0:
            return False
        snap, sc, mv, el = self.undo_stack.pop()
        self.matrix      = [row[:] for row in snap]
        self.score       = sc
        self.moves       = mv
        self.elapsed     = el
        self.tile_scales = [[1.0]*self.size for _ in range(self.size)]
        self.game_over   = False
        self.won         = False
        self.slide_anim.clear()
        self.undo_tokens -= 1
        return True

    @property
    def can_undo(self) -> bool:
        return bool(self.undo_stack) and self.undo_tokens > 0


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


    def _rotate_cw(self):
        n = self.size
        new = [[0]*n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                new[c][n-1-r] = self.matrix[r][c]
        self.matrix = new

    def _slide_left(self) -> tuple[bool, int, list]:
        moved, points, merges = False, 0, []
        combo = 0
        n = self.size
        for r in range(n):
            row = [v for v in self.matrix[r] if v != 0]
            merged, skip = [], False
            for i in range(len(row)):
                if skip:
                    skip = False
                    continue
                if i+1 < len(row) and row[i] == row[i+1]:
                    val = row[i] * 2
                    merged.append(val)
                    combo += 1
                    points += int(val * (1 + 0.1 * combo))
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
        # Standard 2048 rotation: rotate CW N times so direction becomes leftward,
        # slide left, rotate CCW N times back.
        # left=0 (no rotation), right=2 (180°), down=1 (1xCW), up=3 (3xCW)
        rotations = {"left": 0, "right": 2, "down": 1, "up": 3}
        rot = rotations[direction]

        # Snapshot in screen space BEFORE any rotation
        before_screen = [row[:] for row in self.matrix]

        for _ in range(rot):
            self._rotate_cw()

        moved, pts, raw_merges = self._slide_left()

        self.merge_events = []
        for (rr, rc, val) in raw_merges:
            r2, c2 = rr, rc
            for _ in range((4 - rot) % 4):
                r2, c2 = c2, self.size - 1 - r2
            self.merge_events.append((r2, c2, val))

        for _ in range((4 - rot) % 4):
            self._rotate_cw()

        # Snapshot in screen space AFTER rotation is undone
        after_screen = [row[:] for row in self.matrix]

        # Build slide animation entirely in screen space
        if moved:
            self.slide_anim.build(before_screen, after_screen, self.size)

        if moved:
            self.score += pts
            self.moves += 1
            if self.score > self.best:
                self.best = self.score
                save_best(self.best)
            self.place_random()

            if not self.won:
                ht = self.highest_tile()
                # challenge win/fail detection
                if self.mode == MODE_CHALLENGE and self.challenge:
                    ch = self.challenge
                    gt = ch["goal_type"]
                    gv = ch["goal_value"]
                    ml = ch["move_limit"]
                    if (gt == "tile"  and ht >= gv) or \
                    (gt == "score" and self.score >= gv):
                        self.won       = True
                        self.game_over = True
                        self._finish_challenge()
                    elif ml > 0 and self.moves >= ml and not self.won:
                        self.challenge_failed = True
                        self.game_over        = True
                elif self.mode == MODE_DAILY:
                    # daily puzzle ends only when no moves remain
                    pass
                elif (self.mode == MODE_TARGET and ht >= self.target_tile) or \
                    (self.mode == MODE_CLASSIC and ht >= 2048):
                    self.won       = True
                    self.game_over = True
                    self._finish_game()

            if not self.can_move() and not self.game_over:
                self.game_over = True
                if self.mode == MODE_CHALLENGE:
                    self.challenge_failed = True
                    self._finish_challenge()
                elif self.mode == MODE_DAILY:
                    self._finish_daily()
                else:
                    self._finish_game()

            if pts > 0:
                self.score_popups.append(
                    [WIN_W//2, BOARD_TOP + BOARD_PX//2, pts, 255, -2.0]
                )
        return moved

    def _finish_challenge(self):
        """Record challenge result and compute stars."""
        if not self.challenge:
            return
        ch  = self.challenge
        par = ch["par_moves"]
        if self.won:
            if self.moves <= par:
                stars = 3
            elif self.moves <= int(par * 1.4):
                stars = 2
            else:
                stars = 1
        else:
            stars = 0
        from data.persistence import save_challenge_result
        save_challenge_result(ch["id"], stars, self.moves)
        self.challenge_stars = stars

    def _finish_daily(self):
        """Record daily puzzle result. Called when board is full (no moves left)."""
        ht = self.highest_tile()
        record_game(self.score, ht, self.moves)
        from data.persistence import save_daily_result
        save_daily_result(self.score, self.moves, ht)
        # Daily always counts as a completion regardless of score
        self.won            = True
        self.game_over      = True
        self.daily_finished = True

    def _finish_game(self):
        record_game(self.score, self.highest_tile(), self.moves)
        extra = ""
        if self.mode == MODE_TARGET and self.won:
            m = int(self.elapsed) // 60
            s = int(self.elapsed) % 60
            extra = f"{m:02d}:{s:02d}"
        add_leaderboard_entry(self.score, self.mode, extra,
                            board_size=self.size)

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

    def reset(self, size=None, mode=None, target_tile=None,
            time_budget=None, challenge=None):
        if size        is not None: self.size        = size
        if mode        is not None: self.mode        = mode
        if target_tile is not None: self.target_tile = target_tile
        if time_budget is not None: self.time_budget = time_budget
        if challenge   is not None: self.challenge   = challenge
        self.score            = 0
        self.moves            = 0
        self.elapsed          = 0.0
        self.game_over        = False
        self.won              = False
        self.win_shown        = False
        self.challenge_failed = False
        self.challenge_stars  = 0
        self.daily_finished   = False
        self.undo_stack       = []
        self.undo_tokens      = 3
        self.tile_scales      = [[1.0]*self.size for _ in range(self.size)]
        self.score_popups     = []
        self.merge_events     = []
        self.slide_anim.clear()

        # challenge: use prescribed starting matrix or random
        if self.mode == MODE_CHALLENGE and self.challenge and \
                self.challenge.get("start_matrix"):
            sm = self.challenge["start_matrix"]
            self.size   = self.challenge["board_size"]
            self.matrix = copy.deepcopy(sm)
            self.tile_scales = [[1.0]*self.size for _ in range(self.size)]
            # place one random tile on an empty cell to make it interesting
            self.place_random()
        else:
            self.matrix = [[0]*self.size for _ in range(self.size)]
            self.place_random()
            self.place_random()

    def tick_animations(self, dt: float = 1/60):
        n = self.size

        # tick tile scale animations
        for r in range(n):
            for c in range(n):
                s = self.tile_scales[r][c]
                if s < 1.0:
                    self.tile_scales[r][c] = min(1.0, s + 0.08)
                elif s > 1.0:
                    self.tile_scales[r][c] = max(1.0, s - 0.06)

        # tick slide animation
        self.slide_anim.update(dt)

        alive = []
        for p in self.score_popups:
            p[1] += p[4]
            p[3] -= 6
            if p[3] > 0:
                alive.append(p)
        self.score_popups = alive

        if not self.game_over:
            if self.mode in (MODE_TARGET, MODE_TIME_ATTACK):
                self.elapsed += dt
                if self.mode == MODE_TIME_ATTACK and self.elapsed >= self.time_budget:
                    self.elapsed   = self.time_budget
                    self.game_over = True
                    self._finish_game()
