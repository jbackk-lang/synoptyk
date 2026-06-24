#!/usr/bin/env python3
# AUDIO-SYNOPTYK
# TIMDR + Λ–τ–ρ na metadanych akustycznych urządzenia audio

import numpy as np
import sounddevice as sd
from dataclasses import dataclass
from typing import Dict, List


# ==========================
# 1. Pobieranie szumu audio
# ==========================

def capture_noise(duration: float = 2.0, samplerate: int = 44100) -> np.ndarray:
    """
    Rejestruje szum z mikrofonu przez 'duration' sekund.
    Zwraca sygnał jako tablicę numpy.
    """
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
    sd.wait()
    return audio.flatten()


# ==========================
# 2. FFT + metadane akustyczne
# ==========================

def extract_audio_features(signal: np.ndarray, samplerate: int = 44100) -> Dict:
    """
    Wyciąga metadane akustyczne:
    - widmo FFT
    - energia w pasmach
    - szum tła
    - dominujące częstotliwości
    """
    N = len(signal)
    fft_vals = np.abs(np.fft.rfft(signal))
    freqs = np.fft.rfftfreq(N, 1 / samplerate)

    # Energia w pasmach
    bands = {
        "low": float(np.mean(fft_vals[(freqs >= 20) & (freqs < 200)])),
        "mid": float(np.mean(fft_vals[(freqs >= 200) & (freqs < 2000)])),
        "high": float(np.mean(fft_vals[(freqs >= 2000) & (freqs < 8000)])),
    }

    # Szum tła
    noise_floor = float(np.median(fft_vals))

    # Dominanta
    dominant_freq = float(freqs[np.argmax(fft_vals)])

    return {
        "bands": bands,
        "noise_floor": noise_floor,
        "dominant_freq": dominant_freq,
        "fft": fft_vals,
        "freqs": freqs,
    }


# ==========================
# 3. TIMDR na audio
# ==========================

@dataclass
class AudioSignal:
    kind: str
    strength: float
    meta: Dict


def detect_audio_twist(prev: Dict, curr: Dict) -> List[AudioSignal]:
    """
    Skręt: zmiana kierunku energii w pasmach.
    """
    signals = []
    for band in ["low", "mid", "high"]:
        diff = curr["bands"][band] - prev["bands"][band]
        if np.sign(diff) != np.sign(prev["bands"][band] - prev["bands"][band]):
            signals.append(AudioSignal("twist", float(abs(diff)), {"band": band}))
    return signals


def detect_audio_defect(prev: Dict, curr: Dict, sigma: float = 2.5) -> List[AudioSignal]:
    """
    Defekt: skok energii lub szumu tła.
    """
    signals = []

    # Szum tła
    delta_noise = curr["noise_floor"] - prev["noise_floor"]
    if abs(delta_noise) > sigma * np.std([prev["noise_floor"], curr["noise_floor"]]):
        signals.append(AudioSignal("defect_noise", float(abs(delta_noise)), {}))

    # Pasma
    for band in ["low", "mid", "high"]:
        delta = curr["bands"][band] - prev["bands"][band]
        if abs(delta) > sigma * np.std([prev["bands"][band], curr["bands"][band]]):
            signals.append(AudioSignal("defect_band", float(abs(delta)), {"band": band}))

    return signals


def detect_audio_resonance(prev: Dict, curr: Dict) -> List[AudioSignal]:
    """
    Rezonans: jednoczesna zmiana wielu pasm.
    """
    changes = []
    for band in ["low", "mid", "high"]:
        changes.append(curr["bands"][band] - prev["bands"][band])

    if all(abs(c) > 0.1 * abs(changes[0]) for c in changes):
        return [AudioSignal("resonance", float(np.mean(np.abs(changes))), {})]

    return []


# ==========================
# 4. Główna funkcja
# ==========================

def run_audio_synoptyk():
    print("Rejestruję szum (próbka 1)...")
    s1 = capture_noise()
    f1 = extract_audio_features(s1)

    print("Rejestruję szum (próbka 2)...")
    s2 = capture_noise()
    f2 = extract_audio_features(s2)

    twist = detect_audio_twist(f1, f2)
    defect = detect_audio_defect(f1, f2)
    resonance = detect_audio_resonance(f1, f2)

    print("\n=== AUDIO-SYNOPTYK / TIMDR ===")
    print("Skręty:", [s.kind for s in twist])
    print("Defekty:", [s.kind for s in defect])
    print("Rezonans:", [s.kind for s in resonance])

    return twist, defect, resonance


if __name__ == "__main__":
    run_audio_synoptyk()
