import pygame
from constants import WIN_W, WIN_H
from utils.drawing import draw_rounded_rect, font, blit_centered, Button, panel_mouse_pos
import utils.theme as theme
import systems.sound as sound


class StatsScreen:
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
        self._back.update(panel_mouse_pos())

    def draw(self, stats: dict):
        th  = theme.get()
        srf = self.surface
        srf.fill(th["bg"])

        hdr = font("over").render("Statistics", True, th["accent"])
        blit_centered(srf, hdr, WIN_W//2, 65)

        games  = stats["games_played"]
        total  = stats["total_score"]
        avg    = (total // games) if games else 0
        hi     = stats["highest_tile"]
        moves  = stats["total_moves"]
        avg_mv = (moves // games) if games else 0

        rows = [
            ("Games Played",      str(games)),
            ("Highest Tile Ever", str(hi)),
            ("Total Score",       f"{total:,}"),
            ("Average Score",     f"{avg:,}"),
            ("Total Moves",       f"{moves:,}"),
            ("Avg Moves / Game",  str(avg_mv)),
        ]

        card_w, card_h = 400, 58
        cx      = WIN_W // 2
        start_y = 128

        for i, (label, value) in enumerate(rows):
            y    = start_y + i * (card_h + 8)
            rect = pygame.Rect(cx - card_w//2, y, card_w, card_h)
            bg   = (50, 50, 70) if theme.name() == "dark" else (210, 200, 190)
            draw_rounded_rect(srf, bg, rect, 10)
            lbl  = font("label").render(label, True, th["lbl_text"])
            val  = font("hud").render(value,   True, th["accent"])
            srf.blit(lbl, (rect.left + 18, rect.centery - lbl.get_height()//2))
            srf.blit(val, val.get_rect(right=rect.right - 18, centery=rect.centery))

        self._back.draw(srf, th)