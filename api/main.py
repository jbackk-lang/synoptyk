# api/main.py
"""
FastAPI dla synoptyk – udostępnia analizę TIMDR i prognozę SYNOPTIC‑F.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
from datetime import datetime, timedelta

from data.fetcher import WeatherFetcher
from data.cache import WeatherCache
from analyzer.timdr_analyzer import TIMDRAnalyzer
from forecaster import SynopticF, ForecastValidator

# ------------------ INICJALIZACJA ------------------
app = FastAPI(
    title="SYNOPTYK API",
    description="Analiza TIMDR i prognoza SYNOPTIC‑F dla danych meteorologicznych",
    version="2.0"
)

# CORS – pozwala na dostęp z front-endu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ MODELE DANYCH ------------------
class FetchRequest(BaseModel):
    station: str = "krakow_balice"
    days: int = 7

class ForecastRequest(BaseModel):
    station: str = "krakow_balice"
    days: int = 7
    horizon_days: int = 7

class AnalyzeRequest(BaseModel):
    station: str = "krakow_balice"
    days: int = 7

# ------------------ FUNKCJE POMOCNICZE ------------------
def get_station_coords(station: str):
    """Zwraca współrzędne stacji na podstawie nazwy."""
    stations = {
        "krakow_balice": {"lat": 50.083, "lon": 19.917},
        "warszawa": {"lat": 52.237, "lon": 21.017},
        "gdansk": {"lat": 54.352, "lon": 18.646},
        "wroclaw": {"lat": 51.107, "lon": 17.038},
        "poznan": {"lat": 52.406, "lon": 16.925},
        "katowice": {"lat": 50.258, "lon": 19.028}
    }
    if station not in stations:
        raise ValueError(f"Nieznana stacja: {station}. Dostępne: {list(stations.keys())}")
    return stations[station]

def fetch_data(station: str, days: int) -> pd.DataFrame:
    """Pobiera dane dla stacji i liczby dni."""
    coords = get_station_coords(station)
    fetcher = WeatherFetcher(lat=coords["lat"], lon=coords["lon"])
    df = fetcher.fetch_last_n_days(days)
    
    # Zapisz w cache
    cache = WeatherCache()
    cache.save(df)
    cache.close()
    
    return df

# ------------------ ENDPOINTY ------------------
@app.get("/")
def root():
    return {
        "message": "SYNOPTYK API",
        "version": "2.0",
        "endpoints": {
            "/": "Informacje o API",
            "/health": "Status API",
            "/fetch": "Pobierz dane dla stacji",
            "/analyze": "Analiza TIMDR",
            "/forecast": "Prognoza SYNOPTIC‑F",
            "/full": "Pełna analiza (TIMDR + prognoza)",
            "/stations": "Lista dostępnych stacji"
        }
    }

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/stations")
def list_stations():
    """Zwraca listę dostępnych stacji ze współrzędnymi."""
    return {
        "stations": {
            "krakow_balice": {"lat": 50.083, "lon": 19.917, "name": "Kraków-Balice"},
            "warszawa": {"lat": 52.237, "lon": 21.017, "name": "Warszawa"},
            "gdansk": {"lat": 54.352, "lon": 18.646, "name": "Gdańsk"},
            "wroclaw": {"lat": 51.107, "lon": 17.038, "name": "Wrocław"},
            "poznan": {"lat": 52.406, "lon": 16.925, "name": "Poznań"},
            "katowice": {"lat": 50.258, "lon": 19.028, "name": "Katowice"}
        }
    }

@app.post("/fetch")
def fetch_endpoint(request: FetchRequest):
    """Pobiera dane dla podanej stacji i liczby dni."""
    try:
        df = fetch_data(request.station, request.days)
        return {
            "status": "success",
            "station": request.station,
            "days": request.days,
            "records": len(df),
            "columns": list(df.columns),
            "last_date": df["datetime"].iloc[-1] if not df.empty else None,
            "sample": df.head(5).to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analyze")
def analyze_endpoint(request: AnalyzeRequest):
    """Przeprowadza analizę TIMDR dla podanej stacji."""
    try:
        df = fetch_data(request.station, request.days)
        analyzer = TIMDRAnalyzer(station=request.station)
        results = analyzer.analyze(df)
        
        # Konwersja do formatu JSON (datetime → string)
        for key in results:
            results[key] = [
                {
                    "time": item[0].isoformat(),
                    "param": item[1],
                    "value": item[2] if len(item) > 2 else None,
                    "params": item[1] if len(item) > 2 and isinstance(item[1], list) else None
                }
                for item in results[key]
            ]
        
        return {
            "status": "success",
            "station": request.station,
            "days": request.days,
            "signals": results,
            "summary": {
                "skret": len(results["skręt"]),
                "anomalia": len(results["anomalia"]),
                "rezonans": len(results["rezonans"]),
                "defekt": len(results["defekt"])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/forecast")
def forecast_endpoint(request: ForecastRequest):
    """Generuje prognozę SYNOPTIC‑F dla podanej stacji."""
    try:
        df = fetch_data(request.station, request.days)
        forecaster = SynopticF(figure_window=request.days)
        forecast = forecaster.predict_daily(df, horizon_days=request.horizon_days)
        
        # Konwersja do formatu JSON
        result = {}
        for param, data in forecast.items():
            result[param] = {
                "daily_forecast": data["daily_forecast"],
                "dates": [str(d) for d in data["dates"]],
                "horizon_days": data["horizon_days"]
            }
        
        return {
            "status": "success",
            "station": request.station,
            "days": request.days,
            "horizon_days": request.horizon_days,
            "forecast": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/full")
def full_analysis(request: FetchRequest):
    """Pełna analiza: TIMDR + prognoza SYNOPTIC‑F."""
    try:
        df = fetch_data(request.station, request.days)
        
        # 1. Analiza TIMDR
        analyzer = TIMDRAnalyzer(station=request.station)
        timdr_results = analyzer.analyze(df)
        
        # 2. Prognoza SYNOPTIC‑F
        forecaster = SynopticF(figure_window=request.days)
        forecast = forecaster.predict_daily(df, horizon_days=request.days)
        
        # 3. Przygotowanie odpowiedzi
        timdr_json = {}
        for key in timdr_results:
            timdr_json[key] = [
                {
                    "time": item[0].isoformat(),
                    "param": item[1],
                    "value": item[2] if len(item) > 2 else None
                }
                for item in timdr_results[key]
            ]
        
        forecast_json = {}
        for param, data in forecast.items():
            forecast_json[param] = {
                "daily_forecast": data["daily_forecast"],
                "dates": [str(d) for d in data["dates"]],
                "horizon_days": data["horizon_days"]
            }
        
        return {
            "status": "success",
            "station": request.station,
            "days": request.days,
            "timdr": {
                "signals": timdr_json,
                "summary": {
                    "skret": len(timdr_results["skręt"]),
                    "anomalia": len(timdr_results["anomalia"]),
                    "rezonans": len(timdr_results["rezonans"]),
                    "defekt": len(timdr_results["defekt"])
                }
            },
            "forecast": forecast_json
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ------------------ URUCHOMIENIE (dla testów) ------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
