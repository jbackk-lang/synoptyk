#!/usr/bin/env python3
# AUDIO-SYNOPTYK
# TIMDR + Λ–τ–ρ na metadanych akustycznych urządzenia audio
#
# POPRAWKI v2:
#   BUG 1 — detect_audio_twist: prev[band] - prev[band] = 0 zawsze
#            → warunek był spełniony dla KAŻDEJ niezerowej zmiany,
#              czyli twist był zgłaszany zawsze, bez wykrywania faktycznego
#              odwrócenia kierunku. Fix: zapamiętujemy diff_prev między
#              wywołaniami przez opcjonalny parametr prev_diffs.
#
#   BUG 2 — detect_audio_defect: std([prev, curr]) to zawsze |diff|/2,
#            więc warunek |delta| > sigma * std redukuje się do
#            |delta| > sigma/2 * |delta|, co jest trywialne (sigma=2.5 → False zawsze).
#            Fix: historia szumu tła i pasm trzymana w AudioHistory,
#            std liczone z min. 5 ostatnich próbek.
#
#   BUG 3 — detect_audio_resonance: porównanie do changes[0] zamiast
#            do średniej zmian — gdy changes[0] ≈ 0, próg jest ~0
#            i rezonans zgłaszany przy byle szumie; gdy changes[0] jest
#            bardzo duże, pozostałe pasma nigdy nie przejdą progu.
#            Fix: próg = 0.3 * mean(abs(changes)).

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ==========================
# 1. Pobieranie szumu audio
# ==========================

