import sys
import pygame
from pygame.locals import QUIT, KEYDOWN

# ── bootstrap pygame before any other local import that uses fonts
pygame.init()

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

# ── display setup
SURFACE = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("2048")
CLOCK = pygame.time.Clock()

init_fonts()
sound.init()


#  App state
SCREEN_MENU        = "menu"
SCREEN_GAME        = "game"
SCREEN_LEADERBOARD = "leaderboard"
SCREEN_STATS       = "stats"

current_screen = SCREEN_MENU
gs             = None
paused         = False

particle_sys   = particles.ParticleSystem()
shake_sys      = screenshake.ScreenShake()

menu_screen   = MenuScreen(SURFACE)
leader_screen = LeaderboardScreen(SURFACE)
stats_screen  = StatsScreen(SURFACE)


# ─────────────────────────────────────────────────────────────────────────── #
#  Game helpers
# ─────────────────────────────────────────────────────────────────────────── #

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


def load_game():
    global gs, paused, current_screen
    gs = GameState()
    if gs.load():
        paused = False
        particle_sys.clear()
        current_screen = SCREEN_GAME
    else:
        # nothing to load – stay on menu
        pass


# ─────────────────────────────────────────────────────────────────────────── #
#  Event handlers per screen
# ─────────────────────────────────────────────────────────────────────────── #

def handle_menu_event(event):
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
        global current_screen
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
            # particles + sound for merges
            for (r, c, val) in gs.merge_events:
                cx, cy = tile_center(r, c, gs.size)
                particle_sys.burst(cx, cy, val)
                if val >= 512:
                    sound.play("merge")
            # screen shake on game over
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

    elif k == pygame.K_t:
        theme_mod.toggle()

    elif k == pygame.K_m:
        sound.toggle()

    elif pygame.K_3 <= k <= pygame.K_6 and not gs.game_over:
        start_game(mode=gs.mode, size=k - pygame.K_0,
                   target_tile=gs.target_tile, time_budget=gs.time_budget)


# ─────────────────────────────────────────────────────────────────────────── #
#  Main loop
# ─────────────────────────────────────────────────────────────────────────── #

def main():
    global current_screen

    running = True
    while running:
        dt = CLOCK.tick(60) / 1000.0   # seconds

        # ── events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            if current_screen == SCREEN_MENU:
                handle_menu_event(event)
            elif current_screen == SCREEN_GAME:
                handle_game_event(event)
            elif current_screen == SCREEN_LEADERBOARD:
                result = leader_screen.handle_event(event)
                if result == "back":
                    current_screen = SCREEN_MENU
            elif current_screen == SCREEN_STATS:
                result = stats_screen.handle_event(event)
                if result == "back":
                    current_screen = SCREEN_MENU

        # ── update
        if current_screen == SCREEN_MENU:
            menu_screen.update()

        elif current_screen == SCREEN_GAME and gs:
            if not paused:
                gs.tick_animations(dt)
                particle_sys.update()
            shake_sys.update()   # always update shake (drains naturally)

        elif current_screen == SCREEN_LEADERBOARD:
            leader_screen.update()

        elif current_screen == SCREEN_STATS:
            stats_screen.update()

        # ── draw
        ox, oy = shake_sys.update() if current_screen == SCREEN_GAME else (0, 0)

        if current_screen == SCREEN_MENU:
            menu_screen.draw()

        elif current_screen == SCREEN_GAME and gs:
            th = theme_mod.get()
            SURFACE.fill(th["bg"])
            # apply shake offset by drawing onto a sub-surface
            if ox or oy:
                tmp = pygame.Surface((WIN_W, WIN_H))
                tmp.fill(th["bg"])
                draw_hud(tmp, gs, sound.is_enabled(), paused)
                draw_board(tmp, gs)
                draw_score_popups(tmp, gs)
                particle_sys.draw(tmp)
                SURFACE.blit(tmp, (ox, oy))
            else:
                draw_hud(SURFACE, gs, sound.is_enabled(), paused)
                draw_board(SURFACE, gs)
                draw_score_popups(SURFACE, gs)
                particle_sys.draw(SURFACE)

            if gs.game_over and gs.won:
                draw_win(SURFACE, gs)
            elif gs.game_over:
                draw_game_over(SURFACE, gs)
            elif paused:
                draw_pause(SURFACE)

        elif current_screen == SCREEN_LEADERBOARD:
            leader_screen.draw(load_leaderboard())

        elif current_screen == SCREEN_STATS:
            stats_screen.draw(load_stats())

        pygame.display.flip()


if __name__ == "__main__":
    main()