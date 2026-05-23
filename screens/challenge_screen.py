# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate, unused-argument
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring, unused-import, f-string-without-interpolation

import pygame
from constants import WIN_W, WIN_H
from utils.drawing import draw_rounded_rect, font, blit_centered, Button, panel_mouse_pos
import utils.theme as theme
import systems.sound as sound
from data.challenges import all_challenges
from data.persistence import load_challenge_progress

# ── Grid layout
COLS      = 2
CARD_W    = 230
CARD_H    = 110
GAP_X     = 16
GAP_Y     = 10
GRID_LEFT = WIN_W // 2 - (COLS * CARD_W + GAP_X) // 2
GRID_TOP  = 148

# Star colours
STAR_ON  = (237, 194,  46)
STAR_OFF = (70,  70,   90)
STAR_R   = 8

def _draw_stars(srf, n_stars: int, cx: int, y: int):
    """Draw 3 stars centred at cx, n_stars filled."""
    spacing = STAR_R * 2 + 5
    xs = [cx + (i - 1) * spacing for i in range(3)]
    for i, x in enumerate(xs):
        col = STAR_ON if i < n_stars else STAR_OFF
        # Simple filled polygon star
        points = []
        import math
        for k in range(5):
            angle = math.radians(-90 + k * 72)
            points.append((x + STAR_R * math.cos(angle),
                            y + STAR_R * math.sin(angle)))
            angle2 = math.radians(-90 + k * 72 + 36)
            points.append((x + STAR_R * 0.45 * math.cos(angle2),
                            y + STAR_R * 0.45 * math.sin(angle2)))
        pygame.draw.polygon(srf, col, points)

class ChallengeScreen:
    """
    Returns:
        int   — challenge id to start
        "back" — return to menu
        None  — no action
    """
    def __init__(self, surface: pygame.Surface):
        self.surface   = surface
        self._hovered  = -1
        self._back_btn = Button(
            pygame.Rect(WIN_W // 2 - 110, WIN_H - 66, 220, 46),
            "← Back", font_name="menu_med",
        )
    def _card_rect(self, idx: int) -> pygame.Rect:
        col = idx % COLS
        row = idx // COLS
        x   = GRID_LEFT + col * (CARD_W + GAP_X)
        y   = GRID_TOP  + row * (CARD_H + GAP_Y)
        return pygame.Rect(x, y, CARD_W, CARD_H)

    # events
    def handle_event(self, event) -> int | str | None:
        if self._back_btn.is_clicked(event):
            sound.play("click")
            return "back"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            import constants as C
            px = event.pos[0] - C.PANEL_OX
            py = event.pos[1] - C.PANEL_OY
            challenges = all_challenges()
            for i, ch in enumerate(challenges):
                if self._card_rect(i).collidepoint(px, py):
                    sound.play("click")
                    return ch["id"]
        return None
    def update(self):
        mp = panel_mouse_pos()
        self._hovered = -1
        for i in range(len(all_challenges())):
            if self._card_rect(i).collidepoint(mp):
                self._hovered = i
                break
        self._back_btn.update(mp)

    # draw
    def draw(self):
        th         = theme.get()
        srf        = self.surface
        dark       = theme.name() == "dark"
        srf.fill(th["bg"])
        hdr = font("over").render("Challenges", True, th["accent"])
        blit_centered(srf, hdr, WIN_W // 2, 62)
        sub = font("small").render(
            "Complete goals to earn stars", True, th["lbl_text"]
        )
        blit_centered(srf, sub, WIN_W // 2, 108)
        pygame.draw.line(srf, th["divider"], (28, 130), (WIN_W - 28, 130), 1)
        challenges = all_challenges()
        progress   = load_challenge_progress()
        for i, ch in enumerate(challenges):
            rect    = self._card_rect(i)
            hovered = i == self._hovered
            prog    = progress.get(str(ch["id"]), {})
            stars   = prog.get("stars", 0)
            best_mv = prog.get("best_moves", None)
            done    = prog.get("completed", False)
            # ── card background
            if done:
                bg = (38, 55, 38) if dark else (215, 235, 210)
            else:
                bg = (44, 46, 62) if dark else (218, 212, 200)
            if hovered:
                bg = tuple(min(255, c + 18) for c in bg)
            draw_rounded_rect(srf, bg, rect, 12)
            # left accent bar — colour by difficulty (1-3 green, 4-6 amber, 7-10 red)
            cid = ch["id"]
            bar_col = (
                (70, 180,  80) if cid <= 3 else
                (210, 160,  40) if cid <= 6 else
                (200,  70,  60)
            )
            pygame.draw.rect(srf, bar_col,
                            pygame.Rect(rect.left, rect.top, 4, rect.height),
                            border_top_left_radius=12,
                            border_bottom_left_radius=12)
            if hovered:
                pygame.draw.rect(srf, th["accent"], rect,
                                width=2, border_radius=12)
            # ── challenge number badge
            badge = pygame.Rect(rect.left + 10, rect.top + 8, 26, 26)
            draw_rounded_rect(srf, bar_col, badge, 6)
            num = font("hint").render(str(cid), True, (255, 255, 255))
            srf.blit(num, num.get_rect(center=badge.center))
            # ── name
            name_surf = font("label").render(ch["name"], True, th["hud_text"])
            srf.blit(name_surf, (rect.left + 42, rect.top + 10))
            # ── description (two lines max)
            desc_lines = ch["description"].split("\n")
            for li, line in enumerate(desc_lines[:2]):
                d = font("hint").render(line, True, th["lbl_text"])
                srf.blit(d, (rect.left + 10, rect.top + 38 + li * 16))
            # ── stars (bottom right area)
            _draw_stars(srf, stars, rect.right - 46, rect.top + 14)
            # ── best moves badge
            if best_mv and done:
                mv_txt = font("hint").render(f"Best: {best_mv}mv", True, th["hint_text"])
                srf.blit(mv_txt, mv_txt.get_rect(
                    right=rect.right - 8, bottom=rect.bottom - 6))
            # ── goal hint
            if ch["goal_type"] == "tile":
                goal_str = f"Goal: {ch['goal_value']} tile"
            elif ch["goal_type"] == "score":
                goal_str = f"Goal: {ch['goal_value']:,} pts"
            else:
                goal_str = f"Goal: survive"
            if ch["move_limit"] > 0:
                goal_str += f"  ·  {ch['move_limit']} moves"
            gs_surf = font("hint").render(goal_str, True, th["accent"])
            srf.blit(gs_surf, (rect.left + 10, rect.bottom - 20))
        self._back_btn.draw(srf, th)
        ver = font("hint").render("2048 Enhanced Edition  v2.0", True, th["hint_text"])
        srf.blit(ver, (WIN_W // 2 - ver.get_width() // 2, WIN_H - 20))