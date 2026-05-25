# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring, no-member

import pygame

class HapticFeedback:
    def __init__(self):
        self._flash_col   = None   # current flash colour or None
        self._flash_alpha = 0      # 0–255
        self._flash_decay = 0      # alpha units subtracted per frame

    def invalid_move(self):
        """Red border flash — triggered when a move key does nothing."""
        self._flash_col   = (220, 60, 60)
        self._flash_alpha = 200
        self._flash_decay = 12

    def merge_flash(self):
        """Gold glow — triggered on any merge."""
        # Only override if not already showing a stronger effect
        if self._flash_col != (220, 60, 60):
            self._flash_col   = (237, 194, 46)
            self._flash_alpha = 140
            self._flash_decay = 8

    def update(self):
        if self._flash_alpha > 0:
            self._flash_alpha = max(0, self._flash_alpha - self._flash_decay)
        if self._flash_alpha == 0:
            self._flash_col = None

    def draw_border(self, surface: pygame.Surface,
                    board_rect: pygame.Rect, radius: int = 14):
        """Draw a coloured border overlay on the board rect."""
        if not self._flash_col or self._flash_alpha <= 0:
            return
        overlay = pygame.Surface(
            (board_rect.width + 8, board_rect.height + 8), pygame.SRCALPHA
        )
        pygame.draw.rect(
            overlay,
            (*self._flash_col, self._flash_alpha),
            overlay.get_rect(),
            width=6,
            border_radius=radius + 4,
        )
        surface.blit(overlay, (board_rect.left - 4, board_rect.top - 4))
