# pylint: disable=missing-function-docstring, missing-module-docstring, multiple-statements, no-member, invalid-name

import pygame
import math
from constants import WIN_W, WIN_H
from utils.drawing import draw_rounded_rect, font, blit_centered, Button, panel_mouse_pos
from constants import getColor, getTextColor
import utils.theme as theme
import systems.sound as sound

# Modal dimensions
MODAL_W = 480
MODAL_H = 520
MODAL_X = WIN_W // 2 - MODAL_W // 2
MODAL_Y = WIN_H // 2 - MODAL_H // 2

# Mini board dimensions inside modal
MINI_BOARD_PX = 180
MINI_PADDING  = 5


def _mini_tile_rect(row: int, col: int, n: int) -> pygame.Rect:
    cell = (MINI_BOARD_PX - MINI_PADDING * (n + 1)) / n
    x    = MINI_PADDING + col * (cell + MINI_PADDING)
    y    = MINI_PADDING + row * (cell + MINI_PADDING)
    return pygame.Rect(int(x), int(y), int(cell), int(cell))


def _draw_mini_board(srf: pygame.Surface, ox: int, oy: int,
                     matrix: list[list[int]] | None, n: int, th: dict):
    """Draw a small board preview at pixel offset (ox, oy)."""
    board_surf = pygame.Surface((MINI_BOARD_PX, MINI_BOARD_PX), pygame.SRCALPHA)
    board_bg   = th["board_bg"]
    pygame.draw.rect(board_surf, board_bg, board_surf.get_rect(), border_radius=8)

    for r in range(n):
        for c in range(n):
            val  = matrix[r][c] if matrix else 0
            rect = _mini_tile_rect(r, c, n)
            col  = getColor(val) if val else th["cell_empty"]
            pygame.draw.rect(board_surf, col, rect, border_radius=4)
            if val:
                digits = len(str(val))
                fsize  = 14 if digits <= 2 else 11 if digits == 3 else 9
                f      = pygame.font.SysFont(None, fsize + 4, bold=True)
                lbl    = f.render(str(val), True, getTextColor(val))
                board_surf.blit(lbl, lbl.get_rect(center=rect.center))

    srf.blit(board_surf, (ox, oy))


def _draw_stars(srf, n_stars: int, cx: int, y: int, r: int = 14):
    STAR_ON  = (237, 194, 46)
    STAR_OFF = (60,  60,  80)
    spacing  = r * 2 + 8
    xs = [cx + (i - 1) * spacing for i in range(3)]
    for i, x in enumerate(xs):
        col    = STAR_ON if i < n_stars else STAR_OFF
        points = []
        for k in range(5):
            a1 = math.radians(-90 + k * 72)
            points.append((x + r * math.cos(a1), y + r * math.sin(a1)))
            a2 = math.radians(-90 + k * 72 + 36)
            points.append((x + r * 0.42 * math.cos(a2), y + r * 0.42 * math.sin(a2)))
        pygame.draw.polygon(srf, col, points)


