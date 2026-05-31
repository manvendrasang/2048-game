# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring, unused-import, no-member

import pygame
import math
from constants import WIN_W, WIN_H
from utils.drawing import draw_rounded_rect, font, blit_centered, Button, panel_mouse_pos
import utils.theme as theme
import systems.sound as sound
from data.persistence import (
    load_stats, load_unlocked_achievements,
    load_challenge_progress, load_daily_record, get_daily_streak,
)
from data.achievements import ALL_ACHIEVEMENTS, CATEGORIES, CATEGORY_LABELS
from data.daily_puzzle import daily_puzzle_number


TAB_PROFILE      = 0
TAB_ACHIEVEMENTS = 1
TAB_LABELS       = ["Profile & Stats", "Achievements"]

TAB_Y   = 115
TAB_H   = 36
TAB_GAP = 8

CATEGORY_COLORS = {
    "tiles":      (237, 194,  46),
    "scores":     (100, 200, 140),
    "games":      (100, 160, 220),
    "challenges": (220, 130,  70),
    "daily":      (160,  90, 210),
}


def _tab_rects() -> list[pygame.Rect]:
    n    = len(TAB_LABELS)
    pad  = 50
    tw   = (WIN_W - pad * 2 - TAB_GAP * (n - 1)) // n
    return [
        pygame.Rect(pad + i * (tw + TAB_GAP), TAB_Y, tw, TAB_H)
        for i in range(n)
    ]


