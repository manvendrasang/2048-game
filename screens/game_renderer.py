# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring, unused-import, multiple-statements, protected-access
# pylint: disable=unused-argument, no-member

import pygame
import constants as C
from constants import (
    WIN_W, WIN_H, BOARD_PX, BOARD_TOP, BOARD_LEFT, PADDING,
    MODE_TARGET, MODE_TIME_ATTACK, MODE_CHALLENGE, MODE_DAILY,
)
from utils.drawing import draw_rounded_rect, font, blit_centered, format_time
from constants import getColor, getTextColor
import utils.theme as theme



def tile_rect(row: int, col: int, size: int) -> pygame.Rect:
    cell = (BOARD_PX - PADDING * (size + 1)) / size
    x    = BOARD_LEFT + PADDING + col * (cell + PADDING)
    y    = BOARD_TOP  + PADDING + row * (cell + PADDING)
    return pygame.Rect(int(x), int(y), int(cell), int(cell))


def tile_center(row: int, col: int, size: int) -> tuple[int, int]:
    r = tile_rect(row, col, size)
    return r.centerx, r.centery



def _choose_tile_font(value: int) -> pygame.font.Font:
    d = len(str(value))
    if d <= 2:   return font("tile_lg")
    elif d == 3: return font("tile_md")
    else:        return font("tile_sm")


