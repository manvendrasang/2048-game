import sys
import math
import random
import pygame
from pygame.locals import QUIT, KEYDOWN

from constants import getColor, getTextColor, GRAY_DARK

# ── Window / board constants
WIN_W, WIN_H   = 520, 620
BOARD_PX       = 460          # pixel size of the board area
BOARD_TOP      = 140          # y-offset where the board starts
BOARD_LEFT     = 30
PADDING        = 8            # gap between tiles
ANIM_SPEED     = 0.18         # 0–1 lerp factor per frame (higher = faster)
DEFAULT_BOARD  = 4

# ── Colours
BG_COLOR       = (18,  18,  28)
BOARD_BG       = (42,  42,  58)
CELL_EMPTY     = (50,  50,  65)
HUD_TEXT       = (220, 220, 230)
SCORE_BOX_BG   = (50,  50,  70)
ACCENT         = (237, 194,  46)
OVERLAY_COLOR  = (18,  18,  28, 200)   # rgba

pygame.init()
SURFACE = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("2048")
CLOCK = pygame.time.Clock()

# ── Fonts
font_title   = pygame.font.SysFont("consolas",  42, bold=True)
font_tile_lg = pygame.font.SysFont("consolas",  36, bold=True)
font_tile_md = pygame.font.SysFont("consolas",  26, bold=True)
font_tile_sm = pygame.font.SysFont("consolas",  18, bold=True)
font_hud     = pygame.font.SysFont("consolas",  20, bold=True)
font_small   = pygame.font.SysFont("consolas",  15)
font_over    = pygame.font.SysFont("consolas",  48, bold=True)
font_hint    = pygame.font.SysFont("consolas",  14)


