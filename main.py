# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring, no-name-in-module, no-member, unused-import, invalid-name
# pylint: disable=global-statement, unnecessary-dunder-call, redefined-outer-name, global-variable-not-assigned, line-too-long

# main.py
# Entry point. Fullscreen display with centred panel.
# Wires: menu, game, leaderboard, stats, save-slot, challenge picker,
#        challenge result, background music, bg particles.

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
    MODE_CLASSIC, MODE_TARGET, MODE_TIME_ATTACK, MODE_CHALLENGE, MODE_DAILY,
    TARGET_TILE_DEFAULT, TIME_ATTACK_SECONDS,
)
from utils.drawing      import init_fonts
from utils              import theme as theme_mod
from game_state         import GameState
from systems            import sound, particles, screenshake
from systems            import music
from systems.haptic     import HapticFeedback
from systems.score_anim import ScoreAnimator
from systems.bg_particles import BgParticleSystem
from screens.menu       import MenuScreen
from screens.game_renderer import (
    draw_board, draw_hud, draw_score_popups,
    draw_game_over, draw_win, draw_pause, tile_center,
)
from screens.leaderboard         import LeaderboardScreen
from screens.profile_screen      import ProfileScreen
from screens.save_slot_screen    import SaveSlotScreen
from screens.challenge_screen    import ChallengeScreen
from screens.challenge_result_screen import ChallengeResultScreen
from screens.daily_result_screen import DailyResultScreen
from data.persistence  import (
    load_stats, migrate_legacy_save, get_today_result,
    save_daily_result, check_and_unlock_achievements,
)
from data.challenges   import get_challenge
from data.daily_puzzle import generate_daily_board

CLOCK = pygame.time.Clock()
init_fonts()

# Load persisted settings before initialising sound/music/theme
from data.settings import load as load_settings, apply_to_systems, set as set_setting, get as get_setting
load_settings()
apply_to_systems()

sound.init()
music.init()
migrate_legacy_save()

# Panel surface
PANEL   = pygame.Surface((WIN_W, WIN_H))
PANEL_W = WIN_W + 20
PANEL_H = WIN_H + 20
BORDER_OX = C.PANEL_OX - 10
BORDER_OY = C.PANEL_OY - 10

BG = BgParticleSystem(info.current_w, info.current_h)

# Screen IDs
S_MENU         = "menu"
S_GAME         = "game"
S_LEADER       = "leaderboard"
S_PROFILE      = "profile"
S_SAVE_SLOT    = "save_slot"
S_CHALLENGES   = "challenges"
S_CH_RESULT    = "ch_result"
S_DAILY_RESULT = "daily_result"

current_screen     = S_MENU
gs                 = None
paused             = False
_save_slot_origin  = S_GAME
_active_challenge  = None   # challenge dict for current/last challenge

particle_sys = particles.ParticleSystem()
shake_sys    = screenshake.ScreenShake()
haptic       = HapticFeedback()
score_anim   = ScoreAnimator()

menu_screen         = MenuScreen(PANEL)
leader_screen       = LeaderboardScreen(PANEL)
profile_screen      = ProfileScreen(PANEL)
save_slot_screen    = SaveSlotScreen(PANEL)
challenge_screen    = ChallengeScreen(PANEL)
ch_result_screen    = ChallengeResultScreen(PANEL)
daily_result_screen = DailyResultScreen(PANEL)

# Achievement notification queue — list of newly unlocked IDs shown briefly
_ach_queue: list[str] = []
_ach_timer: float     = 0.0
ACH_DISPLAY_SECS      = 3.0

DIRECTION_MAP = {
    pygame.K_UP:    "up",
    pygame.K_DOWN:  "down",
    pygame.K_LEFT:  "left",
    pygame.K_RIGHT: "right",
}


#  Panel blit

