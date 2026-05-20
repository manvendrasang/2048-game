import pygame
from constants import WIN_W, WIN_H, MODE_CLASSIC, MODE_TARGET, MODE_TIME_ATTACK
from utils.drawing import Button, draw_rounded_rect, font, blit_centered, panel_mouse_pos
import utils.theme as theme
import systems.sound as sound


#  shared button factory  

def _make_buttons(items, cx, start_y, w=260, h=52, gap=12):
    btns = []
    for label, action in items:
        r = pygame.Rect(cx - w//2, start_y, w, h)
        btns.append((Button(r, label, font_name="menu_med"), action))
        start_y += h + gap
    return btns


#  MenuScreen  

class MenuScreen:
    """
    Possible return values from handle_event():
        MODE_CLASSIC / MODE_TARGET / MODE_TIME_ATTACK  → start game
        "load"         → load saved game
        "leaderboard"  → show leaderboard
        "stats"        → show stats
        "quit"         → exit
        None           → handled internally (sub-menu navigation)
    """

    # sub-screen IDs
    _SUB_NONE     = None
    _SUB_MODES    = "modes"
    _SUB_OPTIONS  = "options"
    _SUB_CONTROLS = "controls"

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self._sub    = self._SUB_NONE
        self._scroll = 0          # for controls tab scrolling (future-proof)
        self._build_all()

    #  build  

    def _build_all(self):
        cx = WIN_W // 2

        #  main menu
        self._main_btns = _make_buttons([
            ("New Game",    "modes"),
            ("Load Game",   "load"),
            ("Leaderboard", "leaderboard"),
            ("Stats",       "stats"),
            ("Options",     "options"),
            ("Quit",        "quit"),
        ], cx, 240, w=280, h=50, gap=12)

        #  mode selector  (extra gap so desc text has room)
        self._mode_btns = _make_buttons([
            ("Classic Mode",      MODE_CLASSIC),
            ("Target Mode",       MODE_TARGET),
            ("Time Attack Mode",  MODE_TIME_ATTACK),
            ("← Back",            "back"),
        ], cx, 190, w=280, h=50, gap=38)

        #  options menu (toggle rows built dynamically in draw)
        self._opt_btns = _make_buttons([
            ("Controls",  "controls"),
            ("← Back",    "back"),
        ], cx, 460, w=240, h=46, gap=10)

        # toggle rects (drawn manually in options screen)
        tw, th_h = 200, 48
        self._toggle_sound_rect = pygame.Rect(cx - tw//2, 230, tw, th_h)
        self._toggle_theme_rect = pygame.Rect(cx - tw//2, 295, tw, th_h)

        # controls back button
        self._ctrl_back_btn = Button(
            pygame.Rect(cx - 120, WIN_H - 70, 240, 46),
            "← Back", font_name="menu_med"
        )

    #  events  

    def handle_event(self, event) -> str | None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        # translate display coords → panel coords
        import constants as C
        pos = (event.pos[0] - C.PANEL_OX, event.pos[1] - C.PANEL_OY)

        if self._sub == self._SUB_NONE:
            for btn, action in self._main_btns:
                if btn.rect.collidepoint(pos):
                    sound.play("click")
                    if action in ("modes", "options"):
                        self._sub = action
                        return None
                    return action

        elif self._sub == self._SUB_MODES:
            for btn, action in self._mode_btns:
                if btn.rect.collidepoint(pos):
                    sound.play("click")
                    if action == "back":
                        self._sub = self._SUB_NONE
                        return None
                    return action

        elif self._sub == self._SUB_OPTIONS:
            # toggles
            if self._toggle_sound_rect.collidepoint(pos):
                sound.toggle()
                sound.play("click")
                return None
            if self._toggle_theme_rect.collidepoint(pos):
                theme.toggle()
                sound.play("click")
                return None
            for btn, action in self._opt_btns:
                if btn.rect.collidepoint(pos):
                    sound.play("click")
                    if action == "controls":
                        self._sub = self._SUB_CONTROLS
                    elif action == "back":
                        self._sub = self._SUB_NONE
                    return None

        elif self._sub == self._SUB_CONTROLS:
            if self._ctrl_back_btn.is_clicked(event):
                sound.play("click")
                self._sub = self._SUB_OPTIONS
                return None

        return None

    #  update  

    def update(self):
        mp = panel_mouse_pos()
        if self._sub == self._SUB_NONE:
            for btn, _ in self._main_btns: btn.update(mp)
        elif self._sub == self._SUB_MODES:
            for btn, _ in self._mode_btns: btn.update(mp)
        elif self._sub == self._SUB_OPTIONS:
            for btn, _ in self._opt_btns: btn.update(mp)
        elif self._sub == self._SUB_CONTROLS:
            self._ctrl_back_btn.update(mp)

    #  draw  

    def draw(self):
        th  = theme.get()
        srf = self.surface
        srf.fill(th["bg"])

        if self._sub == self._SUB_NONE:
            self._draw_main(srf, th)
        elif self._sub == self._SUB_MODES:
            self._draw_modes(srf, th)
        elif self._sub == self._SUB_OPTIONS:
            self._draw_options(srf, th)
        elif self._sub == self._SUB_CONTROLS:
            self._draw_controls(srf, th)

        # footer on all sub-screens
        ver = font("hint").render("2048 Enhanced Edition  v2.0", True, th["hint_text"])
        srf.blit(ver, (WIN_W//2 - ver.get_width()//2, WIN_H - 20))

    # sub-draw helpers

    def _draw_header(self, srf, th, subtitle=""):
        title = font("over").render("2048", True, th["accent"])
        blit_centered(srf, title, WIN_W//2, 90)
        if subtitle:
            s = font("menu_med").render(subtitle, True, th["hud_text"])
            blit_centered(srf, s, WIN_W//2, 148)

    def _draw_main(self, srf, th):
        self._draw_header(srf, th)
        tagline = font("small").render(
            "Classic  •  Target Mode  •  Time Attack", True, th["lbl_text"]
        )
        blit_centered(srf, tagline, WIN_W//2, 142)
        for btn, _ in self._main_btns:
            btn.draw(srf, th)

    def _draw_modes(self, srf, th):
        self._draw_header(srf, th, "Select Game Mode")

        descs = [
            "Infinite play — no time limit",
            "Race to reach 2048 — fastest time wins",
            "Score as high as you can before time runs out",
            "",
        ]
        for (btn, _), desc in zip(self._mode_btns, descs):
            btn.draw(srf, th)
            if desc:
                d = font("hint").render(desc, True, th["hint_text"])
                # render below the button, vertically centred in the gap
                srf.blit(d, (btn.rect.left + 6, btn.rect.bottom + 6))

    def _draw_options(self, srf, th):
        self._draw_header(srf, th, "Options")

        #  Sound toggle
        self._draw_toggle(
            srf, th,
            self._toggle_sound_rect,
            label="Sound",
            state=sound.is_enabled(),
            on_text="ON",
            off_text="OFF",
        )

        #  Theme toggle
        is_dark = theme.name() == "dark"
        self._draw_toggle(
            srf, th,
            self._toggle_theme_rect,
            label="Theme",
            state=is_dark,
            on_text="Dark",
            off_text="Light",
        )

        pygame.draw.line(
            srf, th["divider"],
            (WIN_W//2 - 130, 360), (WIN_W//2 + 130, 360), 1
        )

        for btn, _ in self._opt_btns:
            btn.draw(srf, th)

    def _draw_toggle(self, srf, th, rect, label, state, on_text, off_text):
        """Draw a labelled toggle row."""
        # background card
        card_col = (50, 50, 70) if theme.name() == "dark" else (210, 200, 190)
        draw_rounded_rect(srf, card_col, rect, 10)

        lbl = font("label").render(label, True, th["hud_text"])
        srf.blit(lbl, (rect.left + 16, rect.centery - lbl.get_height()//2))

        # pill button on the right
        pill_w, pill_h = 80, 32
        pill_x = rect.right - pill_w - 12
        pill_y = rect.centery - pill_h//2
        pill   = pygame.Rect(pill_x, pill_y, pill_w, pill_h)
        pill_col = th["toggle_on"] if state else th["toggle_off"]
        draw_rounded_rect(srf, pill_col, pill, 16)
        val_txt = on_text if state else off_text
        v = font("small").render(val_txt, True, (255, 255, 255))
        srf.blit(v, v.get_rect(center=pill.center))

    def _draw_controls(self, srf, th):
        self._draw_header(srf, th, "Controls")

        controls = [
            ("Arrow Keys",    "Move tiles"),
            ("U",             "Undo last move"),
            ("R",             "Restart game"),
            ("S",             "Save game"),
            ("P",             "Pause / Resume"),
            ("T",             "Toggle Dark / Light theme"),
            ("M",             "Mute / Unmute sound"),
            ("3 – 6",         "Change board size"),
            ("ESC",           "Return to main menu"),
        ]

        row_h  = 38
        left   = WIN_W//2 - 230
        right  = WIN_W//2 + 10
        start_y = 170

        # column headers
        key_hdr = font("label").render("Key", True, th["accent"])
        act_hdr = font("label").render("Action", True, th["accent"])
        srf.blit(key_hdr, (left, start_y))
        srf.blit(act_hdr, (right, start_y))
        pygame.draw.line(srf, th["divider"],
                        (left, start_y + 22), (WIN_W - left, start_y + 22), 1)

        for i, (key, action) in enumerate(controls):
            y   = start_y + 30 + i * row_h
            # alternating row tint
            if i % 2 == 0:
                row_rect = pygame.Rect(left - 8, y - 4, WIN_W - 2*(left-8), row_h - 4)
                bg = (40, 40, 55) if theme.name() == "dark" else (230, 222, 210)
                draw_rounded_rect(srf, bg, row_rect, 6)

            k_surf = font("small").render(f"[ {key} ]", True, th["accent"])
            a_surf = font("small").render(action,       True, th["hud_text"])
            srf.blit(k_surf, (left, y))
            srf.blit(a_surf, (right, y))

        self._ctrl_back_btn.draw(srf, th)