# ── utils/drawing.py
# Shared drawing helpers used across all screens.

import pygame

_fonts: dict = {}


def init_fonts():
    global _fonts
    _fonts = {
        "title":    pygame.font.SysFont("consolas", 42, bold=True),
        "tile_lg":  pygame.font.SysFont("consolas", 36, bold=True),
        "tile_md":  pygame.font.SysFont("consolas", 26, bold=True),
        "tile_sm":  pygame.font.SysFont("consolas", 18, bold=True),
        "hud":      pygame.font.SysFont("consolas", 20, bold=True),
        "small":    pygame.font.SysFont("consolas", 15),
        "over":     pygame.font.SysFont("consolas", 48, bold=True),
        "hint":     pygame.font.SysFont("consolas", 13),
        "menu_big": pygame.font.SysFont("consolas", 32, bold=True),
        "menu_med": pygame.font.SysFont("consolas", 22, bold=True),
        "label":    pygame.font.SysFont("consolas", 17),
        "timer":    pygame.font.SysFont("consolas", 28, bold=True),
    }


def font(name: str) -> pygame.font.Font:
    return _fonts[name]


def draw_rounded_rect(surface, color, rect, radius=10):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_rounded_rect_border(surface, color, rect, radius=10, width=2):
    pygame.draw.rect(surface, color, rect, border_radius=radius, width=width)


class Button:
    """Simple clickable button with hover state."""
    def __init__(self, rect: pygame.Rect, text: str,
                 bg=(60, 60, 80), fg=(220, 220, 230),
                 hover_bg=(80, 80, 110), radius=10,
                 font_name="menu_med"):
        self.rect      = rect
        self.text      = text
        self.bg        = bg
        self.fg        = fg
        self.hover_bg  = hover_bg
        self.radius    = radius
        self.font_name = font_name
        self._hovered  = False

    def update(self, mouse_pos):
        self._hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))

    def draw(self, surface, theme: dict):
        bg = self.hover_bg if self._hovered else self.bg
        draw_rounded_rect(surface, bg, self.rect, self.radius)
        f   = font(self.font_name)
        lbl = f.render(self.text, True, self.fg)
        surface.blit(lbl, lbl.get_rect(center=self.rect.center))


def blit_centered(surface, text_surf, cx, cy):
    r = text_surf.get_rect(centerx=cx, centery=cy)
    surface.blit(text_surf, r)


def format_time(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"