# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring

import sys
import pygame
from pygame.locals import QUIT, KEYDOWN

pygame.init()

import constants as C
info = pygame.display.Info()
DISPLAY = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
pygame.display.set_caption("2048")
C.set_display_size(info.current_w, info.current_h)

from constants import (
    WIN_W, WIN_H, DEFAULT_BOARD,
    MODE_CLASSIC, MODE_TARGET, MODE_TIME_ATTACK,
    TARGET_TILE_DEFAULT, TIME_ATTACK_SECONDS,
)
from utils.drawing import init_fonts
from utils import theme as theme_mod
from game_state import GameState
from systems import sound, particles, screenshake
from systems.bg_particles import BgParticleSystem
from screens.menu import MenuScreen
from screens.game_renderer import (
    draw_board, draw_hud, draw_score_popups,
    draw_game_over, draw_win, draw_pause, tile_center,
)
from screens.leaderboard import LeaderboardScreen
from screens.stats import StatsScreen
from screens.save_slot_screen import SaveSlotScreen
from data.persistence import load_stats, migrate_legacy_save

CLOCK = pygame.time.Clock()
init_fonts()
sound.init()
migrate_legacy_save()

# Panel: slightly larger than WIN_W x WIN_H for a roomier feel
PANEL_W = WIN_W + 20   # 560
PANEL_H = WIN_H + 20   # 680
PANEL   = pygame.Surface((WIN_W, WIN_H))   # game still draws at WIN_W x WIN_H

# Recalculate centring for the drawn border (panel_w x panel_h)
BORDER_OX = C.PANEL_OX - 10
BORDER_OY = C.PANEL_OY - 10

# Background particle system (runs on display coords)
BG = BgParticleSystem(info.current_w, info.current_h)

# ── Screen IDs
SCREEN_MENU      = "menu"
SCREEN_GAME      = "game"
SCREEN_LEADERBOARD = "leaderboard"
SCREEN_STATS     = "stats"
SCREEN_SAVE_SLOT = "save_slot"

current_screen    = SCREEN_MENU
gs                = None
paused            = False
_save_slot_origin = SCREEN_GAME   # which screen triggered the save/load picker

particle_sys = particles.ParticleSystem()
shake_sys    = screenshake.ScreenShake()

menu_screen      = MenuScreen(PANEL)
leader_screen    = LeaderboardScreen(PANEL)
stats_screen     = StatsScreen(PANEL)
save_slot_screen = SaveSlotScreen(PANEL)


# Panel blit with thick rounded border
def _blit_panel(ox: int = 0, oy: int = 0):
    th = theme_mod.get()

    # 1. Outer background
    DISPLAY.fill(th.get("outer_bg", (0, 0, 0)))

    # 2. Background particles
    BG.draw(DISPLAY)

    # 3. Panel shadow (soft dark rect offset slightly)
    shadow = pygame.Surface((PANEL_W + 12, PANEL_H + 12), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 80))
    pygame.draw.rect(shadow, (0, 0, 0, 0),
                    pygame.Rect(0, 0, PANEL_W + 12, PANEL_H + 12),
                    border_radius=22)
    DISPLAY.blit(shadow, (BORDER_OX + ox + 4, BORDER_OY + oy + 6))

    # 4. Panel fill background (slightly larger than WIN_W x WIN_H)
    fill_rect = pygame.Rect(BORDER_OX + ox, BORDER_OY + oy, PANEL_W, PANEL_H)
    pygame.draw.rect(DISPLAY, th["bg"], fill_rect, border_radius=20)

    # 5. Game content (WIN_W x WIN_H centred inside the larger fill)
    DISPLAY.blit(PANEL, (C.PANEL_OX + ox, C.PANEL_OY + oy))

    # 6. Thick rounded border
    border_col = th.get("accent", (237, 194, 46))
    pygame.draw.rect(DISPLAY, border_col, fill_rect, width=3, border_radius=20)

    # 7. Subtle inner glow line
    inner = fill_rect.inflate(-6, -6)
    glow_col = tuple(min(255, c + 40) for c in border_col[:3])
    pygame.draw.rect(DISPLAY, glow_col, inner, width=1, border_radius=18)


#  Game helpers
DIRECTION_MAP = {
    pygame.K_UP:    "up",
    pygame.K_DOWN:  "down",
    pygame.K_LEFT:  "left",
    pygame.K_RIGHT: "right",
}
def start_game(mode=MODE_CLASSIC, size=DEFAULT_BOARD,
            target_tile=TARGET_TILE_DEFAULT,
            time_budget=TIME_ATTACK_SECONDS):
    global gs, paused, current_screen
    gs = GameState(size=size, mode=mode,
                   target_tile=target_tile, time_budget=time_budget)
    gs.reset()
    particle_sys.clear()
    paused = False
    current_screen = SCREEN_GAME
def open_save_slots(mode: str, origin: str):
    global current_screen, _save_slot_origin
    _save_slot_origin = origin
    save_slot_screen.open(mode)
    current_screen = SCREEN_SAVE_SLOT


#  Global key handler (T / M always active)
def handle_global_key(event) -> bool:
    if event.type != KEYDOWN:
        return False
    if event.key == pygame.K_t:
        theme_mod.toggle()
        return True
    if event.key == pygame.K_m:
        sound.toggle()
        return True
    return False


