import pygame
import constants as C

_fonts: dict = {}

# Priority list: first available font is used
# On Windows: segoeui / calibri; on Mac: .sfnsdisplay / helvetica;
# on Linux: liberationsans / dejavusans / freesans.
_SOFT_FONTS = [
    "segoeui", "calibri", "sfnsdisplay", "helveticaneue", "helvetica",
    "arial", "liberationsans", "dejavusans", "freesans", "verdana",
]

def _best_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Return the first available soft font, fallback to pygame default."""
    avail = set(pygame.font.get_fonts())
    for name in _SOFT_FONTS:
        if name.replace(" ", "") in avail:
            return pygame.font.SysFont(name, size, bold=bold)
    return pygame.font.SysFont(None, size, bold=bold)


def init_fonts():
    global _fonts
    _fonts = {
        "title":    _best_font(44, bold=True),
        "tile_lg":  _best_font(36, bold=True),
        "tile_md":  _best_font(28, bold=True),
        "tile_sm":  _best_font(19, bold=True),
        "hud":      _best_font(20, bold=True),
        "small":    _best_font(15),
        "over":     _best_font(50, bold=True),
        "hint":     _best_font(13),
        "menu_big": _best_font(34, bold=True),
        "menu_med": _best_font(22, bold=True),
        "label":    _best_font(17),
        "timer":    _best_font(28, bold=True),
        "tab":      _best_font(16, bold=True),
    }


def font(name: str) -> pygame.font.Font:
    return _fonts[name]


def draw_rounded_rect(surface, color, rect, radius=10):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_rounded_rect_border(surface, color, rect, radius=10, width=2):
    pygame.draw.rect(surface, color, rect, border_radius=radius, width=width)


def panel_mouse_pos() -> tuple[int, int]:
    """Return mouse position translated into panel (WIN_W x WIN_H) coords."""
    mx, my = pygame.mouse.get_pos()
    return (mx - C.PANEL_OX, my - C.PANEL_OY)


class Button:
    """Clickable button. All rects are in panel coords."""

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

    def update(self, panel_pos):
        self._hovered = self.rect.collidepoint(panel_pos)

    def is_clicked(self, event) -> bool:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        px = event.pos[0] - C.PANEL_OX
        py = event.pos[1] - C.PANEL_OY
        return self.rect.collidepoint(px, py)

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