def capture_noise(duration: float = 2.0, samplerate: int = 44100) -> np.ndarray:
    """
    Rejestruje szum z mikrofonu przez 'duration' sekund.
    Zwraca sygnał jako tablicę numpy (mono, float32).

    Wymaga biblioteki sounddevice i działającego urządzenia audio.
    Import odłożony do momentu wywołania — moduł daje się importować
    bez sprzętu audio (np. w testach jednostkowych).
    """
    import sounddevice as sd
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
      - energia w pasmach (low/mid/high)
      - szum tła (mediana widma)
      - dominująca częstotliwość
    """
    N = len(signal)
    fft_vals = np.abs(np.fft.rfft(signal))
    freqs = np.fft.rfftfreq(N, 1 / samplerate)

    bands = {
        "low":  float(np.mean(fft_vals[(freqs >= 20)   & (freqs < 200)])),
        "mid":  float(np.mean(fft_vals[(freqs >= 200)  & (freqs < 2000)])),
        "high": float(np.mean(fft_vals[(freqs >= 2000) & (freqs < 8000)])),
    }
    noise_floor    = float(np.median(fft_vals))
    dominant_freq  = float(freqs[np.argmax(fft_vals)])

    return {
        "bands":        bands,
        "noise_floor":  noise_floor,
        "dominant_freq": dominant_freq,
        "fft":          fft_vals,
        "freqs":        freqs,
    }


# ==========================
# 3. Historia próbek (fix BUG 2)
# ==========================

@dataclass
class AudioHistory:
    """
    Przechowuje historię N ostatnich próbek metadanych akustycznych.
    Używana do liczenia sensownego std w detect_audio_defect.

    BUG 2 FIX: std([prev, curr]) == |diff|/2, co jest trywialne i bezużyteczne.
    Potrzebujemy min. kilku próbek historycznych, żeby std cokolwiek znaczył.
    """
    max_len: int = 30

    noise_history:  List[float] = field(default_factory=list)
    band_history:   Dict[str, List[float]] = field(default_factory=lambda: {
        "low": [], "mid": [], "high": []
    })

    def update(self, features: Dict) -> None:
        self.noise_history.append(features["noise_floor"])
        if len(self.noise_history) > self.max_len:
            self.noise_history.pop(0)
        for b in ["low", "mid", "high"]:
            self.band_history[b].append(features["bands"][b])
            if len(self.band_history[b]) > self.max_len:
                self.band_history[b].pop(0)

    def noise_std(self) -> float:
        if len(self.noise_history) < 3:
            return 1e-9
        return float(np.std(self.noise_history))

    def band_std(self, band: str) -> float:
        h = self.band_history[band]
        if len(h) < 3:
            return 1e-9
        return float(np.std(h))


# ==========================
# 4. TIMDR na audio
# ==========================

@dataclass
class AudioSignal:
    kind:     str
    strength: float
    meta:     Dict


def detect_audio_twist(
    prev: Dict,
    curr: Dict,
    prev_diffs: Optional[Dict[str, float]] = None,
) -> tuple[List[AudioSignal], Dict[str, float]]:
    """
    Skręt: zmiana kierunku energii w paśmie.

    BUG 1 FIX:
      Oryginał: np.sign(prev[band] - prev[band]) == np.sign(0) == 0
      → warunek diff != 0 był zawsze spełniony → fałszywe skręty przy każdej zmianie.

      Poprawka: porównujemy sign(diff_curr) z sign(diff_prev), gdzie diff_prev
      pochodzi z poprzedniego wywołania funkcji (przekazany jako prev_diffs).
      Funkcja zwraca teraz krotkę (signals, curr_diffs) — curr_diffs należy
      przekazać jako prev_diffs przy następnym wywołaniu.

    Parametry:
      prev       — metadane poprzedniej próbki
      curr       — metadane bieżącej próbki
      prev_diffs — słownik {band: diff} z poprzedniego wywołania (lub None na start)

    Zwraca:
      (signals, curr_diffs)
    """
    if prev_diffs is None:
        prev_diffs = {"low": 0.0, "mid": 0.0, "high": 0.0}

    signals: List[AudioSignal] = []
    curr_diffs: Dict[str, float] = {}

    for band in ["low", "mid", "high"]:
        diff_curr = curr["bands"][band] - prev["bands"][band]
        diff_prev = prev_diffs.get(band, 0.0)
        curr_diffs[band] = diff_curr

        if (
            np.sign(diff_curr) != 0
            and np.sign(diff_prev) != 0
            and np.sign(diff_curr) != np.sign(diff_prev)
        ):
            signals.append(AudioSignal(
                kind="twist",
                strength=float(abs(diff_curr)),
                meta={"band": band, "diff_prev": diff_prev, "diff_curr": diff_curr},
            ))

    return signals, curr_diffs


def detect_audio_defect(
    prev: Dict,
    curr: Dict,
    history: AudioHistory,
    sigma: float = 2.5,
) -> List[AudioSignal]:
    """
    Defekt: skok energii lub szumu tła przekraczający sigma * std_historii.

    BUG 2 FIX:
      Oryginał: std([prev_val, curr_val]) = |diff|/2
      → warunek |delta| > sigma * |delta|/2 redukuje się do sigma < 2, co jest
        stałe i niezależne od danych. Z sigma=2.5 defekt NIGDY nie był zgłaszany.

      Poprawka: std liczony z AudioHistory (min. 3, maks. 30 próbek).
      Funkcja powinna być wywołana PO history.update(curr).
    """
    signals: List[AudioSignal] = []

    # Szum tła
    delta_noise = curr["noise_floor"] - prev["noise_floor"]
    noise_std = history.noise_std()
    if noise_std > 0 and abs(delta_noise) > sigma * noise_std:
        signals.append(AudioSignal(
            kind="defect_noise",
            strength=float(abs(delta_noise)),
            meta={"delta": delta_noise, "std": noise_std, "sigma": sigma},
        ))

    # Pasma
    for band in ["low", "mid", "high"]:
        delta = curr["bands"][band] - prev["bands"][band]
        b_std = history.band_std(band)
        # min_std: gdy dane są bardzo stabilne (std ≈ 0 → próg ≈ 0),
        # drobny szum pomiarowy generowałby false-positive defekty.
        # Minimalny próg = 1% średniej wartości pasma z historii.
        band_mean = float(np.mean(history.band_history[band])) if history.band_history[band] else 1.0
        min_std = max(b_std, 0.01 * abs(band_mean) + 1e-9)
        if abs(delta) > sigma * min_std:
            signals.append(AudioSignal(
                kind="defect_band",
                strength=float(abs(delta)),
                meta={"band": band, "delta": delta, "std": b_std, "sigma": sigma},
            ))

    return signals


def detect_audio_resonance(prev: Dict, curr: Dict) -> List[AudioSignal]:
    """
    Rezonans: jednoczesna, spójna zmiana we WSZYSTKICH pasmach.

    BUG 3 FIX:
      Oryginał: próg = 0.1 * abs(changes[0])
      → gdy changes[0] ≈ 0: próg ≈ 0, rezonans zgłaszany przy byle szumie.
      → gdy changes[0] duże: pozostałe pasma rzadko go dorównają.
      → asymetryczny i zależny od kolejności pasm.

      Poprawka: próg = 0.3 * mean(abs(changes)) — symetryczny i zależny
      od średniej aktywności wszystkich pasm. Wartość 0.3 oznacza:
      każde pasmo musi zmieniać się o co najmniej 30% średniej zmiany.
      Jeśli jedna zmiana jest dominu jąca, a reszta to szum — brak rezonansu.
    """
    changes = [
        curr["bands"][band] - prev["bands"][band]
        for band in ["low", "mid", "high"]
    ]
    mean_change = float(np.mean(np.abs(changes)))

    if mean_change < 1e-9:
        return []

    threshold = 0.3 * mean_change
    if all(abs(c) >= threshold for c in changes):
        return [AudioSignal(
            kind="resonance",
            strength=mean_change,
            meta={
                "changes": {b: round(c, 6) for b, c in zip(["low","mid","high"], changes)},
                "threshold": round(threshold, 6),
            },
        )]
    return []


# ==========================
# 5. Główna funkcja
# ==========================

def run_audio_synoptyk(n_samples: int = 5) -> tuple:
    """
    Pobiera n_samples próbek audio i analizuje sygnały TIMDR.

    Zwraca:
      (all_twists, all_defects, all_resonances)
    """
    history = AudioHistory()
    prev_diffs: Optional[Dict[str, float]] = None

    print(f"Rejestruję próbkę 1/{n_samples}...")
    s0 = capture_noise()
    f_prev = extract_audio_features(s0)
    history.update(f_prev)

    all_twists:    List[AudioSignal] = []
    all_defects:   List[AudioSignal] = []
    all_resonances: List[AudioSignal] = []

    for i in range(2, n_samples + 1):
        print(f"Rejestruję próbkę {i}/{n_samples}...")
        s = capture_noise()
        f_curr = extract_audio_features(s)
        history.update(f_curr)

        twists, prev_diffs = detect_audio_twist(f_prev, f_curr, prev_diffs)
        defects            = detect_audio_defect(f_prev, f_curr, history)
        resonances         = detect_audio_resonance(f_prev, f_curr)

        all_twists    += twists
        all_defects   += defects
        all_resonances += resonances

        f_prev = f_curr

    print("\n=== AUDIO-SYNOPTYK / TIMDR ===")
    print(f"Skręty ({len(all_twists)}):",    [s.meta.get("band") for s in all_twists])
    print(f"Defekty ({len(all_defects)}):",  [s.kind for s in all_defects])
    print(f"Rezonans ({len(all_resonances)}):", ["resonance" for _ in all_resonances])

    return all_twists, all_defects, all_resonances


if __name__ == "__main__":
    run_audio_synoptyk(n_samples=5)
