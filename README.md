# 2048-game

2048  –  improved edition
--------------------------
Fixes vs the original
  • Tile rendering was transposed (i/j axes swapped) – fixed
  • getColor crashed on values > 2048 – fixed via fallback
  • saveGameState used f.close instead of f.close() – fixed
  • placeRandomTile could infinite-loop on a full board – fixed
  • loadGameState didn't rebuild tileMatrix to the right size – fixed
  • getRotations returned 0 for UP (no-op) instead of the correct value – fixed
  • Score label was blitted 16× inside the tile loop – fixed
  • reset() called main() recursively (stack overflow risk) – refactored
  • DEFAULT_SCORE was defined but never used – removed
  • Added math.floor instead of the hand-rolled floor()

New features
  • Best-score tracking (persisted to disk)
  • Combo multiplier: consecutive merges in one move reward bonus points
  • Animated score pop-up (+N) on each merge
  • Smooth tile slide/pop animations
  • Tile "birth" animation for newly placed tiles
  • Full HUD: score, best, move counter, undo button hint
  • Gradient-style board background with rounded rects
  • Game-Over overlay with semi-transparent dim
  • Key hints rendered in the HUD