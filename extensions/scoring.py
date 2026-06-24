# extensions/scoring.py
# Moduł rozszerzający SYNOPTYK o scoring 30-dniowy

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List

from synoptyk import (
    make_candles,
    detect_trend_reversal,
    detect_anomalies,
    detect_momentum,
)


@dataclass
class ScoreResult:
    fronty: float
    opady: float
    temperatura: float
    wiatr: float
    srednia: float
    szczegoly: Dict


def score_30_days(df: pd.DataFrame) -> ScoreResult:
    """
    Liczy skuteczność SYNOPTYKA na 30 dniach danych.
    Porównuje sygnały TIMDR z rzeczywistymi zdarzeniami pogodowymi.
    """

    # ============================
    # 1. FRONTY (ciśnienie 12h)
    # ============================
    candles_p = make_candles(df, "pressure", "12H")
    rev_p = detect_trend_reversal(candles_p, threshold=2.0)

    # rzeczywiste fronty = duże zmiany ciśnienia
    diffs = candles_p["close"].diff().abs()
    real_fronts = diffs[diffs > 4.0]  # >4 hPa w 12h = front
    real_front_count = len(real_fronts)
    detected_front_count = len(rev_p)

    front_score = (
        min(detected_front_count, real_front_count) / max(real_front_count, 1)
    ) * 100

    # ============================
    # 2. OPADY (wilgotność 1h)
    # ============================
    candles_h = make_candles(df, "humidity", "1H")
    anom_h = detect_anomalies(candles_h, sigma=2.0)

    # rzeczywiste opady = wzrost wilgotności + precip > 0
    real_rain = df[df["precip"] > 0]
    real_rain_count = len(real_rain)

    detected_rain_count = len(anom_h)

    opady_score = (
        min(detected_rain_count, real_rain_count) / max(real_rain_count, 1)
    ) * 100

    # ============================
    # 3. TEMPERATURA (4h)
    # ============================
    candles_t = make_candles(df, "temp", "4H")
    mom_t = detect_momentum(candles_t, window=3, threshold=2.0)

    # rzeczywiste anomalie temperatury
    real_temp_delta = candles_t["close"].diff().abs()
    real_temp_events = real_temp_delta[real_temp_delta > 2.0]
    real_temp_count = len(real_temp_events)

    detected_temp_count = len(mom_t)

    temp_score = (
        min(detected_temp_count, real_temp_count) / max(real_temp_count, 1)
    ) * 100

    # ============================
    # 4. WIATR (skoki prędkości)
    # ============================
    wind_delta = df["wind_speed"].diff().abs()
    real_wind_events = wind_delta[wind_delta > 4.0]  # skok >4 m/s
    real_wind_count = len(real_wind_events)

    # wykrywanie skoków jako anomalie
    df_w = df.copy()
    df_w["wind"] = df["wind_speed"]
    candles_w = make_candles(df_w, "wind", "1H")
    anom_w = detect_anomalies(candles_w, sigma=2.0)
    detected_wind_count = len(anom_w)

    wind_score = (
        min(detected_wind_count, real_wind_count) / max(real_wind_count, 1)
    ) * 100

    # ============================
    # 5. ŚREDNIA
    # ============================
    avg_score = np.mean([front_score, opady_score, temp_score, wind_score])

    return ScoreResult(
        fronty=front_score,
        opady=opady_score,
        temperatura=temp_score,
        wiatr=wind_score,
        srednia=avg_score,
        szczegoly={
            "fronty_real": real_front_count,
            "fronty_detected": detected_front_count,
            "opady_real": real_rain_count,
            "opady_detected": detected_rain_count,
            "temp_real": real_temp_count,
            "temp_detected": detected_temp_count,
            "wiatr_real": real_wind_count,
            "wiatr_detected": detected_wind_count,
        },
    )
