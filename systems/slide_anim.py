# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate, global-variable-not-assigned, cell-var-from-loop
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring, redefined-outer-name, unused-import, unused-variable,unused-argument

import math
import pygame
from constants import BOARD_PX, BOARD_TOP, BOARD_LEFT, PADDING

SLIDE_DURATION = 0.11
EASE_K         = 5.0


def _cell_size(n: int) -> float:
    return (BOARD_PX - PADDING * (n + 1)) / n


def tile_px(row: int, col: int, n: int) -> tuple[int, int]:
    """Screen-space pixel centre of grid cell (row, col)."""
    cell = _cell_size(n)
    x = BOARD_LEFT + PADDING + col * (cell + PADDING) + cell / 2
    y = BOARD_TOP  + PADDING + row * (cell + PADDING) + cell / 2
    return int(x), int(y)


class TileSlide:
    __slots__ = ("src_x", "src_y", "dst_x", "dst_y", "value", "t")

    def __init__(self, src_x, src_y, dst_x, dst_y, value):
        self.src_x = src_x
        self.src_y = src_y
        self.dst_x = dst_x
        self.dst_y = dst_y
        self.value = value
        self.t     = 0.0

    @property
    def done(self) -> bool:
        return self.t >= 1.0

    def update(self, dt: float):
        self.t = min(1.0, self.t + dt / SLIDE_DURATION)

    def current_pos(self) -> tuple[int, int]:
        e = 1.0 - math.exp(-EASE_K * self.t)
        return (
            int(self.src_x + (self.dst_x - self.src_x) * e),
            int(self.src_y + (self.dst_y - self.src_y) * e),
        )


class SlideAnimSystem:

    def __init__(self):
        self._slides:  list[TileSlide] = []
        self.animating = False

    def clear(self):
        self._slides.clear()
        self.animating = False

    def build(self,
            before_screen: list[list[int]],
            after_screen:  list[list[int]],
            n: int):
        """
        Both matrices are in SCREEN coords (no rotation applied).
        We match each non-zero destination tile to its closest available
        source tile in the same row or column (depending on which axis changed).
        """
        self._slides.clear()

        # Build a pool of available source positions: {(r,c): value}
        src_pool: dict[tuple[int,int], int] = {}
        for r in range(n):
            for c in range(n):
                if before_screen[r][c] != 0:
                    src_pool[(r, c)] = before_screen[r][c]

        used_src: set[tuple[int,int]] = set()

        for r in range(n):
            for c in range(n):
                dst_val = after_screen[r][c]
                if dst_val == 0:
                    continue

                # Find how many source tiles merged into this dst (1 or 2)
                # A merged tile has dst_val = 2 * src_val
                # We prefer sources in the same row/column, closest first.
                half = dst_val // 2
                candidates_single = [
                    (rc, v) for rc, v in src_pool.items()
                    if rc not in used_src and v == dst_val
                    and (rc[0] == r or rc[1] == c)
                ]
                candidates_half = [
                    (rc, v) for rc, v in src_pool.items()
                    if rc not in used_src and v == half
                    and (rc[0] == r or rc[1] == c)
                ]

                def dist(rc):
                    return abs(rc[0] - r) + abs(rc[1] - c)

                # Try to find a single non-merging source first
                # (tile that just slid without merging)
                # Use the one closest in the movement axis
                match_single = sorted(candidates_single, key=lambda x: dist(x[0]))
                match_half   = sorted(candidates_half,   key=lambda x: dist(x[0]))

                if match_half and len(match_half) >= 2:
                    # Two tiles merged into this one
                    for src_rc, _ in match_half[:2]:
                        sx, sy = tile_px(src_rc[0], src_rc[1], n)
                        dx, dy = tile_px(r, c, n)
                        if (sx, sy) != (dx, dy):
                            self._slides.append(TileSlide(sx, sy, dx, dy, dst_val))
                        used_src.add(src_rc)
                        del src_pool[src_rc]
                elif match_single:
                    src_rc = match_single[0][0]
                    sx, sy = tile_px(src_rc[0], src_rc[1], n)
                    dx, dy = tile_px(r, c, n)
                    if (sx, sy) != (dx, dy):
                        self._slides.append(TileSlide(sx, sy, dx, dy, dst_val))
                    used_src.add(src_rc)
                    del src_pool[src_rc]
                elif match_half:
                    # Only found one half — treat as slide (board edge case)
                    src_rc = match_half[0][0]
                    sx, sy = tile_px(src_rc[0], src_rc[1], n)
                    dx, dy = tile_px(r, c, n)
                    if (sx, sy) != (dx, dy):
                        self._slides.append(TileSlide(sx, sy, dx, dy, dst_val))
                    used_src.add(src_rc)
                    del src_pool[src_rc]
                # if nothing found, tile appeared from nowhere (spawn) — no slide

        self.animating = bool(self._slides)

    def update(self, dt: float) -> bool:
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
            get_color, get_text_color, choose_font, draw_rrect, theme,
            tile_border=None):
        th = theme.get()
        for slide in self._slides:
            cx, cy = slide.current_pos()
            w = h = int(cell_size)
            tr = pygame.Rect(cx - w//2, cy - h//2, w, h)
            color = get_color(slide.value)
            draw_rrect(surface, color, tr, 10)
            if tile_border:
                pygame.draw.rect(surface, tile_border, tr, width=2, border_radius=10)
            tf  = choose_font(slide.value)
            lbl = tf.render(str(slide.value), True, get_text_color(slide.value))
            surface.blit(lbl, lbl.get_rect(center=(cx, cy)))
