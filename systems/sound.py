# ── systems/sound.py
# Procedurally generates all sound effects using numpy + pygame.sndarray.
# No external audio files needed.

import numpy as np
import pygame

_sounds: dict = {}
_enabled = True


def _make_sine(freq: float, duration: float, volume: float = 0.4,
               decay: float = 1.0, sample_rate: int = 44100) -> pygame.mixer.Sound:
    t    = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t)
    env  = np.exp(-decay * t / duration)
    wave = (wave * env * volume * 32767).astype(np.int16)
    stereo = np.column_stack([wave, wave])
    return pygame.sndarray.make_sound(stereo)


def _make_chord(freqs: list[float], duration: float, volume: float = 0.35,
                decay: float = 1.2, sample_rate: int = 44100) -> pygame.mixer.Sound:
    t    = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
    env  = np.exp(-decay * t / duration)
    wave = (wave * env * volume * 32767).astype(np.int16)
    stereo = np.column_stack([wave, wave])
    return pygame.sndarray.make_sound(stereo)


def _make_noise_burst(duration: float, volume: float = 0.2,
                      sample_rate: int = 44100) -> pygame.mixer.Sound:
    n    = int(sample_rate * duration)
    wave = np.random.uniform(-1, 1, n)
    env  = np.exp(-6 * np.linspace(0, 1, n))
    wave = (wave * env * volume * 32767).astype(np.int16)
    stereo = np.column_stack([wave, wave])
    return pygame.sndarray.make_sound(stereo)


def init():
    global _sounds
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        _sounds = {
            "move":    _make_sine(440, 0.06, volume=0.25, decay=3.0),
            "merge":   _make_chord([523, 659, 784], 0.18, volume=0.4, decay=2.0),
            "undo":    _make_sine(330, 0.10, volume=0.3,  decay=2.5),
            "win":     _make_chord([523, 659, 784, 1047], 0.7, volume=0.5, decay=0.8),
            "lose":    _make_chord([220, 277, 330], 0.5, volume=0.4, decay=1.0),
            "click":   _make_sine(600, 0.05, volume=0.2,  decay=5.0),
            "shake":   _make_noise_burst(0.15, volume=0.3),
        }
    except Exception as e:
        print("Sound init failed (continuing silently):", e)
        _sounds = {}


def play(name: str):
    if not _enabled or name not in _sounds:
        return
    try:
        _sounds[name].play()
    except Exception:
        pass


def toggle() -> bool:
    global _enabled
    _enabled = not _enabled
    return _enabled


def is_enabled() -> bool:
    return _enabled