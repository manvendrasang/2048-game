# pylint: disable=missing-module-docstring, missing-function-docstring, no-member, broad-exception-caught

import pygame
import random
from datetime import datetime
from constants import WIN_W, WIN_H
from utils.drawing import draw_rounded_rect, font, blit_centered, Button, panel_mouse_pos
import utils.theme as theme
import systems.sound as sound
from data.persistence import get_daily_streak
from data.daily_puzzle import daily_date_str, daily_puzzle_number

TILE_COLORS = {
    2:    (238, 228, 218),  4:    (237, 224, 200),
    8:    (242, 177, 121),  16:   (245, 149,  99),
    32:   (246, 124,  95),  64:   (246,  94,  59),
    128:  (237, 207, 114),  256:  (237, 204,  97),
    512:  (237, 200,  80),  1024: (237, 197,  63),
    2048: (237, 194,  46),
}
def _tile_col(val: int) -> tuple:
    return TILE_COLORS.get(val, (60, 180, 120))

class DailyResultScreen:
    """
    Returns "menu" or None.
    """
    def __init__(self, surface: pygame.Surface):
        self.surface   = surface
        self._result   = None
        self._already  = False
        self._anim_t   = 0.0
        self._confetti = []
        self._confetti_cols = [
            (237, 194, 46), (100, 200, 140), (100, 160, 220),
            (220, 100, 100), (180, 100, 220),
        ]
        cx = WIN_W // 2
        self._menu_btn = Button(
            pygame.Rect(cx - 145, WIN_H - 100, 130, 50),
            "Menu", font_name="menu_med",
        )
        self._share_btn = Button(
            pygame.Rect(cx + 15, WIN_H - 100, 130, 50),
            "Share", font_name="menu_med",
            bg=(50, 100, 160), hover_bg=(70, 130, 200),
        )
    def open(self, result: dict, already_played: bool = False):
        self._result  = result
        self._already = already_played
        self._anim_t  = 0.0
        self._confetti = self._make_confetti()
        if not already_played:
            sound.play("win")
    def _make_confetti(self) -> list:
        return [
            {
                "x":   random.uniform(0, WIN_W),
                "y":   random.uniform(-WIN_H * 0.3, 0),
                "vx":  random.uniform(-1, 1),
                "vy":  random.uniform(1.5, 3.5),
                "col": random.choice(self._confetti_cols),
                "size": random.randint(4, 9),
                "vy0": 0.05,
            }
            for _ in range(70)
        ]
    def handle_event(self, event) -> str | None:
        if self._menu_btn.is_clicked(event):
            sound.play("click")
            return "menu"
        if self._share_btn.is_clicked(event):
            sound.play("click")
            self._copy_result()
        return None
    def _copy_result(self):
        if not self._result:
            return
        r      = self._result
        streak = get_daily_streak()
        txt = (
            f"2048 Daily Puzzle #{daily_puzzle_number()}\n"
            f"Score: {r['score']:,}  Moves: {r['moves']}\n"
            f"Highest Tile: {r['highest_tile']}\n"
            f"Streak: {streak} day{'s' if streak != 1 else ''}"
        )
        try:
            pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, txt.encode())
        except Exception:
            pass
    def update(self, dt: float):
        self._menu_btn.update(panel_mouse_pos())
        self._share_btn.update(panel_mouse_pos())
        self._anim_t = min(self._anim_t + dt, 4.0)
        for p in self._confetti:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.05
        self._confetti = [p for p in self._confetti if p["y"] < WIN_H + 20]
    def draw(self):
        th   = theme.get()
        srf  = self.surface
        dark = theme.name() == "dark"
        srf.fill(th["bg"])
        cx = WIN_W // 2
        if not self._already:
            self._draw_confetti(srf)
        # Header block
        num_str  = f"Daily Puzzle  #{daily_puzzle_number()}"
        hdr      = font("over").render(num_str, True, th["accent"])
        blit_centered(srf, hdr, cx, 72)
        date_surf = font("label").render(daily_date_str(), True, th["lbl_text"])
        blit_centered(srf, date_surf, cx, 124)
        pygame.draw.line(srf, th["divider"], (50, 150), (WIN_W - 50, 150), 1)
        # Status message
        if self._already:
            msg = font("menu_med").render("Already played today!", True, (180, 120, 60))
            blit_centered(srf, msg, cx, 184)
            sub = font("small").render(
                "Come back tomorrow for a new puzzle.", True, th["hint_text"]
            )
            blit_centered(srf, sub, cx, 218)
            stat_top = 255
        else:
            msg = font("menu_med").render("Puzzle Complete!", True, th["accent"])
            blit_centered(srf, msg, cx, 184)
            stat_top = 224
        # Stat cards
        if self._result:
            r      = self._result
            streak = get_daily_streak()
            stats  = [
                ("Score",      f"{r['score']:,}"),
                ("Moves",      str(r["moves"])),
                ("Best Tile",  str(r["highest_tile"])),
                ("Streak",     f"{streak} \U0001f525"),
            ]
            cw, ch2 = 120, 76
            gap     = 12
            total_w = len(stats) * cw + (len(stats) - 1) * gap
            sx      = cx - total_w // 2
            for label, val in stats:
                card = pygame.Rect(sx, stat_top + 20, cw, ch2)
                bg   = (48, 50, 68) if dark else (212, 206, 194)
                draw_rounded_rect(srf, bg, card, 12)
                lbl_s = font("small").render(label, True, th["lbl_text"])
                val_s = font("hud").render(val,     True, th["accent"])
                srf.blit(lbl_s, lbl_s.get_rect(centerx=card.centerx, top=card.top + 10))
                srf.blit(val_s, val_s.get_rect(centerx=card.centerx, top=card.top + 36))
                sx += cw + gap
        # Tile badge
        if self._result:
            ht       = self._result["highest_tile"]
            ht_col   = _tile_col(ht)
            badge_y  = stat_top + 120
            badge    = pygame.Rect(cx - 52, badge_y, 104, 60)
            draw_rounded_rect(srf, ht_col, badge, 14)
            ht_s = font("hud").render(str(ht), True, (255, 255, 255))
            srf.blit(ht_s, ht_s.get_rect(center=badge.center))
            lbl_s = font("hint").render("Highest tile reached", True, th["lbl_text"])
            blit_centered(srf, lbl_s, cx, badge_y + 74)
        # Countdown
        now       = datetime.now()
        midnight  = now.replace(hour=23, minute=59, second=59)
        remaining = (midnight - now).seconds + 1
        hh = remaining // 3600
        mm = (remaining % 3600) // 60
        ss = remaining % 60
        countdown = font("small").render(
            f"Next puzzle in  {hh:02d}:{mm:02d}:{ss:02d}", True, th["hint_text"]
        )
        blit_centered(srf, countdown, cx, WIN_H - 145)
        self._menu_btn.draw(srf, th)
        self._share_btn.draw(srf, th)
        ver = font("hint").render(
            "2048 Enhanced Edition  v2.0", True, th["hint_text"]
        )
        srf.blit(ver, (WIN_W // 2 - ver.get_width() // 2, WIN_H - 20))
    def _draw_confetti(self, srf):
        for p in self._confetti:
            size = p["size"]
            s    = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.rect(s, (*p["col"], 200), pygame.Rect(0, 0, size * 2, size))
            srf.blit(s, (int(p["x"]) - size, int(p["y"]) - size))
