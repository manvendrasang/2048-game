# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring

import random


class ScreenShake:
    def __init__(self):
        self._trauma  = 0.0   # 0-1  (higher = more shake)
        self._decay   = 0.12  # subtracted per frame
    def shake(self, intensity: float = 0.6):
        """Trigger a shake. intensity 0–1."""
        self._trauma = min(1.0, self._trauma + intensity)
    def update(self) -> tuple[int, int]:
        """Call once per frame. Returns (offset_x, offset_y) to shift the whole display."""
        if self._trauma <= 0:
            return 0, 0
        mag = int(self._trauma ** 2 * 14)   # square for smoother falloff
        ox  = random.randint(-mag, mag)
        oy  = random.randint(-mag, mag)
        self._trauma = max(0.0, self._trauma - self._decay)
        return ox, oy
    def is_active(self) -> bool:
        return self._trauma > 0