class ProfileScreen:

    def __init__(self, surface: pygame.Surface):
        self.surface      = surface
        self._tab         = TAB_PROFILE
        self._tab_rects   = _tab_rects()
        self._ach_scroll  = 0   # pixel scroll offset for achievements list
        self._back = Button(
            pygame.Rect(WIN_W // 2 - 120, WIN_H - 76, 240, 50),
            "← Back", font_name="menu_med",
        )

    def handle_event(self, event) -> str | None:
        if self._back.is_clicked(event):
            sound.play("click")
            return "back"

        if event.type == pygame.MOUSEBUTTONDOWN:
            import constants as C
            px = event.pos[0] - C.PANEL_OX
            py = event.pos[1] - C.PANEL_OY

            if event.button == 1:
                for i, r in enumerate(self._tab_rects):
                    if r.collidepoint(px, py):
                        if i != self._tab:
                            self._tab = i
                            self._ach_scroll = 0
                            sound.play("click")
                        return None

            # scroll achievements with mouse wheel
            if self._tab == TAB_ACHIEVEMENTS:
                if event.button == 4:
                    self._ach_scroll = max(0, self._ach_scroll - 30)
                elif event.button == 5:
                    self._ach_scroll = max(0, self._ach_scroll + 30)  # max clamped in draw

        if event.type == pygame.KEYDOWN:
            if self._tab == TAB_ACHIEVEMENTS:
                if event.key == pygame.K_UP:
                    self._ach_scroll = max(0, self._ach_scroll - 30)
                elif event.key == pygame.K_DOWN:
                    self._ach_scroll = max(0, self._ach_scroll + 30)  # max clamped in draw

        return None

    def update(self):
        self._back.update(panel_mouse_pos())

    def draw(self):
        th   = theme.get()
        srf  = self.surface
        dark = theme.name() == "dark"
        srf.fill(th["bg"])
        cx = WIN_W // 2

        # Header
        hdr = font("over").render("Profile", True, th["accent"])
        blit_centered(srf, hdr, cx, 65)

        # Tabs
        mp = panel_mouse_pos()
        for i, (label, rect) in enumerate(zip(TAB_LABELS, self._tab_rects)):
            active  = i == self._tab   
            hovered = rect.collidepoint(mp) and not active
            if active:
                bg = th["accent"]
                fg = (30, 30, 30)
            elif hovered:
                bg = (70, 72, 92) if dark else (195, 190, 178)
                fg = th["hud_text"]
            else:
                bg = (50, 52, 68) if dark else (208, 202, 190)
                fg = th["lbl_text"]
            draw_rounded_rect(srf, bg, rect, 8)
            t = font("tab").render(label, True, fg)
            srf.blit(t, t.get_rect(center=rect.center))

        pygame.draw.line(srf, th["divider"], (40, TAB_Y + TAB_H + 10),
                         (WIN_W - 40, TAB_Y + TAB_H + 10), 1)

        if self._tab == TAB_PROFILE:
            self._draw_profile(srf, th, dark, cx)
        else:
            self._draw_achievements(srf, th, dark, cx)

        self._back.draw(srf, th)

        ver = font("hint").render("2048 Enhanced Edition  v2.0", True, th["hint_text"])
        srf.blit(ver, (WIN_W // 2 - ver.get_width() // 2, WIN_H - 20))

    def _draw_profile(self, srf, th, dark, cx):
        stats   = load_stats()
        unlocked = load_unlocked_achievements()
        streak   = get_daily_streak()
        daily    = load_daily_record()
        ch_prog  = load_challenge_progress()

        content_top = TAB_Y + TAB_H + 24

        # Avatar circle with initials / highest tile
        av_cx, av_cy = cx, content_top + 48
        av_r         = 44
        pygame.draw.circle(srf, th["accent"], (av_cx, av_cy), av_r)
        pygame.draw.circle(srf, th["bg"],     (av_cx, av_cy), av_r - 4)
        ht_val  = stats.get("highest_tile", 0)
        av_txt  = str(ht_val) if ht_val else "—"
        av_surf = font("hud").render(av_txt, True, th["accent"])
        srf.blit(av_surf, av_surf.get_rect(center=(av_cx, av_cy)))

        label_surf = font("hint").render("Best Tile", True, th["lbl_text"])
        srf.blit(label_surf, label_surf.get_rect(centerx=cx, top=av_cy + av_r + 6))

        # Quick summary badges
        badge_y   = content_top + 120
        badges    = [
            (f"{stats.get('games_played', 0)}",  "Games"),
            (f"{streak}🔥",                       "Streak"),
            (f"{len(unlocked)}/20",               "Achiev."),
            (f"{sum(1 for v in ch_prog.values() if v.get('completed'))}/10",
                                                   "Challs"),
        ]
        bw, bh = 130, 64
        bg_gap  = 12
        total_w = len(badges) * bw + (len(badges) - 1) * bg_gap
        bx      = cx - total_w // 2
        for val, lbl in badges:
            card = pygame.Rect(bx, badge_y, bw, bh)
            bg   = (48, 50, 68) if dark else (212, 206, 194)
            draw_rounded_rect(srf, bg, card, 12)
            vs   = font("hud").render(val,  True, th["accent"])
            ls   = font("hint").render(lbl, True, th["lbl_text"])
            srf.blit(vs, vs.get_rect(centerx=card.centerx, top=card.top + 8))
            srf.blit(ls, ls.get_rect(centerx=card.centerx, top=card.top + 38))
            bx += bw + bg_gap

        pygame.draw.line(srf, th["divider"],
                         (40, badge_y + bh + 18), (WIN_W - 40, badge_y + bh + 18), 1)

        # Detailed stat rows
        games    = stats.get("games_played", 0)
        total_sc = stats.get("total_score",  0)
        avg_sc   = (total_sc // games) if games else 0
        total_mv = stats.get("total_moves",  0)
        avg_mv   = (total_mv // games)  if games else 0
        best_s   = stats.get("best_single", 0)
        daily_ct = len(daily)

        stat_rows = [
            ("Total Score",        f"{total_sc:,}"),
            ("Best Single Score",  f"{best_s:,}"),
            ("Average Score",      f"{avg_sc:,}"),
            ("Total Moves",        f"{total_mv:,}"),
            ("Avg Moves / Game",   str(avg_mv)),
            ("Daily Puzzles Done", str(daily_ct)),
            ("Puzzle Streak",      f"{streak} day{'s' if streak != 1 else ''}"),
        ]

        row_top = badge_y + bh + 32
        cw, ch2 = WIN_W - 100, 52
        for i, (label, val) in enumerate(stat_rows):
            y    = row_top + i * (ch2 + 8)
            rect = pygame.Rect(50, y, cw, ch2)
            bg   = (48, 50, 68) if dark else (212, 206, 194)
            draw_rounded_rect(srf, bg, rect, 10)
            ls   = font("label").render(label, True, th["lbl_text"])
            vs   = font("hud").render(val,   True, th["accent"])
            srf.blit(ls, (rect.left + 18, rect.centery - ls.get_height() // 2))
            srf.blit(vs, vs.get_rect(right=rect.right - 18, centery=rect.centery))

    def _draw_achievements(self, srf, th, dark, cx):
        unlocked    = load_unlocked_achievements()
        content_top = TAB_Y + TAB_H + 20
        clip_top    = content_top
        clip_bottom = WIN_H - 90
        visible_h   = clip_bottom - clip_top

        # Compute total scrollable content height so we can cap the scroll
        total_content_h = 0
        for cat in CATEGORIES:
            cat_achs = [a for a in ALL_ACHIEVEMENTS if a["category"] == cat]
            if not cat_achs:
                continue
            total_content_h += 32                    # category header
            total_content_h += len(cat_achs) * 70   # achievement cards
            total_content_h += 10                    # gap after category

        max_scroll = max(0, total_content_h - visible_h)
        self._ach_scroll = min(self._ach_scroll, max_scroll)

        # Clip region so achievements don't bleed into back button
        clip = pygame.Rect(0, clip_top, WIN_W, visible_h)
        srf.set_clip(clip)

        y = content_top - self._ach_scroll

        for cat in CATEGORIES:
            cat_achs = [a for a in ALL_ACHIEVEMENTS if a["category"] == cat]
            if not cat_achs:
                continue

            # Category header
            if y + 30 > clip_top and y < clip_bottom:
                cat_label = CATEGORY_LABELS[cat]
                cat_col   = CATEGORY_COLORS[cat]
                pill = pygame.Rect(44, y, 10, 24)
                draw_rounded_rect(srf, cat_col, pill, 4)
                cs = font("label").render(cat_label, True, cat_col)
                srf.blit(cs, (60, y + 2))
            y += 32

            for ach in cat_achs:
                if y + 62 < clip_top or y > clip_bottom:
                    y += 70
                    continue

                done   = ach["id"] in unlocked
                card   = pygame.Rect(44, y, WIN_W - 88, 62)

                if done:
                    bg = (60, 52, 22) if dark else (255, 248, 210)
                else:
                    bg = (44, 46, 62) if dark else (214, 208, 196)
                draw_rounded_rect(srf, bg, card, 10)

                bar_col = CATEGORY_COLORS[cat] if done else th["divider"]
                pygame.draw.rect(srf, bar_col,
                                 pygame.Rect(card.left, card.top, 4, card.height),
                                 border_top_left_radius=10,
                                 border_bottom_left_radius=10)

                ic_cx, ic_cy = card.left + 32, card.centery
                pygame.draw.circle(
                    srf,
                    CATEGORY_COLORS[cat] if done else (70, 70, 90),
                    (ic_cx, ic_cy), 20
                )
                ic_s = font("menu_med").render(ach["icon"], True, (255, 255, 255))
                srf.blit(ic_s, ic_s.get_rect(center=(ic_cx, ic_cy)))

                name_col = th["accent"] if done else th["hud_text"]
                ns = font("label").render(ach["name"], True, name_col)
                ds = font("hint").render(ach["desc"],  True, th["lbl_text"])
                srf.blit(ns, (card.left + 60, card.top + 10))
                srf.blit(ds, (card.left + 60, card.top + 34))

                if done:
                    badge = font("hint").render("✓ Unlocked", True, (80, 200, 100))
                    srf.blit(badge, badge.get_rect(right=card.right - 12, centery=card.centery))
                else:
                    lock = font("hint").render("Locked", True, th["hint_text"])
                    srf.blit(lock, lock.get_rect(right=card.right - 12, centery=card.centery))

                y += 70

            y += 10

        srf.set_clip(None)

        # Scroll hint + progress indicator
        scroll_pct = (self._ach_scroll / max_scroll * 100) if max_scroll > 0 else 100
        if max_scroll > 0:
            hint_txt = f"↑ ↓ or mouse wheel to scroll  ({int(scroll_pct)}%)"
        else:
            hint_txt = "All achievements visible"
        hint = font("hint").render(hint_txt, True, th["hint_text"])
        srf.blit(hint, hint.get_rect(centerx=cx, top=clip_bottom + 4))

        # Thin scroll bar on the right edge
        if max_scroll > 0:
            bar_x      = WIN_W - 12
            bar_top    = clip_top + 4
            bar_height = visible_h - 8
            track      = pygame.Rect(bar_x, bar_top, 4, bar_height)
            draw_rounded_rect(srf, th["divider"], track, 2)
            thumb_h    = max(24, int(bar_height * visible_h / total_content_h))
            thumb_y    = bar_top + int((bar_height - thumb_h) * self._ach_scroll / max_scroll)
            thumb      = pygame.Rect(bar_x, thumb_y, 4, thumb_h)
            draw_rounded_rect(srf, th["accent"], thumb, 2)