#  Game state
class GameState:
    def __init__(self, size=DEFAULT_BOARD):
        self.size        = size
        self.matrix      = [[0]*size for _ in range(size)]
        self.score       = 0
        self.best        = self._load_best()
        self.moves       = 0
        self.game_over   = False
        self.undo_stack  = []         # list of (matrix_snapshot, score, moves)

        # animation bookkeeping
        self.tile_scales  = [[1.0]*size for _ in range(size)]  # per-tile scale
        self.score_popups = []    # list of [x, y, value, alpha, dy]

    # ── persistence
    def _load_best(self) -> int:
        try:
            with open("bestscores", "r") as f:
                return int(f.read().strip())
        except Exception:
            return 0

    def _save_best(self):
        try:
            with open("bestscores", "w") as f:
                f.write(str(self.best))
        except Exception:
            pass

    def save(self):
        try:
            with open("savedata", "w") as f:
                for row in self.matrix:
                    f.write(" ".join(map(str, row)) + "\n")
                f.write(f"{self.size}\n{self.score}\n{self.moves}\n")
        except Exception as e:
            print("Save failed:", e)

    def load(self) -> bool:
        try:
            with open("savedata", "r") as f:
                lines = f.read().splitlines()
            # figure out size from saved file
            size_line_idx = len(lines) - 3
            size = int(lines[size_line_idx])
            matrix = []
            for i in range(size):
                matrix.append(list(map(int, lines[i].split())))
            self.size    = size
            self.matrix  = matrix
            self.score   = int(lines[size_line_idx + 1])
            self.moves   = int(lines[size_line_idx + 2])
            self.tile_scales = [[1.0]*size for _ in range(size)]
            self.game_over   = False
            return True
        except Exception as e:
            print("Load failed:", e)
            return False

    # ── undo 
    def push_undo(self):
        snapshot = [row[:] for row in self.matrix]
        self.undo_stack.append((snapshot, self.score, self.moves))
        if len(self.undo_stack) > 10:
            self.undo_stack.pop(0)

    def pop_undo(self):
        if self.undo_stack:
            snap, sc, mv = self.undo_stack.pop()
            self.matrix  = [row[:] for row in snap]
            self.score   = sc
            self.moves   = mv
            self.tile_scales = [[1.0]*self.size for _ in range(self.size)]
            self.game_over   = False

    # ── tile helpers 
    def empty_cells(self):
        return [(r, c) for r in range(self.size)
                       for c in range(self.size)
                       if self.matrix[r][c] == 0]

    def place_random(self):
        empties = self.empty_cells()
        if not empties:
            return
        r, c = random.choice(empties)
        self.matrix[r][c] = 4 if random.random() < 0.1 else 2
        # trigger birth animation
        self.tile_scales[r][c] = 0.1

    # ── movement 
    def _rotate_cw(self):
        n = self.size
        new = [[0]*n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                new[c][n - 1 - r] = self.matrix[r][c]
        self.matrix = new

    def _slide_left(self) -> tuple[bool, int]:
        """Slide & merge one row-set leftward.
        Returns (moved: bool, points_earned: int)."""
        moved  = False
        points = 0
        n = self.size
        combo  = 0

        for r in range(n):
            # compact
            row = [v for v in self.matrix[r] if v != 0]
            # merge
            merged = []
            skip = False
            for i in range(len(row)):
                if skip:
                    skip = False
                    continue
                if i + 1 < len(row) and row[i] == row[i+1]:
                    val = row[i] * 2
                    merged.append(val)
                    combo  += 1
                    bonus   = val * (1 + 0.1 * combo)   # combo multiplier
                    points += int(bonus)
                    skip    = True
                else:
                    merged.append(row[i])
            # pad
            merged += [0] * (n - len(merged))
            if merged != self.matrix[r]:
                moved = True
                # record positions of non-zero merged tiles for pop anim
                for c, val in enumerate(merged):
                    if val != 0 and val != self.matrix[r][c]:
                        self.tile_scales[r][c] = 1.2   # pop scale
            self.matrix[r] = merged

        return moved, points

    def move(self, direction: str) -> bool:
        """direction: 'left' | 'right' | 'up' | 'down'
        Returns True if anything changed."""
        rotations = {"left": 0, "up": 1, "right": 2, "down": 3}
        rot = rotations[direction]

        for _ in range(rot):
            self._rotate_cw()

        moved, pts = self._slide_left()

        for _ in range((4 - rot) % 4):
            self._rotate_cw()

        if moved:
            self.score += pts
            self.moves += 1
            if self.score > self.best:
                self.best = self.score
                self._save_best()
            self.place_random()
            if not self.can_move():
                self.game_over = True
            # spawn score popup near the board centre
            if pts > 0:
                self.score_popups.append(
                    [WIN_W // 2, BOARD_TOP + BOARD_PX // 2, pts, 255, -2.0]
                )

        return moved

    def can_move(self) -> bool:
        n = self.size
        for r in range(n):
            for c in range(n):
                if self.matrix[r][c] == 0:
                    return True
                if c + 1 < n and self.matrix[r][c] == self.matrix[r][c+1]:
                    return True
                if r + 1 < n and self.matrix[r][c] == self.matrix[r+1][c]:
                    return True
        return False

    def reset(self, size=None):
        if size is not None:
            self.size = size
        self.matrix     = [[0]*self.size for _ in range(self.size)]
        self.score      = 0
        self.moves      = 0
        self.game_over  = False
        self.undo_stack = []
        self.tile_scales = [[1.0]*self.size for _ in range(self.size)]
        self.score_popups = []
        self.place_random()
        self.place_random()

    # ── animation tick 
    def tick_animations(self):
        n = self.size
        for r in range(n):
            for c in range(n):
                s = self.tile_scales[r][c]
                if s < 1.0:
                    self.tile_scales[r][c] = min(1.0, s + 0.08)
                elif s > 1.0:
                    self.tile_scales[r][c] = max(1.0, s - 0.06)

        # update popups
        alive = []
        for p in self.score_popups:
            p[1] += p[4]   # move up
            p[3] -= 6      # fade
            if p[3] > 0:
                alive.append(p)
        self.score_popups = alive


#  Drawing
def tile_rect(row, col, size):
    """Return the pygame.Rect for a given tile position."""
    cell = (BOARD_PX - PADDING * (size + 1)) / size
    x = BOARD_LEFT + PADDING + col * (cell + PADDING)
    y = BOARD_TOP  + PADDING + row * (cell + PADDING)
    return pygame.Rect(int(x), int(y), int(cell), int(cell))


def draw_rounded_rect(surface, color, rect, radius=10):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def choose_tile_font(value, cell_size):
    digits = len(str(value))
    if digits <= 2:
        return font_tile_lg
    elif digits == 3:
        return font_tile_md
    else:
        return font_tile_sm


def draw_board(gs: GameState):
    # board background
    board_rect = pygame.Rect(BOARD_LEFT, BOARD_TOP, BOARD_PX, BOARD_PX)
    draw_rounded_rect(SURFACE, BOARD_BG, board_rect, 14)

    n = gs.size
    cell = (BOARD_PX - PADDING * (n + 1)) / n

    for r in range(n):
        for c in range(n):
            base_rect = tile_rect(r, c, n)
            val   = gs.matrix[r][c]
            scale = gs.tile_scales[r][c]

            # scale around centre
            cx, cy = base_rect.centerx, base_rect.centery
            w  = int(base_rect.width  * scale)
            h  = int(base_rect.height * scale)
            tr = pygame.Rect(cx - w//2, cy - h//2, w, h)

            color = getColor(val)
            draw_rounded_rect(SURFACE, color, tr, max(4, int(10 * scale)))

            if val != 0:
                tf    = choose_tile_font(val, cell)
                label = tf.render(str(val), True, getTextColor(val))
                lrect = label.get_rect(center=(cx, cy))
                SURFACE.blit(label, lrect)


def draw_hud(gs: GameState):
    # title
    title = font_title.render("2048", True, ACCENT)
    SURFACE.blit(title, (BOARD_LEFT, 14))

    # score boxes
    def score_box(label_txt, val_txt, x, y, w=110, h=55):
        box = pygame.Rect(x, y, w, h)
        draw_rounded_rect(SURFACE, SCORE_BOX_BG, box, 10)
        lbl = font_small.render(label_txt, True, (160, 160, 180))
        val = font_hud.render(val_txt,   True, HUD_TEXT)
        SURFACE.blit(lbl, lbl.get_rect(centerx=x+w//2, top=y+6))
        SURFACE.blit(val, val.get_rect(centerx=x+w//2, top=y+24))

    score_box("SCORE",  str(gs.score), WIN_W - 250, 14)
    score_box("BEST",   str(gs.best),  WIN_W - 130, 14)

    # move counter
    mv_lbl = font_small.render(f"Moves: {gs.moves}", True, (140, 140, 160))
    SURFACE.blit(mv_lbl, (BOARD_LEFT, 90))

    # key hints
    hints = "[←↑↓→] Move   [U] Undo   [S] Save   [L] Load   [R] Restart"
    hint_surf = font_hint.render(hints, True, (90, 90, 110))
    SURFACE.blit(hint_surf, (BOARD_LEFT, WIN_H - 22))


def draw_score_popups(gs: GameState):
    for p in gs.score_popups:
        x, y, val, alpha, _ = p
        txt = font_hud.render(f"+{val}", True, ACCENT)
        txt.set_alpha(max(0, alpha))
        SURFACE.blit(txt, txt.get_rect(centerx=x, centery=int(y)))


def draw_game_over(gs: GameState):
    # semi-transparent overlay
    overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    overlay.fill((18, 18, 28, 200))
    SURFACE.blit(overlay, (0, 0))

    go_txt  = font_over.render("Game Over!", True, (255, 255, 255))
    sc_txt  = font_hud.render(f"Score: {gs.score}", True, HUD_TEXT)
    bs_txt  = font_hud.render(f"Best:  {gs.best}",  True, ACCENT)
    re_txt  = font_hud.render("Press  R  to restart", True, (180, 180, 200))

    SURFACE.blit(go_txt, go_txt.get_rect(centerx=WIN_W//2, centery=220))
    SURFACE.blit(sc_txt, sc_txt.get_rect(centerx=WIN_W//2, centery=300))
    SURFACE.blit(bs_txt, bs_txt.get_rect(centerx=WIN_W//2, centery=340))
    SURFACE.blit(re_txt, re_txt.get_rect(centerx=WIN_W//2, centery=400))


#  Main loop
def main():
    gs = GameState()
    gs.reset()

    direction_map = {
        pygame.K_UP:    "up",
        pygame.K_DOWN:  "down",
        pygame.K_LEFT:  "left",
        pygame.K_RIGHT: "right",
    }

    running = True
    while running:
        CLOCK.tick(60)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            if event.type == KEYDOWN:
                k = event.key

                # ── movement
                if k in direction_map and not gs.game_over:
                    gs.push_undo()
                    gs.move(direction_map[k])

                # ── control keys
                elif k == pygame.K_r:
                    gs.reset()

                elif k == pygame.K_u:
                    gs.pop_undo()

                elif k == pygame.K_s:
                    gs.save()

                elif k == pygame.K_l:
                    gs.load()

                # ── board size: keys 3–6
                elif pygame.K_3 <= k <= pygame.K_6:
                    gs.reset(size=k - pygame.K_0)

        # ── animations 
        gs.tick_animations()

        # ── draw 
        SURFACE.fill(BG_COLOR)
        draw_hud(gs)
        draw_board(gs)
        draw_score_popups(gs)

        if gs.game_over:
            draw_game_over(gs)

        pygame.display.flip()


if __name__ == "__main__":
    main()