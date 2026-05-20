# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring

import math
import random
import pygame

class BgParticle:
    __slots__ = ("x", "y", "vx", "vy", "radius", "base_alpha",
                "alpha", "color", "phase", "phase_speed")
    def __init__(self, w: int, h: int):
        self.x          = random.uniform(0, w)
        self.y          = random.uniform(0, h)
        self.vx         = random.uniform(-0.3, 0.3)
        self.vy         = random.uniform(-0.3, 0.3)
        self.radius     = random.uniform(2, 6)
        self.base_alpha = random.randint(30, 90)
        self.alpha      = self.base_alpha
        self.phase      = random.uniform(0, math.tau)
        self.phase_speed= random.uniform(0.01, 0.03)
        self.color      = random.choice([
            (237, 194,  46),   # gold
            (100, 160, 220),   # blue
            (100, 220, 140),   # green
            (220, 140, 100),   # orange
            (180, 120, 220),   # purple
        ])
    def update(self, w: int, h: int, mx: int, my: int):
        # mouse repulsion
        dx  = self.x - mx
        dy  = self.y - my
        dist = math.hypot(dx, dy)
        if dist < 120 and dist > 0:
            force = (120 - dist) / 120 * 1.8
            self.vx += (dx / dist) * force
            self.vy += (dy / dist) * force
        # damping
        self.vx *= 0.96
        self.vy *= 0.96
        # drift
        self.x += self.vx
        self.y += self.vy
        # wrap
        if self.x < -10:  self.x = w + 10
        if self.x > w+10: self.x = -10
        if self.y < -10:  self.y = h + 10
        if self.y > h+10: self.y = -10
        # pulse alpha
        self.phase += self.phase_speed
        self.alpha  = int(self.base_alpha + math.sin(self.phase) * 20)
        self.alpha  = max(10, min(120, self.alpha))


class BgParticleSystem:
    COUNT = 80   # lower count keeps framerate smooth
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
        for p in self._parts:
            s = pygame.Surface((int(p.radius)*2 + 2, int(p.radius)*2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(
                s, (*p.color, p.alpha),
                (int(p.radius)+1, int(p.radius)+1),
                int(p.radius),
            )
            surface.blit(s, (int(p.x) - int(p.radius), int(p.y) - int(p.radius)))
        # draw faint connection lines between nearby particles
        self._line_surf.fill((0, 0, 0, 0))
        for i, a in enumerate(self._parts):
            for b in self._parts[i+1:]:
                dist = math.hypot(a.x - b.x, a.y - b.y)
                if dist < 80:
                    alpha = int((1 - dist / 80) * 35)
                    pygame.draw.line(
                        self._line_surf,
                        (*a.color, alpha),
                        (int(a.x), int(a.y)),
                        (int(b.x), int(b.y)),
                        1,
                    )
        surface.blit(self._line_surf, (0, 0))