# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring, multiple-statements, invalid-name, global-statement
# pylint: disable=global-variable-not-assigned, broad-exception-caught, unused-variable

import math
import random
import numpy as np
import pygame

SAMPLE_RATE = 44100
_enabled    = True
_channel: pygame.mixer.Channel | None = None
_context    = "menu"

_PENTATONIC = [69, 72, 74, 76, 79,   # A4 C5 D5 E5 G5
               81, 84, 86, 88, 91]   # A5 C6 D6 E6 G6

def _midi_to_freq(note: int) -> float:
    return 440.0 * (2 ** ((note - 69) / 12))

# context → (bpm, volume)
_CONTEXTS = {
    "menu":      (60,  0.10),
    "game":      (72,  0.12),
    "challenge": (80,  0.13),
    "intense":   (88,  0.14),
}

_PATTERNS = {
    "menu":      [0, 2, 4, 2, 5, 4, 7, 4],
    "game":      [0, 4, 2, 7, 4, 9, 5, 2],
    "challenge": [2, 4, 7, 5, 9, 7, 4, 0],
    "intense":   [4, 7, 9, 5, 7, 4, 9, 7],
}

def _sine_note(freq: float, duration: float, vol: float) -> np.ndarray:
    n   = int(SAMPLE_RATE * duration)
    t   = np.linspace(0, duration, n, endpoint=False)
    # pure sine — no harmonics, no bass
    wave = np.sin(2 * math.pi * freq * t)
    # soft envelope: slow attack, very long decay
    attack  = int(0.08 * SAMPLE_RATE)
    release = n
    env = np.ones(n, dtype=np.float32)
    if attack > 0:
        env[:attack] = np.linspace(0.0, 1.0, min(attack, n))
    env[attack:] = np.exp(-2.5 * np.linspace(0, 1, max(1, n - attack)))
    return (wave * env * vol).astype(np.float32)


def _build_bar(context: str) -> np.ndarray:
    bpm, vol = _CONTEXTS.get(context, _CONTEXTS["menu"])
    beat     = 60.0 / bpm
    bar_t    = beat * 4
    n_bar    = int(SAMPLE_RATE * bar_t)
    mix      = np.zeros(n_bar, dtype=np.float32)

    pattern  = _PATTERNS.get(context, _PATTERNS["menu"])
    step_t   = beat / 2
    step_n   = int(SAMPLE_RATE * step_t)

    for i, pidx in enumerate(pattern):
        offset = i * step_n
        if offset + step_n > n_bar:
            break
        note  = _PENTATONIC[pidx % len(_PENTATONIC)]
        # small random humanisation
        freq  = _midi_to_freq(note) * random.uniform(0.999, 1.001)
        seg   = _sine_note(freq, step_t, vol)
        mix[offset:offset + len(seg)] += seg

    # very light high-shelf air (no reverb — keeps it clean and calm)
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak * 0.55

    s16 = (mix * 32767).astype(np.int16)
    return np.column_stack([s16, s16])


_next_buf: pygame.mixer.Sound | None = None
_beat_timer   = 0.0
_bar_duration = 4.0


def init():
    global _channel
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        _channel = pygame.mixer.Channel(6)
        _channel.set_volume(0.4)
        _queue_next_bar(_context)
    except Exception as e:
        print("Music init failed:", e)


def _queue_next_bar(ctx: str):
    global _next_buf
    try:
        _next_buf = pygame.sndarray.make_sound(_build_bar(ctx))
    except Exception:
        _next_buf = None


def set_context(ctx: str):
    global _context, _bar_duration
    if ctx == _context:
        return
    _context      = ctx
    bpm           = _CONTEXTS.get(ctx, _CONTEXTS["menu"])[0]
    _bar_duration = (60.0 / bpm) * 4
    _queue_next_bar(ctx)


def tick(dt: float):
    global _beat_timer, _bar_duration
    if not _enabled or _channel is None:
        return
    _beat_timer += dt
    if _beat_timer >= _bar_duration * 0.85 and _next_buf is not None:
        try:
            if not _channel.get_busy():
                _channel.play(_next_buf)
                _beat_timer = 0.0
                _queue_next_bar(_context)
            elif _beat_timer >= _bar_duration:
                _channel.queue(_next_buf)
                _beat_timer = 0.0
                _queue_next_bar(_context)
        except Exception:
            pass


def toggle() -> bool:
    global _enabled
    _enabled = not _enabled
    if _channel:
        try:
            if _enabled:
                _channel.unpause()
            else:
                _channel.pause()
        except Exception:
            pass
    return _enabled


def is_enabled() -> bool:
    return _enabled


def get_volume() -> float:
    if _channel:
        try:
            return _channel.get_volume()
        except Exception:
            pass
    return 0.4


def set_volume(vol: float):
    """Set music volume 0.0–1.0."""
    v = max(0.0, min(1.0, vol))
    if _channel:
        try:
            _channel.set_volume(v)
        except Exception:
            pass
