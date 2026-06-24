#!/usr/bin/env python3
# synoptyk: TIMDR + Λ–τ–ρ na danych synoptycznych IMGW (np. Balice)

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict


# ==========================
# 1. Wczytanie danych IMGW
# ==========================

def load_imgw_csv(path: str) -> pd.DataFrame:
    """
    Oczekiwany format CSV (godzinowy):
    kolumny: datetime, temp, pressure, humidity, wind_speed, wind_dir, precip
    datetime w formacie ISO: YYYY-MM-DD HH:MM
    """
    df = pd.read_csv(path, parse_dates=["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    return df


# ==========================
# 2. Świece (OHLC) dla serii
# ==========================

def make_candles(df: pd.DataFrame, col: str, freq: str = "1H") -> pd.DataFrame:
    """
    Buduje świece OHLC dla wybranej kolumny (np. pressure, temp).
    freq: "1H", "4H", "12H" itd.
    """
    s = df.set_index("datetime")[col]
    ohlc = s.resample(freq).agg(["first", "max", "min", "last"])
    ohlc.columns = ["open", "high", "low", "close"]
    ohlc = ohlc.dropna()
    return ohlc


# ==========================
# 3. TIMDR – sygnały świecowe
# ==========================

@dataclass
class CandleSignal:
    time: pd.Timestamp
    kind: str
    strength: float
    meta: Dict


def detect_trend_reversal(candles: pd.DataFrame, threshold: float = 0.5) -> List[CandleSignal]:
    """
    Odwrócenie trendu: zmiana znaku różnicy close-close między kolejnymi świecami.
    threshold – minimalna zmiana (w jednostkach serii, np. hPa).
    """
    signals = []
    closes = candles["close"].values
    times = candles.index

    diffs = np.diff(closes)
    signs = np.sign(diffs)

    for i in range(1, len(diffs)):
        if signs[i] != 0 and signs[i - 1] != 0 and signs[i] != signs[i - 1]:
            # zmiana kierunku
            strength = abs(diffs[i])
            if strength >= threshold:
                signals.append(
                    CandleSignal(
                        time=times[i + 1],
                        kind="trend_reversal",
                        strength=float(strength),
                        meta={"prev_diff": float(diffs[i - 1]), "curr_diff": float(diffs[i])},
                    )
                )
    return signals


def detect_anomalies(candles: pd.DataFrame, sigma: float = 2.0) -> List[CandleSignal]:
    """
    Anomalie: świeca, której zmiana (close-open) przekracza sigma * std.
    """
    signals = []
    delta = candles["close"] - candles["open"]
    std = delta.std()
    times = candles.index

    for t, d in zip(times, delta):
        if abs(d) > sigma * std:
            signals.append(
                CandleSignal(
                    time=t,
                    kind="anomaly",
                    strength=float(abs(d)),
                    meta={"delta": float(d), "sigma": float(sigma), "std": float(std)},
                )
            )
    return signals


def detect_momentum(candles: pd.DataFrame, window: int = 3, threshold: float = 1.0) -> List[CandleSignal]:
    """
    Momentum: kumulatywna zmiana w oknie (np. 3 świece) przekracza threshold.
    """
    signals = []
    closes = candles["close"].values
    times = candles.index

    for i in range(window, len(closes)):
        window_delta = closes[i] - closes[i - window]
        if abs(window_delta) >= threshold:
            signals.append(
                CandleSignal(
                    time=times[i],
                    kind="momentum",
                    strength=float(abs(window_delta)),
                    meta={"window": window, "delta": float(window_delta)},
                )
            )
    return signals


# ==========================
# 4. Λ–τ–ρ – meta-struktura
# ==========================

@dataclass
class LTROutput:
    lambda_struct: Dict
    tau_transform: Dict
    rho_defect: Dict


def ltr_analysis(df: pd.DataFrame) -> LTROutput:
    """
    Bardzo uproszczona wersja:
    Λ – stabilność danych
    τ – charakter zmian
    ρ – miejsca defektu (nagłe skoki)
    """
    # Λ – sprawdzenie braków i szumu
    lambda_struct = {
        "rows": len(df),
        "missing": int(df.isna().sum().sum()),
        "stable": bool(df.isna().sum().sum() == 0),
    }

    # τ – rozkład zmian ciśnienia
    pressure = df["pressure"].values
    diffs = np.diff(pressure)
    tau_transform = {
        "mean_diff": float(np.mean(diffs)),
        "std_diff": float(np.std(diffs)),
        "max_diff": float(np.max(diffs)),
        "min_diff": float(np.min(diffs)),
    }

    # ρ – defekt: skoki powyżej progu
    defect_threshold = np.std(diffs) * 3
    defect_indices = np.where(abs(diffs) > defect_threshold)[0]
    rho_defect = {
        "threshold": float(defect_threshold),
        "count": int(len(defect_indices)),
        "times": [str(df["datetime"].iloc[i + 1]) for i in defect_indices],
    }

    return LTROutput(lambda_struct=lambda_struct, tau_transform=tau_transform, rho_defect=rho_defect)


# ==========================
# 5. Prognoza 48h – logika TIMDR
# ==========================

@dataclass
class Forecast48h:
    summary: str
    details: Dict


def forecast_48h(df: pd.DataFrame) -> Forecast48h:
    """
    Uproszczona prognoza 48h na podstawie:
    - świec ciśnienia (12H)
    - świec temperatury (4H)
    - wilgotności (1H)
    - sygnałów TIMDR
    """
    # Świece
    candles_p_12h = make_candles(df, "pressure", "12H")
    candles_t_4h = make_candles(df, "temp", "4H")
    candles_h_1h = make_candles(df, "humidity", "1H")

    # Sygnały
    p_rev = detect_trend_reversal(candles_p_12h, threshold=2.0)
    p_anom = detect_anomalies(candles_p_12h, sigma=2.0)
    t_mom = detect_momentum(candles_t_4h, window=3, threshold=2.0)
    h_anom = detect_anomalies(candles_h_1h, sigma=2.0)

    # Prosta logika:
    # - brak dużych odwróceń + brak anomalii wilgotności → stabilnie, sucho
    # - momentum temperatury dodatnie → ocieplenie
    # - pojedyncze odwrócenie ciśnienia → mikro-front

    stable_pressure = len(p_rev) == 0 and len(p_anom) == 0
    stable_humidity = len(h_anom) == 0
    warming = any(sig.meta["delta"] > 0 for sig in t_mom)
    micro_front = len(p_rev) == 1 and len(p_anom) <= 1

    summary_parts = []
    if stable_pressure and stable_humidity:
        summary_parts.append("pogoda stabilna, bez opadów")
    else:
        summary_parts.append("możliwe przejście frontu / zmiana pogody")

    if warming:
        summary_parts.append("lekki wzrost temperatury w ciągu 48h")
    else:
        summary_parts.append("bez wyraźnego trendu temperatury")

    if micro_front:
        summary_parts.append("mikro-front w horyzoncie ~36–42h")

    summary = "; ".join(summary_parts)

    details = {
        "pressure_signals": [s.kind for s in p_rev + p_anom],
        "temp_momentum_count": len(t_mom),
        "humidity_anomalies_count": len(h_anom),
        "stable_pressure": stable_pressure,
        "stable_humidity": stable_humidity,
        "warming": warming,
        "micro_front": micro_front,
    }

    return Forecast48h(summary=summary, details=details)


# ==========================
# 6. Główna funkcja synoptyka
# ==========================

def run_synoptyk(path: str) -> None:
    df = load_imgw_csv(path)

    # Λ–τ–ρ
    ltr = ltr_analysis(df)

    # Prognoza 48h
    fc = forecast_48h(df)

    print("=== SYNOPTYK / TIMDR / Λ–τ–ρ ===")
    print("Λ (struktura):", ltr.lambda_struct)
    print("τ (transformacja):", ltr.tau_transform)
    print("ρ (defekt):", ltr.rho_defect)
    print("\nPrognoza 48h (TIMDR):")
    print(fc.summary)
    print("Szczegóły:", fc.details)


if __name__ == "__main__":
    # TODO: podmień ścieżkę na swój plik CSV z Balic
    csv_path = "balice_30dni.csv"
    run_synoptyk(csv_path)