#  Per-screen event handlers
def handle_menu_event(event):
    global current_screen
    result = menu_screen.handle_event(event)
    if result == MODE_CLASSIC:
        start_game(mode=MODE_CLASSIC)
    elif result == MODE_TARGET:
        start_game(mode=MODE_TARGET, target_tile=TARGET_TILE_DEFAULT)
    elif result == MODE_TIME_ATTACK:
        start_game(mode=MODE_TIME_ATTACK, time_budget=TIME_ATTACK_SECONDS)
    elif result == "load":
        open_save_slots("load", SCREEN_MENU)
    elif result == "leaderboard":
        current_screen = SCREEN_LEADERBOARD
    elif result == "stats":
        current_screen = SCREEN_STATS
    elif result == "quit":
        pygame.quit()
        sys.exit()
def handle_game_event(event):
    global paused, current_screen
    if event.type != KEYDOWN:
        return
    k = event.key
    if k == pygame.K_ESCAPE:
        current_screen = SCREEN_MENU
        return
    if k == pygame.K_p:
        paused = not paused
        return
    if paused:
        return
    if k in DIRECTION_MAP and not gs.game_over:
        gs.push_undo()
        moved = gs.move(DIRECTION_MAP[k])
        if moved:
            sound.play("move")
            for (r, c, val) in gs.merge_events:
                cx, cy = tile_center(r, c, gs.size)
                particle_sys.burst(cx, cy, val)
                if val >= 512:
                    sound.play("merge")
            if gs.game_over and not gs.won:
                shake_sys.shake(0.7)
                sound.play("shake")
            if gs.won:
                sound.play("win")
    elif k == pygame.K_r:
        start_game(mode=gs.mode, size=gs.size,
                target_tile=gs.target_tile, time_budget=gs.time_budget)
    elif k == pygame.K_u and not gs.game_over:
        gs.pop_undo()
        sound.play("undo")
    elif k == pygame.K_s and not gs.game_over:
        open_save_slots("save", SCREEN_GAME)
    elif k == pygame.K_l:
        open_save_slots("load", SCREEN_GAME)
    elif pygame.K_3 <= k <= pygame.K_6 and not gs.game_over:
        start_game(mode=gs.mode, size=k - pygame.K_0,
                target_tile=gs.target_tile, time_budget=gs.time_budget)
def handle_save_slot_event(event):
    global current_screen, gs, paused
    result = save_slot_screen.handle_event(event)
    if result is None:
        return
    if result == "back":
        current_screen = _save_slot_origin
        return
    if isinstance(result, tuple):
        action, slot = result
        if action == "save" and gs is not None:
            gs.save(slot)
            save_slot_screen.open("save")   # refresh slot display
        elif action == "load":
            new_gs = GameState()
            if new_gs.load(slot):
                gs = new_gs
                particle_sys.clear()
                paused = False
                current_screen = SCREEN_GAME
        elif action == "delete":
            save_slot_screen.open(save_slot_screen.mode)   # refresh


#  Main loop
def main():
    global current_screen
    while True:
        dt = CLOCK.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        # events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if handle_global_key(event):
                continue
            if current_screen == SCREEN_MENU:
                handle_menu_event(event)
            elif current_screen == SCREEN_GAME:
                handle_game_event(event)
            elif current_screen == SCREEN_LEADERBOARD:
                if leader_screen.handle_event(event) == "back":
                    current_screen = SCREEN_MENU
            elif current_screen == SCREEN_STATS:
                if stats_screen.handle_event(event) == "back":
                    current_screen = SCREEN_MENU
            elif current_screen == SCREEN_SAVE_SLOT:
                handle_save_slot_event(event)
        # update
        BG.update(mouse_pos)
        if current_screen == SCREEN_MENU:
            menu_screen.update()
        elif current_screen == SCREEN_GAME and gs:
            if not paused:
                gs.tick_animations(dt)
                particle_sys.update()
            shake_sys.update()
        elif current_screen == SCREEN_LEADERBOARD:
            leader_screen.update()
        elif current_screen == SCREEN_STATS:
            stats_screen.update()
        elif current_screen == SCREEN_SAVE_SLOT:
            save_slot_screen.update()
        # draw panel content
        th = theme_mod.get()
        if current_screen == SCREEN_MENU:
            menu_screen.draw()
        elif current_screen == SCREEN_GAME and gs:
            PANEL.fill(th["bg"])
            draw_hud(PANEL, gs, sound.is_enabled(), paused)
            draw_board(PANEL, gs)
            draw_score_popups(PANEL, gs)
            particle_sys.draw(PANEL)
            if gs.game_over and gs.won:
                draw_win(PANEL, gs)
            elif gs.game_over:
                draw_game_over(PANEL, gs)
            elif paused:
                draw_pause(PANEL)
        elif current_screen == SCREEN_LEADERBOARD:
            leader_screen.draw()
        elif current_screen == SCREEN_STATS:
            stats_screen.draw(load_stats())
        elif current_screen == SCREEN_SAVE_SLOT:
            save_slot_screen.draw()
        # blit panel to display (with shake if in-game)
        ox, oy = (shake_sys.update() if current_screen == SCREEN_GAME else (0, 0))
        _blit_panel(ox, oy)
        pygame.display.flip()


if __name__ == "__main__":
    main()