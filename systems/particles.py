# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring, no-member

import math
import random
import pygame
from constants import PARTICLE_CONFIGS


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "color", "size", "life", "max_life", "alpha")
    def __init__(self, x, y, vx, vy, color, size, lifetime):
        self.x        = float(x)
        self.y        = float(y)
        self.vx       = vx
        self.vy       = vy
        self.color    = color
        self.size     = size
        self.life     = lifetime
        self.max_life = lifetime
        self.alpha    = 255
    def update(self) -> bool:
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.18          # gravity
        self.vx   *= 0.97          # air drag
        self.life -= 1
        self.alpha = int(255 * self.life / self.max_life)
        return self.life > 0


class ParticleSystem:
    def __init__(self):
        self._particles: list[Particle] = []
    def _threshold_for(self, value: int) -> int | None:
        """Return the matching config key (256/512/1024/2048+)."""
        for threshold in sorted(PARTICLE_CONFIGS.keys(), reverse=True):
            if value >= threshold:
                return threshold
        return None
    def burst(self, cx: int, cy: int, tile_value: int):
        key = self._threshold_for(tile_value)
        if key is None:
            return
        cfg   = PARTICLE_CONFIGS[key]
        count = cfg["count"]
        speed = cfg["speed"]
        size  = cfg["size"]
        color = cfg["color"]
        life  = cfg["lifetime"]
        for i in range(count):
            angle = (2 * math.pi * i / count) + random.uniform(-0.2, 0.2)
            spd   = speed * random.uniform(0.6, 1.4)
            vx    = math.cos(angle) * spd
            vy    = math.sin(angle) * spd
            # slightly randomise color brightness
            r     = min(255, color[0] + random.randint(-20, 20))
            g     = min(255, color[1] + random.randint(-20, 20))
            b     = min(255, color[2] + random.randint(-10, 10))
            sz    = max(2, size + random.randint(-2, 2))
            lt    = life + random.randint(-8, 8)
            self._particles.append(Particle(cx, cy, vx, vy, (r, g, b), sz, lt))
    def update(self):
        self._particles = [p for p in self._particles if p.update()]
    def draw(self, surface: pygame.Surface):
        for p in self._particles:
            s = pygame.Surface((p.size * 2, p.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p.color, p.alpha), (p.size, p.size), p.size)
            surface.blit(s, (int(p.x) - p.size, int(p.y) - p.size))
    def clear(self):
        self._particles.clear()
