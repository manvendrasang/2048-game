# ── screens/leaderboard.py
# Displays the top-5 leaderboard with scores, mode, date, and extra info.

import pygame
from constants import WIN_W, WIN_H, MODE_CLASSIC, MODE_TARGET, MODE_TIME_ATTACK
from utils.drawing import draw_rounded_rect, font, blit_centered, Button
import utils.theme as theme
import systems.sound as sound


MODE_LABELS = {
    MODE_CLASSIC:     "Classic",
    MODE_TARGET:      "Target",
    MODE_TIME_ATTACK: "Time Attack",
}
MODE_COLORS = {
    MODE_CLASSIC:     (100, 160, 220),
    MODE_TARGET:      (100, 220, 140),
    MODE_TIME_ATTACK: (220, 140, 100),
}


class LeaderboardScreen:
    """Returns 'back' when the user wants to return."""

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        back_rect    = pygame.Rect(WIN_W//2 - 100, WIN_H - 70, 200, 44)
        self._back   = Button(back_rect, "← Back", font_name="menu_med")

    def handle_event(self, event) -> str | None:
        if self._back.is_clicked(event):
            sound.play("click")
            return "back"
        return None

    def update(self):
        self._back.update(pygame.mouse.get_pos())

    def draw(self, entries: list):
        th  = theme.get()
        srf = self.surface
        srf.fill(th["bg"])

        # Header
        hdr = font("over").render("Leaderboard", True, th["accent"])
        blit_centered(srf, hdr, WIN_W//2, 60)
        sub = font("small").render("Top 5 All-Time Scores", True, th["lbl_text"])
        blit_centered(srf, sub, WIN_W//2, 108)

        # Column headers
        col_x = [50, 160, 270, 360, 460]
        col_headers = ["#", "Score", "Mode", "Time/Extra", "Date"]
        for x, h in zip(col_x, col_headers):
            lbl = font("label").render(h, True, th["lbl_text"])
            srf.blit(lbl, (x, 140))

        pygame.draw.line(srf, th["lbl_text"], (40, 160), (WIN_W - 40, 160), 1)

        if not entries:
            none = font("hud").render("No scores yet – play a game!", True, th["hint_text"])
            blit_centered(srf, none, WIN_W//2, 280)
        else:
            for i, e in enumerate(entries):
                y   = 176 + i * 58
                row = pygame.Rect(36, y - 6, WIN_W - 72, 48)
                bg  = (50, 50, 70) if theme.name() == "dark" else (210, 200, 190)
                draw_rounded_rect(srf, bg, row, 8)

                rank  = font("hud").render(f"{i+1}", True, th["accent"])
                score = font("hud").render(str(e["score"]), True, th["hud_text"])
                mode_str = MODE_LABELS.get(e["mode"], e["mode"])
                mode_col = MODE_COLORS.get(e["mode"], th["hud_text"])
                mode  = font("label").render(mode_str, True, mode_col)
                extra = font("label").render(e.get("extra", "—") or "—", True, th["hud_text"])
                date  = font("hint").render(e.get("date", ""), True, th["lbl_text"])

                srf.blit(rank,  (col_x[0], y))
                srf.blit(score, (col_x[1], y))
                srf.blit(mode,  (col_x[2], y))
                srf.blit(extra, (col_x[3], y))
                srf.blit(date,  (col_x[4], y))

        self._back.draw(srf, th)