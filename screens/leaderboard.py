# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring

import pygame
from constants import WIN_W, WIN_H, MODE_CLASSIC, MODE_TARGET, MODE_TIME_ATTACK, MODE_DAILY
from utils.drawing import draw_rounded_rect, font, blit_centered, Button, panel_mouse_pos
import utils.theme as theme
import systems.sound as sound
from data.persistence import load_leaderboard_by_mode

# Tabs
TABS = [
    ("All",         None),
    ("Classic",     MODE_CLASSIC),
    ("Target",      MODE_TARGET),
    ("Time Attack", MODE_TIME_ATTACK),
    ("Daily",       MODE_DAILY),
]
TAB_COLORS = {
    None:             (120, 120, 145),
    MODE_CLASSIC:     (90,  150, 215),
    MODE_TARGET:      (70,  190, 110),
    MODE_TIME_ATTACK: (215, 130,  65),
    MODE_DAILY:       (150,  90, 210),
}

# Podium row styles  (bg, left-accent-bar, score-text, rank-badge)
PODIUM = [
    # 1st — gold
    {
        "row_dark":   (72,  60,  22),
        "row_light":  (255, 243, 195),
        "bar":        (212, 175,  55),
        "score":      (255, 220,  60),
        "badge_bg":   (212, 175,  55),
        "badge_fg":   (40,  30,   0),
        "label":      "1st",
    },
    # 2nd — silver
    {
        "row_dark":   (52,  55,  68),
        "row_light":  (230, 232, 238),
        "bar":        (180, 182, 192),
        "score":      (210, 215, 225),
        "badge_bg":   (180, 182, 192),
        "badge_fg":   (30,  30,  40),
        "label":      "2nd",
    },
    # 3rd — bronze
    {
        "row_dark":   (60,  42,  25),
        "row_light":  (245, 225, 200),
        "bar":        (175, 110,  55),
        "score":      (220, 155,  80),
        "badge_bg":   (175, 110,  55),
        "badge_fg":   (40,  20,   0),
        "label":      "3rd",
    },
]

# Layout
TAB_Y       = 118
TAB_H       = 34
TAB_RADIUS  = 8
CONTENT_TOP = 168
ROW_H       = 56
ROW_RADIUS  = 10
BAR_W       = 4     # left accent bar width

# Columns  (x positions)
COL_RANK  = 36
COL_SCORE = 88
COL_GRID  = 230     # board-size column  e.g. "4×4"
COL_EXTRA = 296     # mode pill (All tab) or extra info
COL_DATE  = 400

