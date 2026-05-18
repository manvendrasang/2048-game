# ── Tile colours
# Each power-of-2 tile gets its own warm/pastel colour.
# Values beyond 2048 fall back to GOLD so the game never crashes.

BLACK       = (  0,   0,   0)
WHITE       = (255, 255, 255)
GRAY_DARK   = ( 30,  30,  40)

color_dict = {
    0:    ( 50,  50,  65),   # empty cell – dark slate
    2:    (238, 228, 218),   # cream
    4:    (237, 224, 200),   # warm wheat
    8:    (242, 177, 121),   # peach
    16:   (245, 149,  99),   # orange
    32:   (246, 124,  95),   # coral
    64:   (246,  94,  59),   # deep orange-red
    128:  (237, 207, 114),   # gold-yellow
    256:  (237, 204,  97),   # golden
    512:  (237, 200,  80),   # amber
    1024: (237, 197,  63),   # bright gold
    2048: (237, 194,  46),   # vivid gold
}

FALLBACK_COLOR = (60, 180, 120)   # emerald – shown for 4096+


def getColor(value: int) -> tuple:
    """Return the RGB colour for *value*, with a safe fallback."""
    return color_dict.get(value, FALLBACK_COLOR)


def getTextColor(value: int) -> tuple:
    """Dark text for light tiles (2, 4), white for everything else."""
    return (119, 110, 101) if value in (0, 2, 4) else WHITE