# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring

import pygame
from constants import WIN_W, WIN_H, MODE_CLASSIC, MODE_TARGET, MODE_TIME_ATTACK
from utils.drawing import draw_rounded_rect, font, blit_centered, Button, panel_mouse_pos
import utils.theme as theme
import systems.sound as sound
from data.persistence import load_leaderboard_by_mode

# Tab definitions  (label, mode_filter)
TABS = [
    ("All",         None),
    ("Classic",     MODE_CLASSIC),
    ("Target",      MODE_TARGET),
    ("Time Attack", MODE_TIME_ATTACK),
]
TAB_COLORS = {
    None:             (140, 140, 160),
    MODE_CLASSIC:     (100, 160, 220),
    MODE_TARGET:      (80,  200, 120),
    MODE_TIME_ATTACK: (220, 140,  80),
}

# Layout
TAB_Y       = 118
TAB_H       = 34
TAB_RADIUS  = 8
CONTENT_TOP = 168   # where rows start

# Column layout — no "Mode" column when filtered; "Extra" becomes "Time" for Target
COL_RANK  = 36
COL_SCORE = 100
COL_EXTRA = 290
COL_DATE  = 400


class LeaderboardScreen:
    def __init__(self, surface: pygame.Surface):
        self.surface       = surface
        self._active_tab   = 0          # index into TABS
        self._tab_rects: list[pygame.Rect] = []
        self._back = Button(
            pygame.Rect(WIN_W//2 - 110, WIN_H - 66, 220, 46),
            "← Back", font_name="menu_med",
        )
        self._build_tabs()
    def _build_tabs(self):
        """Distribute tab rects evenly across the panel width."""
        n       = len(TABS)
        pad     = 30
        total_w = WIN_W - pad * 2
        gap     = 8
        tw      = (total_w - gap * (n - 1)) // n
        self._tab_rects = []
        for i in range(n):
            x = pad + i * (tw + gap)
            self._tab_rects.append(pygame.Rect(x, TAB_Y, tw, TAB_H))

    # events
    def handle_event(self, event) -> str | None:
        if self._back.is_clicked(event):
            sound.play("click")
            return "back"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            import constants as C
            px = event.pos[0] - C.PANEL_OX
            py = event.pos[1] - C.PANEL_OY
            for i, r in enumerate(self._tab_rects):
                if r.collidepoint(px, py):
                    if i != self._active_tab:
                        self._active_tab = i
                        sound.play("click")
                    break
        return None
    def update(self):
        self._back.update(panel_mouse_pos())

    # draw
    def draw(self, _entries_unused=None):
        th       = theme.get()
        srf      = self.surface
        srf.fill(th["bg"])
        # header
        hdr = font("over").render("Leaderboard", True, th["accent"])
        blit_centered(srf, hdr, WIN_W//2, 62)
        # tab bar
        mp = panel_mouse_pos()
        for i, (label, mode_filter) in enumerate(TABS):
            rect      = self._tab_rects[i]
            active    = i == self._active_tab
            hovered   = rect.collidepoint(mp) and not active
            tab_color = TAB_COLORS[mode_filter]
            if active:
                bg = tab_color
            elif hovered:
                bg = tuple(min(255, c + 30) for c in
                        (TAB_COLORS[mode_filter] if theme.name() == "dark"
                            else (160, 155, 145)))
            else:
                bg = (50, 52, 68) if theme.name() == "dark" else (200, 194, 182)
            draw_rounded_rect(srf, bg, rect, TAB_RADIUS)
            fg = (255, 255, 255) if active else th["lbl_text"]
            t  = font("tab").render(label, True, fg)
            srf.blit(t, t.get_rect(center=rect.center))

        # divider below tabs
        pygame.draw.line(srf, th["divider"],
                        (30, CONTENT_TOP - 10), (WIN_W - 30, CONTENT_TOP - 10), 1)

        # ── load entries for active tab
        _, mode_filter = TABS[self._active_tab]
        entries = load_leaderboard_by_mode(mode_filter)

        # ── column headers
        is_target = mode_filter == MODE_TARGET
        extra_hdr = "Time" if is_target else "Extra"
        headers = [
            (COL_RANK,  "#"),
            (COL_SCORE, "Score"),
            (COL_EXTRA, extra_hdr),
            (COL_DATE,  "Date"),
        ]
        for x, h in headers:
            lbl = font("hint").render(h, True, th["lbl_text"])
            srf.blit(lbl, (x, CONTENT_TOP))
        pygame.draw.line(srf, th["divider"],
                        (30, CONTENT_TOP + 18), (WIN_W - 30, CONTENT_TOP + 18), 1)

        # rows
        if not entries:
            msg = font("label").render(
                "No scores yet for this mode — play a game!",
                True, th["hint_text"],
            )
            blit_centered(srf, msg, WIN_W//2, CONTENT_TOP + 130)
        else:
            row_h = 54
            for i, e in enumerate(entries):
                ry  = CONTENT_TOP + 26 + i * row_h
                row = pygame.Rect(28, ry - 4, WIN_W - 56, row_h - 6)
                row_bg = (48, 50, 68) if theme.name() == "dark" else (212, 205, 193)
                draw_rounded_rect(srf, row_bg, row, 8)

                # rank badge
                badge = pygame.Rect(COL_RANK, ry, 26, 26)
                badge_colors = [
                    (212, 175,  55),   # gold
                    (180, 180, 185),   # silver
                    (180, 115,  65),   # bronze
                ]
                badge_col = badge_colors[i] if i < 3 else (80, 80, 100)
                draw_rounded_rect(srf, badge_col, badge, 6)
                num = font("hint").render(str(i+1), True, (30, 30, 30))
                srf.blit(num, num.get_rect(center=badge.center))

                # score
                sc = font("hud").render(f"{e['score']:,}", True, th["hud_text"])
                srf.blit(sc, (COL_SCORE, ry + 2))

                # extra / time — show mode pill when "All" tab active
                if mode_filter is None:
                    # show mini mode pill instead of extra
                    pill_labels = {
                        MODE_CLASSIC:     ("Classic",  (80, 130, 200)),
                        MODE_TARGET:      ("Target",   (70, 180, 100)),
                        MODE_TIME_ATTACK: ("TimeAtk",  (200, 120, 60)),
                    }
                    p_label, p_col = pill_labels.get(
                        e.get("mode", ""), ("?", (100, 100, 100))
                    )
                    pill = pygame.Rect(COL_EXTRA, ry + 4, 66, 20)
                    draw_rounded_rect(srf, p_col, pill, 6)
                    pt = font("hint").render(p_label, True, (255, 255, 255))
                    srf.blit(pt, pt.get_rect(center=pill.center))
                else:
                    ex = e.get("extra", "") or "—"
                    ex_surf = font("label").render(ex, True, th["lbl_text"])
                    srf.blit(ex_surf, (COL_EXTRA, ry + 2))

                # date — now has plenty of room
                date_str  = e.get("date", "")
                date_surf = font("label").render(date_str, True, th["lbl_text"])
                srf.blit(date_surf, (COL_DATE, ry + 2))

        # back button + footer
        self._back.draw(srf, th)
        ver = font("hint").render("2048 Enhanced Edition  v2.0", True, th["hint_text"])
        srf.blit(ver, (WIN_W//2 - ver.get_width()//2, WIN_H - 20))