import sys
import pygame
from pygame.locals import QUIT, KEYDOWN

pygame.init()

# fullscreen first, then resolve panel offset
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
from utils.drawing      import init_fonts
from utils              import theme as theme_mod
from game_state         import GameState
from systems            import sound, particles, screenshake
from screens.menu       import MenuScreen
from screens.game_renderer import (
    draw_board, draw_hud, draw_score_popups,
    draw_game_over, draw_win, draw_pause, tile_center,
)
from screens.leaderboard import LeaderboardScreen
from screens.stats       import StatsScreen
from data.persistence    import load_leaderboard, load_stats

CLOCK = pygame.time.Clock()
init_fonts()
sound.init()

# panel surface — all game drawing happens here, then blitted to DISPLAY
PANEL = pygame.Surface((WIN_W, WIN_H))



#  Screen IDs

SCREEN_MENU        = "menu"
SCREEN_GAME        = "game"
SCREEN_LEADERBOARD = "leaderboard"
SCREEN_STATS       = "stats"

current_screen = SCREEN_MENU
gs             = None
paused         = False

particle_sys = particles.ParticleSystem()
shake_sys    = screenshake.ScreenShake()

menu_screen   = MenuScreen(PANEL)
leader_screen = LeaderboardScreen(PANEL)
stats_screen  = StatsScreen(PANEL)



#  Helpers


DIRECTION_MAP = {
    pygame.K_UP:    "up",
    pygame.K_DOWN:  "down",
    pygame.K_LEFT:  "left",
    pygame.K_RIGHT: "right",
}


def _blit_panel(ox=0, oy=0):
    """Blit the panel onto the fullscreen display, centred + optional shake."""
    th = theme_mod.get()
    DISPLAY.fill(th.get("outer_bg", (0, 0, 0)))
    DISPLAY.blit(PANEL, (C.PANEL_OX + ox, C.PANEL_OY + oy))
    # subtle border around panel
    pygame.draw.rect(
        DISPLAY, th.get("divider", (60, 60, 80)),
        pygame.Rect(C.PANEL_OX + ox - 1, C.PANEL_OY + oy - 1, WIN_W + 2, WIN_H + 2),
        1,
    )


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


def load_game():
    global gs, paused, current_screen
    gs = GameState()
    if gs.load():
        paused = False
        particle_sys.clear()
        current_screen = SCREEN_GAME



#  Global key handler (T = theme, M = mute — active on every screen)


def handle_global_key(event) -> bool:
    """Returns True if the key was consumed globally."""
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
        load_game()
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
    elif k == pygame.K_s:
        gs.save()
    elif pygame.K_3 <= k <= pygame.K_6 and not gs.game_over:
        start_game(mode=gs.mode, size=k - pygame.K_0,
                   target_tile=gs.target_tile, time_budget=gs.time_budget)



#  Main loop


def main():
    global current_screen

    while True:
        dt = CLOCK.tick(60) / 1000.0

        # events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            # global keys first (T / M) — skip if consumed
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

        # update
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

        # draw to PANEL
        th = theme_mod.get()

        if current_screen == SCREEN_MENU:
            menu_screen.draw()
            _blit_panel()

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

            # screen shake: offset the blit
            ox, oy = shake_sys.update()
            _blit_panel(ox, oy)

        elif current_screen == SCREEN_LEADERBOARD:
            leader_screen.draw(load_leaderboard())
            _blit_panel()

        elif current_screen == SCREEN_STATS:
            stats_screen.draw(load_stats())
            _blit_panel()

        pygame.display.flip()


if __name__ == "__main__":
    main()