def _blit_panel(ox: int = 0, oy: int = 0):
    th = theme_mod.get()
    DISPLAY.fill(th.get("outer_bg", (0, 0, 0)))
    BG.draw(DISPLAY)

    # shadow
    shadow = pygame.Surface((PANEL_W + 12, PANEL_H + 12), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 80),
                    shadow.get_rect(), border_radius=22)
    DISPLAY.blit(shadow, (BORDER_OX + ox + 4, BORDER_OY + oy + 6))

    # fill
    fill_rect = pygame.Rect(BORDER_OX + ox, BORDER_OY + oy, PANEL_W, PANEL_H)
    pygame.draw.rect(DISPLAY, th["bg"], fill_rect, border_radius=20)

    # content
    DISPLAY.blit(PANEL, (C.PANEL_OX + ox, C.PANEL_OY + oy))

    # border
    border_col = th.get("accent", (237, 194, 46))
    pygame.draw.rect(DISPLAY, border_col, fill_rect, width=3, border_radius=20)

    # inner glow
    inner = fill_rect.inflate(-6, -6)
    glow  = tuple(min(255, c + 40) for c in border_col[:3])
    pygame.draw.rect(DISPLAY, glow, inner, width=1, border_radius=18)


#  Game / challenge starters

def start_game(mode=MODE_CLASSIC, size=DEFAULT_BOARD,
            target_tile=TARGET_TILE_DEFAULT,
            time_budget=TIME_ATTACK_SECONDS,
            challenge=None):
    global gs, paused, current_screen, _active_challenge
    _active_challenge = challenge
    gs = GameState(size=size, mode=mode,
                target_tile=target_tile,
                time_budget=time_budget,
                challenge=challenge)
    gs.reset(challenge=challenge)
    particle_sys.clear()
    haptic.__init__()
    score_anim.snap(0)
    paused = False
    current_screen = S_GAME
    # music context
    if mode == MODE_CHALLENGE:
        music.set_context("challenge")
    elif mode == MODE_TIME_ATTACK:
        music.set_context("intense")
    else:
        music.set_context("game")


def start_challenge(cid: int):
    ch = get_challenge(cid)
    if ch is None:
        return
    start_game(
        mode=MODE_CHALLENGE,
        size=ch["board_size"],
        challenge=ch,
    )


def start_daily():
    """Start today's daily puzzle, or show result if already played."""
    global gs, paused, current_screen
    today = get_today_result()
    if today is not None:
        daily_result_screen.open(today, already_played=True)
        current_screen = S_DAILY_RESULT
        return
    board = generate_daily_board(size=4)
    gs    = GameState(size=4, mode=MODE_DAILY)
    gs.reset()
    gs.matrix     = board
    gs.tile_scales = [[1.0]*4 for _ in range(4)]
    particle_sys.clear()
    paused         = False
    current_screen = S_GAME
    music.set_context("game")


def open_save_slots(mode: str, origin: str):
    global current_screen, _save_slot_origin
    _save_slot_origin = origin
    save_slot_screen.open(mode)
    current_screen = S_SAVE_SLOT


#  Global keys (T / M / N for music)

def handle_global_key(event) -> bool:
    if event.type != KEYDOWN:
        return False
    if event.key == pygame.K_t:
        new_theme = theme_mod.toggle()
        set_setting("theme", new_theme)
        return True
    if event.key == pygame.K_m:
        enabled = sound.toggle()
        set_setting("sfx_enabled", enabled)
        return True
    if event.key == pygame.K_n:
        enabled = music.toggle()
        set_setting("music_enabled", enabled)
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
    elif result == "daily":
        start_daily()
    elif result == "challenges":
        current_screen = S_CHALLENGES
    elif result == "load":
        open_save_slots("load", S_MENU)
    elif result == "leaderboard":
        current_screen = S_LEADER
    elif result == "profile":
        current_screen = S_PROFILE
    elif result == "quit":
        pygame.quit()
        sys.exit()


