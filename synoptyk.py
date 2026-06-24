#!/usr/bin/env python3
# synoptyk: TIMDR + Λ–τ–ρ na danych synoptycznych IMGW (np. Balice)
#
# POPRAWKI v2:
#   BUG 4 — make_candles: freq='1H','4H','12H' przestarzałe w pandas >= 2.2
#            (aktywny crash: "Invalid frequency: H").
#            Fix: zamieniono na '1h','4h','12h'.
#
#   BUG 5 — detect_resonance: cichy błąd przy porównaniu Series z różnymi
#            indeksami (df_p co 12h, df_h co 12h — pasują, ale tylko przypadkowo).
#            Fix: reindex df_h do indeksu df_p przed porównaniem.
#
#   BUG 6 — forecast_48h: make_candles wewnątrz funkcji z '12H' → crash.
#            Fix: wywołanie z poprawionymi stringami.
#
#   BUG 7 — run_synoptyk: extensions.scoring importowana wewnątrz __main__
#            bez sprawdzenia czy moduł istnieje → NameError gdy brak extensions/.
#            Fix: import z obsługą ImportError.

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

def make_candles(df: pd.DataFrame, col: str, freq: str = "1h") -> pd.DataFrame:
    """
    Buduje świece OHLC dla wybranej kolumny (np. pressure, temp).

    BUG 4 FIX: pandas >= 2.2 odrzuca stare aliasy 'H','T','S' itd.
    Używaj wyłącznie małych liter: '1h','4h','12h'.
    Stary kod przyjmował '1H','4H','12H' co powoduje crash:
      "Invalid frequency: H. Did you mean h?"
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
    time:     pd.Timestamp
    kind:     str
    strength: float
    meta:     Dict


def detect_trend_reversal(
    candles: pd.DataFrame,
    threshold: float = 0.5,
) -> List[CandleSignal]:
    """
    Odwrócenie trendu: zmiana znaku różnicy close-close między kolejnymi świecami.
    threshold – minimalna zmiana (w jednostkach serii, np. hPa).
    """
    signals = []
    closes = candles["close"].values
    times  = candles.index
    diffs  = np.diff(closes)
    signs  = np.sign(diffs)

    for i in range(1, len(diffs)):
        if signs[i] != 0 and signs[i - 1] != 0 and signs[i] != signs[i - 1]:
            strength = abs(diffs[i])
            if strength >= threshold:
                signals.append(CandleSignal(
                    time=times[i + 1],
                    kind="trend_reversal",
                    strength=float(strength),
                    meta={"prev_diff": float(diffs[i - 1]), "curr_diff": float(diffs[i])},
                ))
    return signals


def detect_anomalies(
    candles: pd.DataFrame,
    sigma: float = 2.0,
) -> List[CandleSignal]:
    """
    Anomalie: świeca, której zmiana (close-open) przekracza sigma * std.
    """
    signals = []
    delta = candles["close"] - candles["open"]
    std   = delta.std()
    times = candles.index

    for t, d in zip(times, delta):
        if abs(d) > sigma * std:
            signals.append(CandleSignal(
                time=t,
                kind="anomaly",
                strength=float(abs(d)),
                meta={"delta": float(d), "sigma": float(sigma), "std": float(std)},
            ))
    return signals


def detect_momentum(
    candles: pd.DataFrame,
    window: int = 3,
    threshold: float = 1.0,
) -> List[CandleSignal]:
    """
    Momentum: kumulatywna zmiana w oknie (np. 3 świece) przekracza threshold.
    """
    signals = []
    closes = candles["close"].values
    times  = candles.index

    for i in range(window, len(closes)):
        window_delta = closes[i] - closes[i - window]
        if abs(window_delta) >= threshold:
            signals.append(CandleSignal(
                time=times[i],
                kind="momentum",
                strength=float(abs(window_delta)),
                meta={"window": window, "delta": float(window_delta)},
            ))
    return signals


def detect_resonance(
    df_p: pd.DataFrame,
    df_t: pd.DataFrame,
    df_h: pd.DataFrame,
) -> List[CandleSignal]:
    """
    Rezonans: jednoczesny spadek ciśnienia + wzrost wilgotności → sygnał frontu.

    BUG 5 FIX: oryginał używał .get(t, 0) na Series z potencjalnie różnymi
    indeksami — Series.get() na Timestamp działa tylko gdy t jest dokładnie
    w indeksie; przy minimalnym przesunięciu (np. DST) milcząco zwraca 0.

    Fix: reindexujemy df_h do indeksu df_p przed obliczeniem delty.
    Dzięki temu porównanie odbywa się zawsze na tym samym zbiorze timestampów.
    """
    signals = []

    p_close = df_p["close"]
    p_delta = p_close.diff()

    # BUG 5 FIX: wyrównanie indeksów
    h_close = df_h["close"].reindex(df_p.index)
    h_delta = h_close.diff()

    for t in df_p.index[1:]:
        pd_v = p_delta.get(t, np.nan)
        hd_v = h_delta.get(t, np.nan)

        if pd.isna(pd_v) or pd.isna(hd_v):
            continue
        if pd_v < -1.5 and hd_v > 3.0:
            signals.append(CandleSignal(
                time=t,
                kind="resonance_front",
                strength=float(abs(pd_v) + hd_v),
                meta={"p_delta": float(pd_v), "h_delta": float(hd_v)},
            ))
    return signals


# ==========================
# 4. Λ–τ–ρ – meta-struktura
# ==========================

@dataclass
class LTROutput:
    lambda_struct: Dict
    tau_transform: Dict
    rho_defect:    Dict


def ltr_analysis(df: pd.DataFrame) -> LTROutput:
    """
    Λ – stabilność danych
    τ – charakter zmian ciśnienia
    ρ – miejsca defektu (nagłe skoki)
    """
    lambda_struct = {
        "rows":      len(df),
        "missing":   int(df.isna().sum().sum()),
        "stable":    bool(df.isna().sum().sum() == 0),
    }

    pressure = df["pressure"].values
    diffs    = np.diff(pressure)

    tau_transform = {
        "mean_diff": float(np.mean(diffs)),
        "std_diff":  float(np.std(diffs)),
        "max_diff":  float(np.max(diffs)),
        "min_diff":  float(np.min(diffs)),
    }

    defect_threshold = np.std(diffs) * 3
    defect_indices   = np.where(abs(diffs) > defect_threshold)[0]
    rho_defect = {
        "threshold": float(defect_threshold),
        "count":     int(len(defect_indices)),
        "times":     [str(df["datetime"].iloc[i + 1]) for i in defect_indices],
    }

    return LTROutput(
        lambda_struct=lambda_struct,
        tau_transform=tau_transform,
        rho_defect=rho_defect,
    )


# ==========================
# 5. Prognoza 48h – logika TIMDR
# ==========================

@dataclass
class Forecast48h:
    summary: str
    details: Dict


def forecast_48h(df: pd.DataFrame) -> Forecast48h:
    """
    Uproszczona prognoza 48h na podstawie sygnałów TIMDR.

    BUG 4 FIX: make_candles wywoływane z małymi literami ('12h' zamiast '12H').
    BUG 5 FIX: detect_resonance dostaje świece na tym samym freq ('12h').
    """
    # BUG 4 FIX: małe litery freq
    candles_p_12h = make_candles(df, "pressure", "12h")
    candles_t_4h  = make_candles(df, "temp",     "4h")
    candles_h_1h  = make_candles(df, "humidity", "1h")
    candles_h_12h = make_candles(df, "humidity", "12h")  # do resonance (ten sam freq co p)

    p_rev  = detect_trend_reversal(candles_p_12h, threshold=2.0)
    p_anom = detect_anomalies(candles_p_12h, sigma=2.0)
    t_mom  = detect_momentum(candles_t_4h, window=3, threshold=2.0)
    h_anom = detect_anomalies(candles_h_1h, sigma=2.0)

    # BUG 5 FIX: detect_resonance z wyrównanymi indeksami
    resonance = detect_resonance(candles_p_12h, candles_t_4h, candles_h_12h)

    stable_pressure = len(p_rev) == 0 and len(p_anom) == 0
    stable_humidity = len(h_anom) == 0
    warming         = any(sig.meta.get("delta", 0) > 0 for sig in t_mom)
    micro_front     = len(p_rev) == 1 and len(p_anom) <= 1
    front_resonance = len(resonance) > 0

    summary_parts = []
    if front_resonance:
        summary_parts.append("rezonans frontu wykryty — zmiana pogody w 12–36h")
    elif stable_pressure and stable_humidity:
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
        "pressure_signals":       [s.kind for s in p_rev + p_anom],
        "temp_momentum_count":    len(t_mom),
        "humidity_anomalies_count": len(h_anom),
        "resonance_count":        len(resonance),
        "stable_pressure":        stable_pressure,
        "stable_humidity":        stable_humidity,
        "warming":                warming,
        "micro_front":            micro_front,
        "front_resonance":        front_resonance,
    }

    return Forecast48h(summary=summary, details=details)


# ==========================
# 6. Główna funkcja synoptyka
# ==========================

def run_synoptyk(path: str) -> None:
    df  = load_imgw_csv(path)
    ltr = ltr_analysis(df)
    fc  = forecast_48h(df)

    print("=== SYNOPTYK / TIMDR / Λ–τ–ρ ===")
    print("Λ (struktura):", ltr.lambda_struct)
    print("τ (transformacja):", ltr.tau_transform)
    print("ρ (defekt):", ltr.rho_defect)
    print("\nPrognoza 48h (TIMDR):")
    print(fc.summary)
    print("Szczegóły:", fc.details)

    # BUG 7 FIX: obsługa brakującego modułu extensions.scoring
    try:
        from extensions.scoring import score_30_days
        print("\n=== SCORING 30 DNI ===")
        score = score_30_days(df)
        print("Fronty:",      f"{score.fronty:.1f}%")
        print("Opady:",       f"{score.opady:.1f}%")
        print("Temperatura:", f"{score.temperatura:.1f}%")
        print("Wiatr:",       f"{score.wiatr:.1f}%")
        print("Średnia:",     f"{score.srednia:.1f}%")
        print("Szczegóły:",   score.szczegoly)
    except ImportError:
        print("\n[INFO] Moduł extensions.scoring niedostępny — pomijam scoring 30 dni.")


if __name__ == "__main__":
    csv_path = "balice_30dni.csv"
    run_synoptyk(csv_path)
