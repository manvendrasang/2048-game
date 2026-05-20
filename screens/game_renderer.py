# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate, unused-argument
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring, unused-import

import pygame
import constants as C
from constants import (
    WIN_W, WIN_H, BOARD_PX, BOARD_TOP, BOARD_LEFT, PADDING,
    MODE_TARGET, MODE_TIME_ATTACK,
)
from utils.drawing import draw_rounded_rect, font, blit_centered, format_time
from constants import getColor, getTextColor
import utils.theme as theme


# geometry helper

def tile_rect(row: int, col: int, size: int) -> pygame.Rect:
    cell = (BOARD_PX - PADDING * (size + 1)) / size
    x    = BOARD_LEFT + PADDING + col * (cell + PADDING)
    y    = BOARD_TOP  + PADDING + row * (cell + PADDING)
    return pygame.Rect(int(x), int(y), int(cell), int(cell))


def tile_center(row: int, col: int, size: int) -> tuple[int, int]:
    r = tile_rect(row, col, size)
    return r.centerx, r.centery


# board

def _choose_tile_font(value: int) -> pygame.font.Font:
    d = len(str(value))
    if d <= 2:   return font("tile_lg")
    elif d == 3: return font("tile_md")
    else:        return font("tile_sm")


def draw_board(surface: pygame.Surface, gs):
    th = theme.get()
    board_rect = pygame.Rect(BOARD_LEFT, BOARD_TOP, BOARD_PX, BOARD_PX)
    draw_rounded_rect(surface, th["board_bg"], board_rect, 14)

    n = gs.size
    for r in range(n):
        for c in range(n):
            base = tile_rect(r, c, n)
            val  = gs.matrix[r][c]
            sc   = gs.tile_scales[r][c]
            cx, cy = base.centerx, base.centery
            w    = int(base.width  * sc)
            h    = int(base.height * sc)
            tr   = pygame.Rect(cx - w//2, cy - h//2, w, h)

            color = getColor(val) if val else th["cell_empty"]
            draw_rounded_rect(surface, color, tr, max(4, int(10 * sc)))

            if val:
                tf  = _choose_tile_font(val)
                lbl = tf.render(str(val), True, getTextColor(val))
                surface.blit(lbl, lbl.get_rect(center=(cx, cy)))

# HUD

def draw_hud(surface: pygame.Surface, gs, sound_on: bool, paused: bool):
    th = theme.get()

    # Title
    title = font("title").render("2048", True, th["accent"])
    surface.blit(title, (BOARD_LEFT, 14))

    # Score boxes
    def score_box(label_txt, val_txt, x, y, w=110, h=55):
        box = pygame.Rect(x, y, w, h)
        draw_rounded_rect(surface, th["score_box_bg"], box, 10)
        lbl = font("small").render(label_txt, True, th["lbl_text"])
        val = font("hud").render(val_txt,     True, th["hud_text"])
        surface.blit(lbl, lbl.get_rect(centerx=x+w//2, top=y+6))
        surface.blit(val, val.get_rect(centerx=x+w//2, top=y+24))

    score_box("SCORE", str(gs.score), WIN_W - 250, 14)
    score_box("BEST",  str(gs.best),  WIN_W - 130, 14)

    # Move counter
    mv = font("small").render(f"Moves: {gs.moves}", True, th["move_text"])
    surface.blit(mv, (BOARD_LEFT, 90))

    # Mode timer
    mode_y = 90
    if gs.mode == MODE_TARGET:
        t_lbl = font("timer").render(f"  {format_time(gs.elapsed)}", True, th["accent"])
        surface.blit(t_lbl, t_lbl.get_rect(right=WIN_W - 30, centery=mode_y + 10))
        m_lbl = font("small").render(f"Target: {gs.target_tile}", True, th["lbl_text"])
        surface.blit(m_lbl, m_lbl.get_rect(right=WIN_W - 30, top=mode_y + 28))
    elif gs.mode == MODE_TIME_ATTACK:
        remaining = max(0, gs.time_budget - gs.elapsed)
        color     = (220, 80, 80) if remaining < 20 else th["accent"]
        t_lbl     = font("timer").render(f"  {format_time(remaining)}", True, color)
        surface.blit(t_lbl, t_lbl.get_rect(right=WIN_W - 30, centery=mode_y + 10))

    # Hint bar
    sound_icon = "[M] Mute" if sound_on else "[M] Unmute"
    hints = f"[Arrows] Move  [U] Undo  [S] Save  [P] Pause  [T] Theme  {sound_icon}  [ESC] Menu"
    hint_surf = font("hint").render(hints, True, th["hint_text"])
    surface.blit(hint_surf, (WIN_W//2 - hint_surf.get_width()//2, WIN_H - 20))


# score popups

def draw_score_popups(surface: pygame.Surface, gs):
    th = theme.get()
    for p in gs.score_popups:
        x, y, val, alpha, _ = p
        txt = font("hud").render(f"+{val}", True, th["accent"])
        txt.set_alpha(max(0, alpha))
        surface.blit(txt, txt.get_rect(centerx=x, centery=int(y)))


# overlays

def _overlay(surface, alpha=210):
    ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    ov.fill((18, 18, 28, alpha))
    surface.blit(ov, (0, 0))


def draw_game_over(surface: pygame.Surface, gs):
    _overlay(surface)
    th = theme.get()
    cx = WIN_W // 2
    blit_centered(surface, font("over").render("Game Over!", True, (255, 100, 100)), cx, 210)
    blit_centered(surface, font("hud").render(f"Score: {gs.score}", True, th["hud_text"]), cx, 295)
    blit_centered(surface, font("hud").render(f"Best:  {gs.best}",  True, th["accent"]),   cx, 335)
    blit_centered(surface, font("hud").render("[ R ] Restart   [ ESC ] Menu",
                                            True, (180, 180, 200)), cx, 395)


def draw_win(surface: pygame.Surface, gs):
    _overlay(surface, 200)
    th = theme.get()
    cx = WIN_W // 2
    blit_centered(surface, font("over").render("You Win!", True, th["accent"]), cx, 200)
    blit_centered(surface, font("hud").render(f"Score: {gs.score}", True, th["hud_text"]), cx, 285)
    if gs.mode == MODE_TARGET:
        blit_centered(surface, font("hud").render(
            f"Time:  {format_time(gs.elapsed)}", True, th["accent"]), cx, 325)
    blit_centered(surface, font("hud").render("[ R ] Restart   [ ESC ] Menu",
                                            True, (180, 180, 200)), cx, 395)


def draw_pause(surface: pygame.Surface):
    _overlay(surface, 180)
    th = theme.get()

    blit_centered(surface, font("over")
                .render("PAUSED", True, th["hud_text"]), WIN_W//2, WIN_H//2 - 40)
    blit_centered(surface, font("hud")
                .render("[ P ] Resume", True, (160,160,180)), WIN_W//2, WIN_H//2 + 30)