def handle_game_event(event):
    global paused, current_screen
    if event.type != KEYDOWN:
        return
    k = event.key

    if k == pygame.K_ESCAPE:
        current_screen = S_MENU
        music.set_context("menu")
        return
    if k == pygame.K_p:
        paused = not paused
        return
    if paused:
        return

    if k in DIRECTION_MAP and not gs.game_over:
        if gs.slide_anim.animating:
            return
        gs.push_undo()
        moved = gs.move(DIRECTION_MAP[k])
        if moved:
            sound.play("move")
            for (r, c, val) in gs.merge_events:
                cx, cy = tile_center(r, c, gs.size)
                particle_sys.burst(cx, cy, val)
                if val >= 512:
                    sound.play("merge")
                haptic.merge_flash()
            if gs.game_over and not gs.won:
                shake_sys.shake(0.7)
                sound.play("shake")
            if gs.won:
                sound.play("win")

            # Check achievements after every move — catches score/tile milestones
            # immediately so they are saved to disk even if window closes soon after
            newly = check_and_unlock_achievements()
            if newly:
                _ach_queue.extend(newly)

            if gs.game_over and gs.mode == MODE_CHALLENGE:
                _show_challenge_result()

            # Daily: trigger result screen as soon as daily_finished is set
            if getattr(gs, "daily_finished", False):
                _show_daily_result()
        else:
            haptic.invalid_move()

    elif k == pygame.K_r:
        if gs.mode == MODE_CHALLENGE and _active_challenge:
            start_challenge(_active_challenge["id"])
        else:
            start_game(mode=gs.mode, size=gs.size,
                    target_tile=gs.target_tile,
                    time_budget=gs.time_budget)
    elif k == pygame.K_u and not gs.game_over:
        if gs.mode != MODE_DAILY:
            if gs.can_undo:
                gs.pop_undo()
                sound.play("undo")
            else:
                haptic.invalid_move()   # red flash when no tokens left
    elif k == pygame.K_s and not gs.game_over and gs.mode not in (MODE_CHALLENGE, MODE_DAILY):
        open_save_slots("save", S_GAME)
    elif k == pygame.K_l and gs.mode not in (MODE_CHALLENGE, MODE_DAILY):
        open_save_slots("load", S_GAME)
    elif pygame.K_3 <= k <= pygame.K_6 and not gs.game_over \
            and gs.mode not in (MODE_CHALLENGE, MODE_DAILY):
        start_game(mode=gs.mode, size=k - pygame.K_0,
                target_tile=gs.target_tile,
                time_budget=gs.time_budget)


def _show_challenge_result():
    global current_screen
    ch = gs.challenge
    ch_result_screen.open(
        won=gs.won,
        stars=getattr(gs, "challenge_stars", 0),
        score=gs.score,
        moves=gs.moves,
        ch_name=ch["name"] if ch else "",
        par_moves=ch["par_moves"] if ch else 0,
    )
    current_screen = S_CH_RESULT


def _show_daily_result():
    global current_screen
    from data.persistence import get_today_result
    result = get_today_result()
    if result:
        daily_result_screen.open(result, already_played=False)
        current_screen = S_DAILY_RESULT


def handle_daily_result_event(event):
    global current_screen
    result = daily_result_screen.handle_event(event)
    if result == "menu":
        current_screen = S_MENU
        music.set_context("menu")


def handle_challenge_result_event(event):
    global current_screen
    result = ch_result_screen.handle_event(event)
    if result == "retry" and _active_challenge:
        start_challenge(_active_challenge["id"])
    elif result == "challenges":
        current_screen = S_CHALLENGES
        music.set_context("menu")
    elif result == "menu":
        current_screen = S_MENU
        music.set_context("menu")


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
            save_slot_screen.open("save")
        elif action == "load":
            new_gs = GameState()
            if new_gs.load(slot):
                gs = new_gs
                particle_sys.clear()
                score_anim.snap(gs.score)
                paused = False
                current_screen = S_GAME
                music.set_context("game")
        elif action == "delete":
            save_slot_screen.open(save_slot_screen.mode)


#  Main loop

