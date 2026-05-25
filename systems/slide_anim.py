# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate, global-variable-not-assigned
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring, redefined-outer-name, unused-import, unused-variable,unused-argument

import pygame
from constants import BOARD_PX, BOARD_TOP, BOARD_LEFT, PADDING

SLIDE_DURATION = 0.10   # seconds for a tile to travel full board width
EASE_K         = 4.0    # exponential ease-out strength

def _cell_size(n: int) -> float:
    return (BOARD_PX - PADDING * (n + 1)) / n

def tile_px(row: int, col: int, n: int) -> tuple[int, int]:
    """Return pixel centre of grid position (row, col) for board size n."""
    cell = _cell_size(n)
    x = BOARD_LEFT + PADDING + col * (cell + PADDING) + cell / 2
    y = BOARD_TOP  + PADDING + row * (cell + PADDING) + cell / 2
    return int(x), int(y)

class TileSlide:
    """One tile animating from src to dst."""
    __slots__ = ("src_x", "src_y", "dst_x", "dst_y", "value", "t", "is_merge")

    def __init__(self, src_x, src_y, dst_x, dst_y, value, is_merge=False):
        self.src_x    = src_x
        self.src_y    = src_y
        self.dst_x    = dst_x
        self.dst_y    = dst_y
        self.value    = value
        self.t        = 0.0
        self.is_merge = is_merge

    @property
    def done(self) -> bool:
        return self.t >= 1.0

    def update(self, dt: float):
        self.t = min(1.0, self.t + dt / SLIDE_DURATION)

    def current_pos(self) -> tuple[int, int]:
        # ease-out exponential: f(t) = 1 - e^(-k*t)
        import math
        e = 1.0 - math.exp(-EASE_K * self.t)
        x = int(self.src_x + (self.dst_x - self.src_x) * e)
        y = int(self.src_y + (self.dst_y - self.src_y) * e)
        return x, y

class SlideAnimSystem:
    """
    Owned by GameState. Call start_move() before the matrix changes,
    then commit() after. Draw via draw_slides().
    """

    def __init__(self):
        self._slides: list[TileSlide] = []
        self._static_tiles: list     = []  # tiles not moving this turn
        self.animating = False

    def clear(self):
        self._slides.clear()
        self._static_tiles.clear()
        self.animating = False

    def build(self, before: list[list[int]], after: list[list[int]],
            merge_dsts: set[tuple[int,int]], n: int):
        """
        Compute slide paths by matching non-zero tiles in each row/col.
        before/after are n×n matrices (already in left-slid frame;
        caller handles rotation mapping externally via direction).
        merge_dsts: set of (row, col) cells in `after` that are merged tiles.
        """
        self._slides.clear()
        self._static_tiles.clear()

        # For each row, match source tiles to destination positions
        for r in range(n):
            src_vals = [(c, before[r][c]) for c in range(n) if before[r][c] != 0]
            dst_vals = [(c, after[r][c])  for c in range(n) if after[r][c]  != 0]

            # Each destination tile came from one or two source tiles.
            # Simple greedy left-to-right assignment works for slide-left.
            si = 0
            for dc, dv in dst_vals:
                is_merge = (r, dc) in merge_dsts
                count = 2 if is_merge else 1
                for _ in range(count):
                    if si >= len(src_vals):
                        break
                    sc, sv = src_vals[si]
                    si += 1
                    sx, sy = tile_px(r, sc, n)
                    dx, dy = tile_px(r, dc, n)
                    if sx != dx or sy != dy:
                        self._slides.append(
                            TileSlide(sx, sy, dx, dy, dv, is_merge and count == 2)
                        )
                    else:
                        # tile didn't move — static
                        self._static_tiles.append((r, dc, dv))

        self.animating = bool(self._slides)

    def update(self, dt: float) -> bool:
        """Update all slides. Returns True when all done."""
        if not self.animating:
            return True
        for s in self._slides:
            s.update(dt)
        if all(s.done for s in self._slides):
            self.animating = False
            self._slides.clear()
            return True
        return False

    def draw(self, surface: pygame.Surface, n: int, cell_size: float,
            get_color, get_text_color, choose_font, draw_rrect, theme):
        """Draw sliding tiles. Called instead of normal tile drawing during animation."""
        th = theme.get()
        for slide in self._slides:
            cx, cy = slide.current_pos()
            w = h = int(cell_size)
            tr = pygame.Rect(cx - w//2, cy - h//2, w, h)
            color = get_color(slide.value)
            draw_rrect(surface, color, tr, 10)
            tf  = choose_font(slide.value)
            lbl = tf.render(str(slide.value), True, get_text_color(slide.value))
            surface.blit(lbl, lbl.get_rect(center=(cx, cy)))