class LeaderboardScreen:
    def __init__(self, surface: pygame.Surface):
        self.surface     = surface
        self._active_tab = 0
        self._tab_rects: list[pygame.Rect] = []
        self._back = Button(
            pygame.Rect(WIN_W//2 - 110, WIN_H - 66, 220, 46),
            "← Back", font_name="menu_med",
        )
        self._build_tabs()
    # tab geometry
    def _build_tabs(self):
        n       = len(TABS)
        pad     = 28
        gap     = 7
        tw      = (WIN_W - pad*2 - gap*(n-1)) // n
        self._tab_rects = [
            pygame.Rect(pad + i*(tw+gap), TAB_Y, tw, TAB_H)
            for i in range(n)
        ]
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
    def draw(self, _=None):
        th  = theme.get()
        srf = self.surface
        srf.fill(th["bg"])
        dark = theme.name() == "dark"
        # header
        hdr = font("over").render("Leaderboard", True, th["accent"])
        blit_centered(srf, hdr, WIN_W//2, 62)
        # tab bar
        mp = panel_mouse_pos()
        for i, (label, mf) in enumerate(TABS):
            rect   = self._tab_rects[i]
            active = i == self._active_tab
            hov    = rect.collidepoint(mp) and not active
            tc     = TAB_COLORS[mf]
            if active:
                bg = tc
            elif hov:
                bg = tuple(min(255, c + 25) for c in tc)
            else:
                bg = (50, 52, 68) if dark else (200, 194, 182)
            draw_rounded_rect(srf, bg, rect, TAB_RADIUS)
            fg = (255, 255, 255) if active else th["lbl_text"]
            t  = font("tab").render(label, True, fg)
            srf.blit(t, t.get_rect(center=rect.center))
        pygame.draw.line(srf, th["divider"],
                        (28, CONTENT_TOP - 10), (WIN_W - 28, CONTENT_TOP - 10), 1)
        # active tab data
        _, mode_filter = TABS[self._active_tab]
        entries = load_leaderboard_by_mode(mode_filter)
        # column headers
        is_target = mode_filter == MODE_TARGET
        extra_hdr = "Time" if is_target else ("Mode" if mode_filter is None else "Extra")
        for x, h in [
            (COL_RANK,  "#"),
            (COL_SCORE, "Score"),
            (COL_GRID,  "Grid"),
            (COL_EXTRA, extra_hdr),
            (COL_DATE,  "Date"),
        ]:
            srf.blit(font("hint").render(h, True, th["lbl_text"]), (x, CONTENT_TOP))
        pygame.draw.line(srf, th["divider"],
                        (28, CONTENT_TOP + 18), (WIN_W - 28, CONTENT_TOP + 18), 1)
        # rows
        if not entries:
            msg = font("label").render(
                "No scores yet for this mode — play a game!", True, th["hint_text"]
            )
            blit_centered(srf, msg, WIN_W//2, CONTENT_TOP + 140)
        else:
            for i, e in enumerate(entries):
                self._draw_row(srf, i, e, mode_filter, dark, th)
        self._back.draw(srf, th)
        ver = font("hint").render("2048 Enhanced Edition  v2.0", True, th["hint_text"])
        srf.blit(ver, (WIN_W//2 - ver.get_width()//2, WIN_H - 20))
    # single row
    def _draw_row(self, srf, i: int, e: dict, mode_filter, dark: bool, th: dict):
        ry  = CONTENT_TOP + 26 + i * ROW_H
        row = pygame.Rect(28, ry - 4, WIN_W - 56, ROW_H - 6)
        # background + left accent bar
        if i < 3:
            p      = PODIUM[i]
            row_bg = p["row_dark"] if dark else p["row_light"]
            bar_c  = p["bar"]
            score_c = p["score"]
        else:
            row_bg  = (46, 48, 64) if dark else (212, 207, 197)
            bar_c   = th["divider"]
            score_c = th["hud_text"]
        draw_rounded_rect(srf, row_bg, row, ROW_RADIUS)
        # accent bar on the left edge
        bar_rect = pygame.Rect(row.left, row.top, BAR_W, row.height)
        pygame.draw.rect(srf, bar_c, bar_rect,
                        border_top_left_radius=ROW_RADIUS,
                        border_bottom_left_radius=ROW_RADIUS)
        # rank badge
        if i < 3:
            p = PODIUM[i]
            badge_bg = p["badge_bg"]
            badge_fg = p["badge_fg"]
            badge_txt = p["label"]       # "1st" / "2nd" / "3rd"
        else:
            badge_bg  = (75, 75, 95)
            badge_fg  = (200, 200, 210)
            badge_txt = str(i+1)
        badge_w  = 36 if i < 3 else 26
        badge_r  = pygame.Rect(COL_RANK, ry, badge_w, 26)
        draw_rounded_rect(srf, badge_bg, badge_r, 7)
        bn = font("hint").render(badge_txt, True, badge_fg)
        srf.blit(bn, bn.get_rect(center=badge_r.center))
        # score (podium rows get coloured text + bold feel)
        sc = font("hud").render(f"{e['score']:,}", True, score_c)
        srf.blit(sc, (COL_SCORE, ry + 2))
        # grid size  e.g. "4×4"
        bs   = e.get("board_size", 4)
        grid = font("label").render(f"{bs}×{bs}", True, th["lbl_text"])
        srf.blit(grid, grid.get_rect(centerx=COL_GRID + 22, top=ry + 4))
        # extra / mode pill
        if mode_filter is None:
            # show mode pill
            pill_meta = {
                MODE_CLASSIC:     ("Classic",  (70, 120, 195)),
                MODE_TARGET:      ("Target",   (60, 170,  90)),
                MODE_TIME_ATTACK: ("TimeAtk",  (195, 110, 50)),
                MODE_DAILY:       ("Daily",    (140,  80, 200)),
            }
            p_label, p_col = pill_meta.get(e.get("mode", ""), ("?", (100,100,100)))
            pill = pygame.Rect(COL_EXTRA, ry + 4, 68, 20)
            draw_rounded_rect(srf, p_col, pill, 6)
            pt = font("hint").render(p_label, True, (255, 255, 255))
            srf.blit(pt, pt.get_rect(center=pill.center))
        else:
            ex = e.get("extra", "") or "—"
            srf.blit(font("label").render(ex, True, th["lbl_text"]),
                    (COL_EXTRA, ry + 4))
        # date
        srf.blit(font("label").render(e.get("date", ""), True, th["lbl_text"]),
                (COL_DATE, ry + 4))