def _draw_ach_toast(dt: float):
    """Draw an achievement unlock notification toast over everything."""
    global _ach_timer, _ach_queue
    if not _ach_queue:
        return
    _ach_timer += dt
    if _ach_timer >= ACH_DISPLAY_SECS:
        _ach_queue.pop(0)
        _ach_timer = 0.0
        return

    from data.achievements import ALL_ACHIEVEMENTS
    from utils.drawing import font as dfont
    ach_id = _ach_queue[0]
    ach    = next((a for a in ALL_ACHIEVEMENTS if a["id"] == ach_id), None)
    if not ach:
        return

    fade   = min(1.0, min(_ach_timer, ACH_DISPLAY_SECS - _ach_timer) / 0.4)
    alpha  = int(fade * 230)
    tw, th2 = 320, 64
    tx     = C.PANEL_OX + C.WIN_W // 2 - tw // 2
    ty     = C.PANEL_OY + 30

    toast  = pygame.Surface((tw, th2), pygame.SRCALPHA)
    pygame.draw.rect(toast, (30, 30, 40, alpha), toast.get_rect(), border_radius=14)
    pygame.draw.rect(toast, (237, 194, 46, alpha), toast.get_rect(),
                    width=2, border_radius=14)

    icon_s = dfont("menu_med").render(ach["icon"], True, (255, 255, 255))
    icon_s.set_alpha(alpha)
    toast.blit(icon_s, (14, th2 // 2 - icon_s.get_height() // 2))

    tag = dfont("hint").render("Achievement Unlocked!", True, (237, 194, 46))
    tag.set_alpha(alpha)
    toast.blit(tag, (52, 10))

    name_s = dfont("label").render(ach["name"], True, (220, 220, 230))
    name_s.set_alpha(alpha)
    toast.blit(name_s, (52, 32))

    DISPLAY.blit(toast, (tx, ty))


def main():
    global current_screen
    music.set_context("menu")

    while True:
        dt = CLOCK.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if handle_global_key(event):
                continue
            if current_screen == S_MENU:
                handle_menu_event(event)
            elif current_screen == S_GAME:
                handle_game_event(event)
            elif current_screen == S_LEADER:
                if leader_screen.handle_event(event) == "back":
                    current_screen = S_MENU
            elif current_screen == S_PROFILE:
                if profile_screen.handle_event(event) == "back":
                    current_screen = S_MENU
            elif current_screen == S_SAVE_SLOT:
                handle_save_slot_event(event)
            elif current_screen == S_CHALLENGES:
                result = challenge_screen.handle_event(event)
                if isinstance(result, int):
                    start_challenge(result)
                elif result == "back":
                    current_screen = S_MENU
            elif current_screen == S_CH_RESULT:
                handle_challenge_result_event(event)
            elif current_screen == S_DAILY_RESULT:
                handle_daily_result_event(event)

        # update
        BG.update(mouse_pos)
        music.tick(dt)

        if current_screen == S_MENU:
            menu_screen.update()
        elif current_screen == S_GAME and gs:
            if not paused:
                gs.tick_animations(dt)
                particle_sys.update()
                score_anim.set_target(gs.score)
                score_anim.tick(dt)
            shake_sys.update()
        elif current_screen == S_LEADER:
            leader_screen.update()
        elif current_screen == S_PROFILE:
            profile_screen.update()
        elif current_screen == S_SAVE_SLOT:
            save_slot_screen.update()
        elif current_screen == S_CHALLENGES:
            challenge_screen.update()
        elif current_screen == S_CH_RESULT:
            ch_result_screen.update(dt)
        elif current_screen == S_DAILY_RESULT:
            daily_result_screen.update(dt)

        # draw panel
        th = theme_mod.get()

        if current_screen == S_MENU:
            menu_screen.draw()
        elif current_screen == S_GAME and gs:
            PANEL.fill(th["bg"])
            draw_hud(PANEL, gs, sound.is_enabled(), paused,
                    displayed_score=score_anim.value)
            draw_board(PANEL, gs, haptic)
            draw_score_popups(PANEL, gs)
            particle_sys.draw(PANEL)
            if gs.game_over and gs.won and gs.mode not in (MODE_CHALLENGE, MODE_DAILY):
                draw_win(PANEL, gs)
            elif gs.game_over and gs.mode not in (MODE_CHALLENGE, MODE_DAILY):
                draw_game_over(PANEL, gs)
            elif paused:
                draw_pause(PANEL)
        elif current_screen == S_LEADER:
            leader_screen.draw()
        elif current_screen == S_PROFILE:
            profile_screen.draw()
        elif current_screen == S_SAVE_SLOT:
            save_slot_screen.draw()
        elif current_screen == S_CHALLENGES:
            challenge_screen.draw()
        elif current_screen == S_CH_RESULT:
            ch_result_screen.draw()
        elif current_screen == S_DAILY_RESULT:
            daily_result_screen.draw()

        ox, oy = shake_sys.update() if current_screen == S_GAME else (0, 0)
        _blit_panel(ox, oy)

        _draw_ach_toast(dt)

        pygame.display.flip()


if __name__ == "__main__":
    main()
