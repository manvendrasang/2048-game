# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring

class ScoreAnimator:
    SPEED      = 8.0    # fraction of gap closed per second
    MIN_STEP   = 12     # minimum points added per frame so tiny gains aren't sluggish

    def __init__(self):
        self._displayed: float = 0.0
        self._target:    int   = 0

    def set_target(self, score: int):
        self._target = score

    def snap(self, score: int):
        """Instantly jump — call on restart/load."""
        self._displayed = float(score)
        self._target    = score

    def tick(self, dt: float) -> int:
        """Advance animation. Returns integer to display."""
        if self._displayed < self._target:
            gap  = self._target - self._displayed
            step = max(self.MIN_STEP, gap * self.SPEED * dt)
            self._displayed = min(self._target, self._displayed + step)
        elif self._displayed > self._target:
            # score went down (undo) — snap immediately
            self._displayed = float(self._target)
        return int(self._displayed)

    @property
    def value(self) -> int:
        return int(self._displayed)