class ChallengePreview:
    """
    Drawn on top of ChallengeScreen as a modal.
    Returns:
        ("start", challenge_id)  — player confirmed
        "cancel"                 — player dismissed
        None                     — no action
    """

    def __init__(self, surface: pygame.Surface):
        self.surface    = surface
        self._challenge = None
        self._progress  = {}
        self._visible   = False

        cx = WIN_W // 2
        by = MODAL_Y + MODAL_H - 68
        self._start_btn = Button(
            pygame.Rect(cx - 200, by, 180, 50),
            "▶  Start", font_name="menu_med",
            bg=(60, 130, 60), hover_bg=(80, 170, 80),
        )
        self._cancel_btn = Button(
            pygame.Rect(cx + 20, by, 180, 50),
            "✕  Cancel", font_name="menu_med",
            bg=(90, 50, 50), hover_bg=(130, 70, 70),
        )

    def open(self, challenge: dict, progress: dict):
        self._challenge = challenge
        self._progress  = progress
        self._visible   = True

    def close(self):
        self._visible   = False
        self._challenge = None

    def is_visible(self) -> bool:
        return self._visible

    def handle_event(self, event) -> tuple | str | None:
        if not self._visible:
            return None

        # Click outside modal → cancel
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            import constants as C
            px = event.pos[0] - C.PANEL_OX
            py = event.pos[1] - C.PANEL_OY
            modal_rect = pygame.Rect(MODAL_X, MODAL_Y, MODAL_W, MODAL_H)
            if not modal_rect.collidepoint(px, py):
                sound.play("click")
                self.close()
                return "cancel"

        if self._start_btn.is_clicked(event):
            sound.play("click")
            cid = self._challenge["id"]
            self.close()
            return ("start", cid)

        if self._cancel_btn.is_clicked(event):
            sound.play("click")
            self.close()
            return "cancel"

        return None

    def update(self):
        if not self._visible:
            return
        mp = panel_mouse_pos()
        self._start_btn.update(mp)
        self._cancel_btn.update(mp)

    def draw(self):
        if not self._visible or not self._challenge:
            return

        th   = theme.get()
        srf  = self.surface
        dark = theme.name() == "dark"
        ch   = self._challenge

        # Dim background
        dim = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        srf.blit(dim, (0, 0))

        # Modal card
        modal = pygame.Rect(MODAL_X, MODAL_Y, MODAL_W, MODAL_H)
        card_bg = (32, 34, 48) if dark else (240, 235, 222)
        draw_rounded_rect(srf, card_bg, modal, 18)
        pygame.draw.rect(srf, th["accent"], modal, width=2, border_radius=18)

        cx = WIN_W // 2

        # Challenge number badge + name
        diff_col = (
            (70, 180,  80) if ch["id"] <= 3 else
            (210, 160,  40) if ch["id"] <= 6 else
            (200,  70,  60)
        )
        badge_rect = pygame.Rect(MODAL_X + 20, MODAL_Y + 20, 34, 34)
        draw_rounded_rect(srf, diff_col, badge_rect, 8)
        num_s = font("label").render(str(ch["id"]), True, (255, 255, 255))
        srf.blit(num_s, num_s.get_rect(center=badge_rect.center))

        name_s = font("menu_big").render(ch["name"], True, th["accent"])
        srf.blit(name_s, (MODAL_X + 62, MODAL_Y + 24))

        pygame.draw.line(srf, th["divider"],
                        (MODAL_X + 20, MODAL_Y + 62),
                        (MODAL_X + MODAL_W - 20, MODAL_Y + 62), 1)

        # Mini board on the left
        board_n      = ch["board_size"]
        start_matrix = ch.get("start_matrix")
        board_ox     = MODAL_X + 24
        board_oy     = MODAL_Y + 74
        _draw_mini_board(srf, board_ox, board_oy, start_matrix, board_n, th)

        # Board label
        bl = font("hint").render(
            "Random start" if not start_matrix else "Fixed start",
            True, th["hint_text"]
        )
        blit_centered(srf, bl, board_ox + MINI_BOARD_PX // 2, board_oy + MINI_BOARD_PX + 12)

        # Info panel on the right
        ix = MODAL_X + MINI_BOARD_PX + 44
        iy = MODAL_Y + 76

        def info_row(label: str, value: str, col=None):
            nonlocal iy
            ls = font("hint").render(label + ":", True, th["lbl_text"])
            vs = font("label").render(value, True, col or th["hud_text"])
            srf.blit(ls, (ix, iy))
            srf.blit(vs, (ix, iy + 16))
            iy += 46

        # Goal
        gt = ch["goal_type"]
        gv = ch["goal_value"]
        goal_str = f"Reach {gv} tile" if gt == "tile" else f"Score {gv:,} pts"
        info_row("Goal", goal_str, th["accent"])

        # Move limit
        ml = ch["move_limit"]
        info_row("Move Limit", str(ml) + " moves" if ml > 0 else "Unlimited")

        # Par
        info_row("Par (3 stars)", str(ch["par_moves"]) + " moves")

        # Board size
        info_row("Board", f"{board_n} × {board_n}")

        # Stars hint
        sh = font("hint").render(ch["stars_hint"], True, th["hint_text"])
        srf.blit(sh, (ix, iy))
        iy += 22

        # Full description
        pygame.draw.line(srf, th["divider"],
                        (MODAL_X + 20, MODAL_Y + 290),
                        (MODAL_X + MODAL_W - 20, MODAL_Y + 290), 1)

        desc_lines = ch["description"].replace("\n", " ").split(". ")
        dy = MODAL_Y + 304
        for line in desc_lines[:2]:
            if not line.endswith("."): line += "."
            ds = font("small").render(line, True, th["lbl_text"])
            blit_centered(srf, ds, cx, dy)
            dy += 22

        # Previous stars (if any)
        prog  = self._progress.get(str(ch["id"]), {})
        stars = prog.get("stars", 0)
        best  = prog.get("best_moves")
        if stars > 0:
            star_y = MODAL_Y + 362
            prev_s = font("hint").render("Your best:", True, th["lbl_text"])
            blit_centered(srf, prev_s, cx, star_y - 18)
            _draw_stars(srf, stars, cx, star_y)
            if best:
                bm = font("hint").render(f"{best} moves", True, th["hint_text"])
                blit_centered(srf, bm, cx, star_y + 22)
        else:
            not_played = font("hint").render("Not played yet", True, th["hint_text"])
            blit_centered(srf, not_played, cx, MODAL_Y + 360)

        self._start_btn.draw(srf, th)
        self._cancel_btn.draw(srf, th)
