# Logical game panel (fixed, never changes)
WIN_W, WIN_H   = 540, 660
BOARD_PX       = 460
BOARD_TOP      = 140
BOARD_LEFT     = 30
PADDING        = 8
DEFAULT_BOARD  = 4

# Fullscreen display dimensions (resolved at runtime)
DISPLAY_W: int = WIN_W
DISPLAY_H: int = WIN_H
PANEL_OX:  int = 0
PANEL_OY:  int = 0


def set_display_size(dw: int, dh: int):
    global DISPLAY_W, DISPLAY_H, PANEL_OX, PANEL_OY
    DISPLAY_W = dw
    DISPLAY_H = dh
    PANEL_OX  = (dw - WIN_W) // 2
    PANEL_OY  = (dh - WIN_H) // 2


# Animation
ANIM_SPEED     = 0.18

# Game modes
MODE_CLASSIC     = "classic"
MODE_TARGET      = "target"
MODE_TIME_ATTACK = "time_attack"

TIME_ATTACK_SECONDS = 120
TARGET_TILE_DEFAULT = 2048

# Theme colours (dark)
THEME_DARK = {
    "bg":           (18,  18,  28),
    "board_bg":     (42,  42,  58),
    "cell_empty":   (50,  50,  65),
    "hud_text":     (220, 220, 230),
    "score_box_bg": (50,  50,  70),
    "accent":       (237, 194,  46),
    "hint_text":    (90,  90, 110),
    "move_text":    (140, 140, 160),
    "lbl_text":     (160, 160, 180),
    "outer_bg":     (10,  10,  18),
    "divider":      (60,  60,  80),
    "toggle_on":    (80, 180,  80),
    "toggle_off":   (120,  60,  60),
}

# Theme colours (light)
THEME_LIGHT = {
    "bg":           (250, 248, 239),
    "board_bg":     (185, 173, 160),
    "cell_empty":   (205, 193, 180),
    "hud_text":     (50,  50,  60),
    "score_box_bg": (185, 173, 160),
    "accent":       (160, 100,   0),
    "hint_text":    (140, 130, 120),
    "move_text":    (100,  90,  80),
    "lbl_text":     (120, 110, 100),
    "outer_bg":     (220, 215, 200),
    "divider":      (160, 148, 130),
    "toggle_on":    (60, 160,  60),
    "toggle_off":   (180,  80,  60),
}

# Tile colours
BLACK       = (  0,   0,   0)
WHITE       = (255, 255, 255)
GRAY_DARK   = ( 30,  30,  40)

color_dict = {
    0:    ( 50,  50,  65),
    2:    (238, 228, 218),
    4:    (237, 224, 200),
    8:    (242, 177, 121),
    16:   (245, 149,  99),
    32:   (246, 124,  95),
    64:   (246,  94,  59),
    128:  (237, 207, 114),
    256:  (237, 204,  97),
    512:  (237, 200,  80),
    1024: (237, 197,  63),
    2048: (237, 194,  46),
}
FALLBACK_COLOR = (60, 180, 120)


def getColor(value: int) -> tuple:
    return color_dict.get(value, FALLBACK_COLOR)


def getTextColor(value: int) -> tuple:
    return (119, 110, 101) if value in (0, 2, 4) else WHITE


# Particle burst config per threshold
PARTICLE_CONFIGS = {
    256:  {"count": 18, "speed": 4.0, "size": 5,  "color": (237, 204,  97), "lifetime": 35},
    512:  {"count": 28, "speed": 5.5, "size": 7,  "color": (237, 200,  80), "lifetime": 45},
    1024: {"count": 40, "speed": 7.0, "size": 9,  "color": (237, 197,  63), "lifetime": 55},
    2048: {"count": 60, "speed": 9.0, "size": 11, "color": (237, 194,  46), "lifetime": 70},
}