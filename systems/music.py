# pylint: disable=no-name-in-module, missing-module-docstring, consider-using-enumerate, unused-argument, broad-exception-caught
# pylint: disable=no-member, invalid-name, missing-function-docstring, multiple-statements, too-many-instance-attributes
# pylint: disable=missing-final-newline, global-statement, missing-class-docstring, unused-import, global-variable-not-assigned

import math
import random
import numpy as np
import pygame

SAMPLE_RATE = 44100
_enabled    = True
_channel: pygame.mixer.Channel | None = None
_context    = "menu"

# Music theory helpers
# A-minor pentatonic: A C D E G  (MIDI notes, octave 3)
_PENTATONIC = [57, 60, 62, 64, 67,   # octave 3
            69, 72, 74, 76, 79]   # octave 4
def _midi_to_freq(note: int) -> float:
    return 440.0 * (2 ** ((note - 69) / 12))

# Context → (tempo_bpm, melody_volume, pad_volume, bass_volume)
_CONTEXTS = {
    "menu":      (72,  0.18, 0.10, 0.12),
    "game":      (90,  0.22, 0.12, 0.15),
    "challenge": (100, 0.26, 0.14, 0.16),
    "intense":   (115, 0.30, 0.16, 0.18),
}

# Synthesis building blocks
def _sine(freq, duration, vol=0.3, phase=0.0):
    n  = int(SAMPLE_RATE * duration)
    t  = np.linspace(0, duration, n, endpoint=False)
    return (np.sin(2 * math.pi * freq * t + phase) * vol).astype(np.float32)
def _triangle(freq, duration, vol=0.2):
    n  = int(SAMPLE_RATE * duration)
    t  = np.linspace(0, duration, n, endpoint=False)
    w  = 2 * (t * freq - np.floor(t * freq + 0.5))
    return (w * vol).astype(np.float32)
def _apply_adsr(wave, sr, a=0.05, d=0.1, s_level=0.7, r=0.15):
    n   = len(wave)
    env = np.ones(n, dtype=np.float32)
    ai  = int(a * sr);  di = int(d * sr);  ri = int(r * sr)
    if ai > 0: env[:ai]   = np.linspace(0, 1,       min(ai, n))
    if di > 0: env[ai:ai+di] = np.linspace(1, s_level, min(di, n - ai))
    env[ai+di:max(n-ri,0)]   = s_level
    if ri > 0: env[max(n-ri,0):] = np.linspace(s_level, 0, min(ri, n - max(n-ri,0)))
    return wave * env
def _reverb(wave, delay_samples=2200, decay=0.35):
    out = wave.copy()
    for i in range(delay_samples, len(out)):
        out[i] += out[i - delay_samples] * decay
    return np.clip(out, -1, 1)

# ── Sequencer ─────────────────────────────────────────────────────────── #
_PATTERNS = {
    "menu":      [0, 4, 2, 7, 5, 9, 4, 2],
    "game":      [0, 2, 4, 7, 5, 4, 2, 9],
    "challenge": [2, 5, 7, 4, 9, 7, 5, 0],
    "intense":   [4, 7, 9, 7, 5, 9, 7, 4],
}
def _build_bar(context: str) -> np.ndarray:
    """Generate one 2-second musical bar for the given context."""
    bpm, mel_vol, pad_vol, bass_vol = _CONTEXTS.get(context, _CONTEXTS["menu"])
    beat   = 60.0 / bpm
    bar_t  = beat * 4
    n_bar  = int(SAMPLE_RATE * bar_t)
    mix    = np.zeros(n_bar, dtype=np.float32)
    pattern = _PATTERNS.get(context, _PATTERNS["menu"])
    # ── bass drone (root + fifth, two octaves down)
    root_freq = _midi_to_freq(45)   # A2
    fifth_freq = root_freq * 1.5
    bass = _triangle(root_freq,  bar_t, bass_vol * 0.7) + \
           _triangle(fifth_freq, bar_t, bass_vol * 0.4)
    mix += bass * 0.8
    # ── pad chords (Am → G → C → Em cycle, soft sine)
    chord_roots = [57, 55, 60, 52]   # Am G C Em
    chord_idx   = random.randint(0, 3)
    for interval in [0, 3, 7]:
        f = _midi_to_freq(chord_roots[chord_idx] + interval)
        pad = _sine(f, bar_t, pad_vol * 0.6, phase=random.uniform(0, 0.5))
        pad = _apply_adsr(pad, SAMPLE_RATE, a=0.3, d=0.2, s_level=0.8, r=0.4)
        mix += pad
    # ── melody (pentatonic notes, 8th-note rhythm)
    step_t  = beat / 2
    step_n  = int(SAMPLE_RATE * step_t)
    for i, pidx in enumerate(pattern):
        offset = i * step_n
        if offset + step_n > n_bar:
            break
        note  = _PENTATONIC[pidx % len(_PENTATONIC)]
        freq  = _midi_to_freq(note)
        # slight pitch variation for humanisation
        freq *= random.uniform(0.998, 1.002)
        seg   = _sine(freq, step_t, mel_vol, phase=random.uniform(0, 0.3))
        seg   = _apply_adsr(seg, SAMPLE_RATE, a=0.01, d=0.05, s_level=0.6, r=0.08)
        mix[offset:offset + step_n] += seg
    # reverb + normalise
    mix = _reverb(mix)
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak * 0.72
    # Convert to int16 stereo
    s16 = (mix * 32767).astype(np.int16)
    return np.column_stack([s16, s16])

# Public API
_next_buf: pygame.mixer.Sound | None = None
_buf_ctx  = None
_beat_timer = 0.0
_bar_duration = 2.0    # seconds per bar (updated on context change)
def init():
    global _channel
    try:
        # mixer should already be init'd by sound.py; just grab a channel
        _channel = pygame.mixer.Channel(6)   # dedicate channel 6 to music
        _channel.set_volume(0.5)
        _queue_next_bar(_context)
    except Exception as e:
        print("Music init failed (continuing silently):", e)
def _queue_next_bar(ctx: str):
    global _next_buf, _buf_ctx
    try:
        data    = _build_bar(ctx)
        _next_buf  = pygame.sndarray.make_sound(data)
        _buf_ctx   = ctx
    except Exception:
        _next_buf = None
def set_context(ctx: str):
    global _context, _bar_duration
    if ctx == _context:
        return
    _context = ctx
    bpm = _CONTEXTS.get(ctx, _CONTEXTS["menu"])[0]
    _bar_duration = (60.0 / bpm) * 4
    _queue_next_bar(ctx)
def tick(dt: float):
    """Call once per frame. Advances the music sequencer."""
    global _beat_timer, _bar_duration
    if not _enabled or _channel is None:
        return
    _beat_timer += dt
    # When the current bar is almost done, play the queued next bar
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