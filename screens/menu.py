# ── screens/menu.py
# Main menu: New Game / Load / Leaderboard / Stats / Quit
# Also handles game-mode selection sub-menu.

import pygame
from constants import WIN_W, WIN_H, MODE_CLASSIC, MODE_TARGET, MODE_TIME_ATTACK
from utils.drawing import Button, draw_rounded_rect, font, blit_centered, format_time
import utils.theme as theme
import utils.drawing as drawing
import systems.sound as sound


# ─────────────────────── helper to build button list ──────────────────── #

def _make_buttons(labels_actions: list[tuple[str, str]], cx: int, start_y: int,
                  w=260, h=52, gap=14) -> list[tuple[Button, str]]:
    btns = []
    for i, (label, action) in enumerate(labels_actions):
        r = pygame.Rect(cx - w//2, start_y + i*(h+gap), w, h)
        btns.append((Button(r, label, font_name="menu_med"), action))
    return btns


# ─────────────────────────── MenuScreen ──────────────────────────────── #

class MenuScreen:
    """
    Returns one of:
        "classic"      → start classic game
        "target"       → start target mode
        "time_attack"  → start time-attack mode
        "load"         → load saved game
        "leaderboard"  → show leaderboard screen
        "stats"        → show stats screen
        "quit"         → exit
    """

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self._sub    = None   # None | "modes"
        self._build_main_buttons()
        self._build_mode_buttons()

    def _build_main_buttons(self):
        items = [
            ("New Game",     "modes"),
            ("Load Game",    "load"),
            ("Leaderboard",  "leaderboard"),
            ("Stats",        "stats"),
            ("Quit",         "quit"),
        ]
        self._main_btns = _make_buttons(items, WIN_W//2, 230)

    def _build_mode_buttons(self):
        items = [
            ("Classic Mode",     MODE_CLASSIC),
            ("Target Mode",      MODE_TARGET),
            ("Time Attack Mode", MODE_TIME_ATTACK),
            ("← Back",           "back"),
        ]
        self._mode_btns = _make_buttons(items, WIN_W//2, 200)

    def handle_event(self, event) -> str | None:
        buttons = self._mode_btns if self._sub == "modes" else self._main_btns
        for btn, action in buttons:
            if btn.is_clicked(event):
                sound.play("click")
                if action == "modes":
                    self._sub = "modes"
                    return None
                if action == "back":
                    self._sub = None
                    return None
                return action
        return None

    def update(self):
        mx, my = pygame.mouse.get_pos()
        buttons = self._mode_btns if self._sub == "modes" else self._main_btns
        for btn, _ in buttons:
            btn.update((mx, my))

    def draw(self):
        th = theme.get()
        self.surface.fill(th["bg"])

        # Title
        acc = th["accent"]
        title = font("over").render("2048", True, acc)
        blit_centered(self.surface, title, WIN_W//2, 100)
        sub = font("small").render(
            "Target Mode  •  Time Attack  •  Classic", True, th["lbl_text"]
        )
        blit_centered(self.surface, sub, WIN_W//2, 155)

        # Buttons
        buttons = self._mode_btns if self._sub == "modes" else self._main_btns
        if self._sub == "modes":
            hdr = font("label").render("Select Game Mode", True, th["hud_text"])
            blit_centered(self.surface, hdr, WIN_W//2, 168)
        for btn, _ in buttons:
            btn.draw(self.surface, th)

        # Mode descriptions (only in mode sub-menu)
        if self._sub == "modes":
            descs = [
                "Infinite play – no time limit",
                "Race to reach 2048 – fastest time wins",
                "Hit target score before time runs out",
                "",
            ]
            buttons_list = self._mode_btns
            for i, ((btn, _), desc) in enumerate(zip(buttons_list, descs)):
                if desc:
                    d = font("hint").render(desc, True, th["hint_text"])
                    self.surface.blit(
                        d, (btn.rect.right + 12, btn.rect.centery - d.get_height()//2)
                    )

        # Footer
        ver = font("hint").render("v2.0  |  ← → ↑ ↓ to move", True, th["hint_text"])
        self.surface.blit(ver, (WIN_W//2 - ver.get_width()//2, WIN_H - 22))