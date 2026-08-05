# api/main.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import pandas as pd

from data.fetcher import WeatherFetcher
from data.cache import WeatherCache
from analyzer.timdr_analyzer import TIMDRAnalyzer
from analyzer.wind_analyzer import WindAnalyzer
from forecaster import SynopticF

app = FastAPI(title="SYNOPTYK API", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class FetchRequest(BaseModel):
    station: str = "krakow_balice"
    days: int = 7

def get_station_coords(station: str):
    stations = {
        "krakow_balice": {"lat": 50.083, "lon": 19.917},
        "warszawa": {"lat": 52.237, "lon": 21.017},
        "gdansk": {"lat": 54.352, "lon": 18.646},
        "wroclaw": {"lat": 51.107, "lon": 17.038},
        "poznan": {"lat": 52.406, "lon": 16.925},
        "katowice": {"lat": 50.258, "lon": 19.028}
    }
    if station not in stations:
        raise ValueError(f"Nieznana stacja: {station}")
    return stations[station]

def fetch_data(station: str, days: int) -> pd.DataFrame:
    coords = get_station_coords(station)
    fetcher = WeatherFetcher(lat=coords["lat"], lon=coords["lon"])
    return fetcher.fetch_last_n_days(days)

@app.get("/")
def root():
    return {"message": "SYNOPTYK API", "version": "2.0"}

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/stations")
def list_stations():
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
def analyze_endpoint(request: FetchRequest):
    try:
        df = fetch_data(request.station, request.days)
        analyzer = TIMDRAnalyzer(station=request.station)
        results = analyzer.analyze(df)
        for key in results:
            results[key] = [
                {"time": item[0].isoformat(), "param": item[1], "value": item[2] if len(item) > 2 else None}
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
def forecast_endpoint(request: FetchRequest):
    try:
        df = fetch_data(request.station, request.days)
        forecaster = SynopticF(figure_window=request.days)
        forecast = forecaster.predict_daily(df, horizon_days=request.days)
        result = {}
        for param, data in forecast.items():
            result[param] = {
                "daily_forecast": data["daily_forecast"],
                "dates": [str(d) for d in data["dates"]],
                "horizon_days": data["horizon_days"]
            }
        return {"status": "success", "station": request.station, "days": request.days, "forecast": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/wind")
def wind_analysis(request: FetchRequest):
    try:
        df = fetch_data(request.station, request.days)
        wind = WindAnalyzer(df)
        return {
            "status": "success",
            "station": request.station,
            "days": request.days,
            "wind": {
                "avg_speed": wind.average_speed(),
                "avg_direction": wind.average_direction(),
                "sudden_change": wind.sudden_direction_change(),
                "front_detected": wind.detect_front(),
                "wind_rose": wind.wind_rose_data().to_dict()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/full")
def full_analysis(request: FetchRequest):
    try:
        df = fetch_data(request.station, request.days)
        analyzer = TIMDRAnalyzer(station=request.station)
        timdr_results = analyzer.analyze(df)
        forecaster = SynopticF(figure_window=request.days)
        forecast = forecaster.predict_daily(df, horizon_days=request.days)
        timdr_json = {}
        for key in timdr_results:
            timdr_json[key] = [
                {"time": item[0].isoformat(), "param": item[1], "value": item[2] if len(item) > 2 else None}
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
