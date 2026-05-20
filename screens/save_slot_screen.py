# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring

import pygame
from constants import WIN_W, WIN_H, MODE_CLASSIC, MODE_TARGET, MODE_TIME_ATTACK
from utils.drawing import draw_rounded_rect, font, blit_centered, Button, panel_mouse_pos
import utils.theme as theme
import systems.sound as sound
from data.persistence import get_save_slots, delete_slot

MODE_LABELS = {
    MODE_CLASSIC:     "Classic",
    MODE_TARGET:      "Target",
    MODE_TIME_ATTACK: "Time Atk",
}

COLS       = 2
ROWS       = 5
SLOT_W     = 220
SLOT_H     = 72
GAP_X      = 14
GAP_Y      = 10
GRID_LEFT  = WIN_W // 2 - (COLS * SLOT_W + GAP_X) // 2
GRID_TOP   = 160


class SaveSlotScreen:
    """
    Returns:
        ("save",   slot_idx)  — caller should save to that slot
        ("load",   slot_idx)  — caller should load from that slot
        ("delete", slot_idx)  — slot was deleted (stay on screen)
        "back"                — user cancelled
        None                  — no action yet
    """

    def __init__(self, surface: pygame.Surface):
        self.surface   = surface
        self.mode      = "save"    # "save" | "load"
        self._slots    = []
        self._hovered  = -1

        back_rect      = pygame.Rect(WIN_W//2 - 110, WIN_H - 66, 220, 46)
        self._back_btn = Button(back_rect, "← Cancel", font_name="menu_med")

    def open(self, mode: str):
        """Call before showing: mode is 'save' or 'load'."""
        self.mode   = mode
        self._slots = get_save_slots()

    def _slot_rect(self, idx: int) -> pygame.Rect:
        col = idx % COLS
        row = idx // COLS
        x   = GRID_LEFT + col * (SLOT_W + GAP_X)
        y   = GRID_TOP  + row * (SLOT_H + GAP_Y)
        return pygame.Rect(x, y, SLOT_W, SLOT_H)

    def handle_event(self, event) -> tuple | str | None:
        if self._back_btn.is_clicked(event):
            sound.play("click")
            return "back"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            import constants as C
            px = event.pos[0] - C.PANEL_OX
            py = event.pos[1] - C.PANEL_OY

            for i in range(10):
                r = self._slot_rect(i)
                if r.collidepoint(px, py):
                    data = self._slots[i]
                    if self.mode == "save":
                        sound.play("click")
                        return ("save", i)
                    elif self.mode == "load":
                        if data is not None:
                            sound.play("click")
                            return ("load", i)
                        # empty slot — do nothing
                    return None

        # Right-click to delete
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            import constants as C
            px = event.pos[0] - C.PANEL_OX
            py = event.pos[1] - C.PANEL_OY
            for i in range(10):
                if self._slot_rect(i).collidepoint(px, py):
                    if self._slots[i] is not None:
                        delete_slot(i)
                        self._slots[i] = None
                        sound.play("click")
                        return ("delete", i)

        return None

    def update(self):
        mp = panel_mouse_pos()
        self._hovered = -1
        for i in range(10):
            if self._slot_rect(i).collidepoint(mp):
                self._hovered = i
                break
        self._back_btn.update(mp)

    def draw(self):
        th  = theme.get()
        srf = self.surface
        srf.fill(th["bg"])

        title_txt = "Save Game — Choose Slot" if self.mode == "save" else "Load Game — Choose Slot"
        hdr = font("menu_big").render(title_txt, True, th["accent"])
        blit_centered(srf, hdr, WIN_W//2, 70)

        hint = "Left-click to select  •  Right-click to delete" if self.mode == "save" else \
            "Left-click to load  •  Right-click to delete"
        h = font("hint").render(hint, True, th["hint_text"])
        blit_centered(srf, h, WIN_W//2, 108)

        pygame.draw.line(srf, th["divider"], (30, 130), (WIN_W-30, 130), 1)

        for i in range(10):
            rect = self._slot_rect(i)
            data = self._slots[i]
            hovered = i == self._hovered

            # background card
            if data:
                bg = (55, 65, 85) if theme.name() == "dark" else (200, 190, 175)
            else:
                bg = (38, 38, 52) if theme.name() == "dark" else (220, 214, 202)
            if hovered:
                r_, g_, b_ = bg
                bg = (min(255, r_+20), min(255, g_+20), min(255, b_+20))

            draw_rounded_rect(srf, bg, rect, 10)
            if hovered:
                pygame.draw.rect(srf, th["accent"], rect, border_radius=10, width=2)

            # slot number badge
            badge_r = pygame.Rect(rect.left + 6, rect.top + 6, 28, 28)
            pygame.draw.rect(srf, th["accent"], badge_r, border_radius=6)
            num = font("small").render(str(i+1), True, (30, 30, 30))
            srf.blit(num, num.get_rect(center=badge_r.center))

            if data:
                # mode pill
                mode_str = MODE_LABELS.get(data.get("mode", ""), "?")
                mode_col = {
                    MODE_CLASSIC:     (80, 140, 200),
                    MODE_TARGET:      (80, 200, 120),
                    MODE_TIME_ATTACK: (200, 120, 80),
                }.get(data.get("mode", ""), (120, 120, 120))

                pill = pygame.Rect(rect.left + 40, rect.top + 8, 68, 20)
                draw_rounded_rect(srf, mode_col, pill, 6)
                ms = font("hint").render(mode_str, True, (255, 255, 255))
                srf.blit(ms, ms.get_rect(center=pill.center))

                sc  = font("hud").render(f"Score: {data['score']:,}", True, th["hud_text"])
                mv  = font("hint").render(
                    f"Moves: {data['moves']}   Tile: {max(max(r) for r in data['matrix'])}",
                    True, th["lbl_text"],
                )
                dt  = font("hint").render(data.get("date", ""), True, th["hint_text"])

                srf.blit(sc,  (rect.left + 8, rect.top + 34))
                srf.blit(mv,  (rect.left + 8, rect.top + 54))
                srf.blit(dt,  dt.get_rect(right=rect.right - 8, top=rect.top + 8))
            else:
                empty = font("label").render("— Empty Slot —", True, th["hint_text"])
                srf.blit(empty, empty.get_rect(center=rect.center))

        self._back_btn.draw(srf, th)

        # footer
        ver = font("hint").render("2048 Enhanced Edition  v2.0", True, th["hint_text"])
        srf.blit(ver, (WIN_W//2 - ver.get_width()//2, WIN_H - 20))