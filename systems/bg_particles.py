# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring, no-member, multiple-statements

import math
import random
import pygame


class BgParticle:
    __slots__ = ("x", "y", "vx", "vy", "dvx", "dvy",
                "radius", "base_alpha", "alpha", "color",
                "phase", "phase_speed")

    def __init__(self, w: int, h: int):
        self.x          = random.uniform(0, w)
        self.y          = random.uniform(0, h)
        # autonomous drift — slow constant velocity plus tiny random wander
        speed           = random.uniform(0.15, 0.45)
        angle           = random.uniform(0, math.tau)
        self.vx         = math.cos(angle) * speed
        self.vy         = math.sin(angle) * speed
        self.dvx        = 0.0   # mouse repulsion component
        self.dvy        = 0.0
        self.radius     = random.uniform(2, 6)
        self.base_alpha = random.randint(30, 85)
        self.alpha      = self.base_alpha
        self.phase      = random.uniform(0, math.tau)
        self.phase_speed= random.uniform(0.008, 0.022)
        self.color      = random.choice([
            (237, 194,  46),
            (100, 160, 220),
            (100, 220, 140),
            (220, 140, 100),
            (180, 120, 220),
        ])

    def update(self, w: int, h: int, mx: int, my: int):
        # mouse repulsion
        dx   = self.x - mx
        dy   = self.y - my
        dist = math.hypot(dx, dy)
        if dist < 120 and dist > 0:
            force    = (120 - dist) / 120 * 1.5
            self.dvx += (dx / dist) * force
            self.dvy += (dy / dist) * force

        # decay repulsion component back to zero
        self.dvx *= 0.92
        self.dvy *= 0.92

        # total velocity: base drift + repulsion
        self.x += self.vx + self.dvx
        self.y += self.vy + self.dvy

        # slight random wander to autonomous drift
        self.vx += random.uniform(-0.004, 0.004)
        self.vy += random.uniform(-0.004, 0.004)

        # clamp autonomous drift speed so it stays gentle
        speed = math.hypot(self.vx, self.vy)
        if speed > 0.55:
            self.vx = self.vx / speed * 0.55
            self.vy = self.vy / speed * 0.55

        # wrap around edges
        if self.x < -10:  self.x = w + 10
        if self.x > w+10: self.x = -10
        if self.y < -10:  self.y = h + 10
        if self.y > h+10: self.y = -10

        # pulse alpha
        self.phase += self.phase_speed
        self.alpha  = int(self.base_alpha + math.sin(self.phase) * 18)
        self.alpha  = max(10, min(110, self.alpha))


class BgParticleSystem:
    COUNT = 80

    def __init__(self, display_w: int, display_h: int):
        self.w          = display_w
        self.h          = display_h
        self._parts     = [BgParticle(display_w, display_h) for _ in range(self.COUNT)]
        self._line_surf = pygame.Surface((display_w, display_h), pygame.SRCALPHA)

    def update(self, mouse_display_pos: tuple[int, int]):
        mx, my = mouse_display_pos
        for p in self._parts:
            p.update(self.w, self.h, mx, my)

    def draw(self, surface: pygame.Surface):
        # draw particles
        for p in self._parts:
            s = pygame.Surface((int(p.radius)*2 + 2, int(p.radius)*2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(
                s, (*p.color, p.alpha),
                (int(p.radius)+1, int(p.radius)+1),
                int(p.radius),
            )
            surface.blit(s, (int(p.x) - int(p.radius), int(p.y) - int(p.radius)))

        # faint connection lines between nearby particles
        self._line_surf.fill((0, 0, 0, 0))
        for i, a in enumerate(self._parts):
            for b in self._parts[i+1:]:
                dist = math.hypot(a.x - b.x, a.y - b.y)
                if dist < 75:
                    alpha = int((1 - dist / 75) * 28)
                    pygame.draw.line(
                        self._line_surf,
                        (*a.color, alpha),
                        (int(a.x), int(a.y)),
                        (int(b.x), int(b.y)),
                        1,
                    )
        surface.blit(self._line_surf, (0, 0))
