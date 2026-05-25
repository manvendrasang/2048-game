# pylint: disable=missing-module-docstring, missing-function-docstring, no-member

import pygame
import math
from constants import WIN_W, WIN_H
from utils.drawing import draw_rounded_rect, font, blit_centered, Button, panel_mouse_pos
import utils.theme as theme
import systems.sound as sound

STAR_R    = 22
STAR_ON   = (237, 194,  46)
STAR_OFF  = (55,  55,   72)
STAR_GLOW = (255, 230, 100)

def _star_points(cx, cy, r, n=5):
    pts = []
    for k in range(n):
        a1 = math.radians(-90 + k * 72)
        pts.append((cx + r * math.cos(a1), cy + r * math.sin(a1)))
        a2 = math.radians(-90 + k * 72 + 36)
        pts.append((cx + r * 0.42 * math.cos(a2), cy + r * 0.42 * math.sin(a2)))
    return pts
def _draw_star(srf, filled: bool, cx: int, cy: int, r: int = STAR_R):
    col = STAR_ON if filled else STAR_OFF
    pts = _star_points(cx, cy, r)
    if filled:
        # glow halo
        glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*STAR_GLOW, 40), (r * 2, r * 2), r * 2)
        srf.blit(glow, (cx - r * 2, cy - r * 2))
    pygame.draw.polygon(srf, col, pts)
    pygame.draw.polygon(srf, (255, 255, 255, 80) if filled else STAR_OFF,
                        pts, 1)

class ChallengeResultScreen:
    """
    Returns:
        "retry"      — restart same challenge
        "challenges" — back to challenge picker
        "menu"       — main menu
    """
    def __init__(self, surface: pygame.Surface):
        self.surface   = surface
        self._won      = False
        self._stars    = 0
        self._score    = 0
        self._moves    = 0
        self._ch_name  = ""
        self._par      = 0
        self._anim_t   = 0.0   # drives star reveal animation
        cx = WIN_W // 2
        self._retry_btn = Button(
            pygame.Rect(cx - 230, WIN_H - 100, 140, 48),
            "↺  Retry", font_name="menu_med",
        )
        self._list_btn = Button(
            pygame.Rect(cx - 70,  WIN_H - 100, 160, 48),
            "Challenges", font_name="menu_med",
        )
        self._menu_btn = Button(
            pygame.Rect(cx + 110, WIN_H - 100, 120, 48),
            "Menu", font_name="menu_med",
        )
    def open(self, won: bool, stars: int, score: int, moves: int,
            ch_name: str, par_moves: int):
        self._won     = won
        self._stars   = stars
        self._score   = score
        self._moves   = moves
        self._ch_name = ch_name
        self._par     = par_moves
        self._anim_t  = 0.0
        if won:
            sound.play("win")
        else:
            sound.play("lose")
    def handle_event(self, event) -> str | None:
        if self._retry_btn.is_clicked(event):
            sound.play("click")
            return "retry"
        if self._list_btn.is_clicked(event):
            sound.play("click")
            return "challenges"
        if self._menu_btn.is_clicked(event):
            sound.play("click")
            return "menu"
        return None
    def update(self, dt: float):
        mp = panel_mouse_pos()
        self._retry_btn.update(mp)
        self._list_btn.update(mp)
        self._menu_btn.update(mp)
        self._anim_t = min(self._anim_t + dt, 2.5)
    def draw(self):
        th   = theme.get()
        srf  = self.surface
        dark = theme.name() == "dark"
        srf.fill(th["bg"])
        cx = WIN_W // 2
        # outcome banner
        if self._won:
            banner_col = th["accent"]
            banner_txt = "Challenge Complete!"
        else:
            banner_col = (200, 80, 80)
            banner_txt = "Challenge Failed"
        banner = font("over").render(banner_txt, True, banner_col)
        blit_centered(srf, banner, cx, 72)
        # challenge name
        name_surf = font("menu_med").render(self._ch_name, True, th["hud_text"])
        blit_centered(srf, name_surf, cx, 124)
        pygame.draw.line(srf, th["divider"], (40, 148), (WIN_W - 40, 148), 1)
        # animated stars (reveal one by one)
        star_cx  = [cx - 56, cx, cx + 56]
        star_y   = 210
        for i in range(3):
            reveal_t = 0.4 + i * 0.45       # each star reveals 0.45s after the last
            filled   = (self._won and i < self._stars and
                        self._anim_t >= reveal_t)
            # scale animation: pop in
            if filled:
                elapsed = self._anim_t - reveal_t
                scale   = min(1.0, elapsed / 0.25)
                r       = int(STAR_R * (0.3 + 0.7 * scale))
            else:
                r = STAR_R
            _draw_star(srf, filled, star_cx[i], star_y, r)
        # stats
        stat_y = 265
        stats  = [
            ("Score",    f"{self._score:,}"),
            ("Moves",    str(self._moves)),
            ("Par",      str(self._par)),
        ]
        card_w = 110
        gap    = 14
        total  = len(stats) * card_w + (len(stats) - 1) * gap
        sx     = cx - total // 2
        for label, val in stats:
            card = pygame.Rect(sx, stat_y, card_w, 66)
            bg   = (48, 50, 68) if dark else (212, 206, 194)
            draw_rounded_rect(srf, bg, card, 10)
            lbl  = font("hint").render(label, True, th["lbl_text"])
            v    = font("hud").render(val,   True, th["accent"])
            srf.blit(lbl, lbl.get_rect(centerx=card.centerx, top=card.top + 8))
            srf.blit(v,   v.get_rect(centerx=card.centerx,   top=card.top + 30))
            sx  += card_w + gap
        # stars label / encouragement
        if self._won:
            msgs = {
                3: "Perfect run!  Gold stars!",
                2: "Great job!  Nearly perfect.",
                1: "Completed!  Can you do better?",
                0: "Completed but no stars — keep practising.",
            }
            msg = font("label").render(msgs[self._stars], True, th["hud_text"])
            blit_centered(srf, msg, cx, 360)
        else:
            hint = font("label").render("Keep trying — you'll get there!", True, th["lbl_text"])
            blit_centered(srf, hint, cx, 360)
        # buttons
        self._retry_btn.draw(srf, th)
        self._list_btn.draw(srf, th)
        self._menu_btn.draw(srf, th)