def draw_board(surface: pygame.Surface, gs, haptic=None):
    th        = theme.get()
    n         = gs.size
    cell_size = (BOARD_PX - PADDING * (n + 1)) / n
    board_rect = pygame.Rect(BOARD_LEFT, BOARD_TOP, BOARD_PX, BOARD_PX)
    draw_rounded_rect(surface, th["board_bg"], board_rect, 14)

    animating = gs.slide_anim.animating

    # Draw empty cell slots always
    for r in range(n):
        for c in range(n):
            base = tile_rect(r, c, n)
            draw_rounded_rect(surface, th["cell_empty"], base, 10)

    if animating:
        # During slide: draw non-moving tiles from final matrix, skip tiles
        # that are being animated (they will be drawn by slide system on top)
        moving_dsts = {(int(round((s.dst_y - BOARD_TOP - PADDING) / (cell_size + PADDING))),
                        int(round((s.dst_x - BOARD_LEFT - PADDING) / (cell_size + PADDING))))
                    for s in gs.slide_anim._slides}

        for r in range(n):
            for c in range(n):
                val = gs.matrix[r][c]
                if val == 0 or (r, c) in moving_dsts:
                    continue
                base = tile_rect(r, c, n)
                draw_rounded_rect(surface, getColor(val), base, 10)
                tf  = _choose_tile_font(val)
                lbl = tf.render(str(val), True, getTextColor(val))
                surface.blit(lbl, lbl.get_rect(center=base.center))

        # Draw sliding tiles on top
        gs.slide_anim.draw(
            surface, n, cell_size,
            getColor, getTextColor, _choose_tile_font,
            draw_rounded_rect, theme,
        )
    else:
        # Normal draw with scale animations (spawn pop, merge pop)
        for r in range(n):
            for c in range(n):
                base = tile_rect(r, c, n)
                val  = gs.matrix[r][c]
                sc   = gs.tile_scales[r][c]
                cx2, cy2 = base.centerx, base.centery
                w = int(base.width  * sc)
                h = int(base.height * sc)
                tr = pygame.Rect(cx2 - w//2, cy2 - h//2, w, h)
                color = getColor(val) if val else th["cell_empty"]
                draw_rounded_rect(surface, color, tr, max(4, int(10 * sc)))
                if val:
                    tf  = _choose_tile_font(val)
                    lbl = tf.render(str(val), True, getTextColor(val))
                    surface.blit(lbl, lbl.get_rect(center=(cx2, cy2)))

    # Haptic border flash drawn on top of everything
    if haptic:
        haptic.update()
        haptic.draw_border(surface, board_rect)



def _draw_undo_tokens(surface: pygame.Surface, gs, th: dict):
    """Draw undo token circles: filled = available, hollow = spent."""
    tokens_total = 3
    r     = 8
    gap   = 6
    start_x = BOARD_LEFT
    y     = 112
    lbl   = font("hint").render("Undos:", True, th["lbl_text"])
    surface.blit(lbl, (start_x, y - lbl.get_height() // 2))
    ox = start_x + lbl.get_width() + 8
    for i in range(tokens_total):
        cx = ox + i * (r * 2 + gap) + r
        if i < gs.undo_tokens:
            pygame.draw.circle(surface, th["accent"], (cx, y), r)
        else:
            pygame.draw.circle(surface, th["divider"], (cx, y), r)
            pygame.draw.circle(surface, th["hint_text"], (cx, y), r, 1)


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

    score_box("SCORE", str(gs.score), WIN_W - 300, 14)
    score_box("BEST",  str(gs.best),  WIN_W - 160, 14)

    # Move counter — skip in daily mode (shown differently below)
    if gs.mode != MODE_DAILY:
        mv = font("small").render(f"Moves: {gs.moves}", True, th["move_text"])
        surface.blit(mv, (BOARD_LEFT, 90))

    # Undo tokens — shown for all modes except daily/challenge
    if gs.mode not in (MODE_DAILY, MODE_CHALLENGE):
        _draw_undo_tokens(surface, gs, th)

    # Mode-specific right-side info
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
    elif gs.mode == MODE_CHALLENGE and gs.challenge:
        ch = gs.challenge
        gt = ch["goal_type"]
        gv = ch["goal_value"]
        if gt == "tile":
            goal_lbl = f"Tile: {gs.highest_tile()} / {gv}"
        else:
            goal_lbl = f"Score: {gs.score:,} / {gv:,}"
        g_surf = font("small").render(goal_lbl, True, th["accent"])
        surface.blit(g_surf, g_surf.get_rect(right=WIN_W - 30, top=mode_y))
        ml = ch["move_limit"]
        if ml > 0:
            left  = max(0, ml - gs.moves)
            m_col = (220, 80, 80) if left <= 5 else th["lbl_text"]
            m_lbl = font("small").render(f"Moves left: {left}", True, m_col)
            surface.blit(m_lbl, m_lbl.get_rect(right=WIN_W - 30, top=mode_y + 22))
        n_lbl = font("hint").render(ch["name"], True, th["hint_text"])
        surface.blit(n_lbl, (BOARD_LEFT, 90))
    elif gs.mode == MODE_DAILY:
        from data.daily_puzzle import daily_puzzle_number, daily_date_str, get_daily_description
        # right side: puzzle number + date
        num_lbl = font("small").render(
            f"Daily Puzzle #{daily_puzzle_number()}", True, th["accent"]
        )
        surface.blit(num_lbl, num_lbl.get_rect(right=WIN_W - 30, top=mode_y))
        date_lbl = font("hint").render(daily_date_str(), True, th["lbl_text"])
        surface.blit(date_lbl, date_lbl.get_rect(right=WIN_W - 30, top=mode_y + 20))
        # left side row 1: moves counter
        mv_daily = font("small").render(f"Moves: {gs.moves}", True, th["move_text"])
        surface.blit(mv_daily, (BOARD_LEFT, 90))
        # left side row 2: description (on its own line, clearly below moves)
        desc_lbl = font("hint").render(get_daily_description(), True, th["hint_text"])
        surface.blit(desc_lbl, (BOARD_LEFT, 110))

    # Hint bar
    sound_icon = "[M] Mute" if sound_on else "[M] Unmute"
    if gs.mode == MODE_DAILY:
        hints = f"[Arrows] Move  [P] Pause  [T] Theme  {sound_icon}  [ESC] Menu  · No undo/save"
    else:
        hints = f"[Arrows] Move  [U] Undo  [S] Save  [P] Pause  [T] Theme  {sound_icon}  [ESC] Menu"
    hint_surf = font("hint").render(hints, True, th["hint_text"])
    surface.blit(hint_surf, (WIN_W//2 - hint_surf.get_width()//2, WIN_H - 20))



def draw_score_popups(surface: pygame.Surface, gs):
    th = theme.get()
    for p in gs.score_popups:
        x, y, val, alpha, _ = p
        txt = font("hud").render(f"+{val}", True, th["accent"])
        txt.set_alpha(max(0, alpha))
        surface.blit(txt, txt.get_rect(centerx=x, centery=int(y)))



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
    blit_centered(surface, font("over").render("PAUSED",
                                            True, th["hud_text"]), WIN_W//2, WIN_H//2 - 40)
    blit_centered(surface, font("hud").render("[ P ] Resume",
                                            True, (160,160,180)), WIN_W//2, WIN_H//2 + 30)
