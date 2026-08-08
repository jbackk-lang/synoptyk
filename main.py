import os
import sys
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# Dodanie katalogu głównego do ścieżki systemowej
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from synoptyk_f import SynoptykFEngine
    from analyzer.timdr_analyzer import TIMDRAnalyzer
    from data.fetcher import WeatherFetcher
    from topomap_data import get_node_metadata, NODE_COORDS
    from grid_engine import SpatialGridEngine, get_region_bbox
except ImportError as e:
    print(f"[Ostrzeżenie API] Problem z importem modułów rdzennych: {e}")

app = FastAPI(
    title="Synoptyk-v2.0 TIMDR Weather API",
    description="Interfejs API dla prognoz pogodowych zintegrowany z silnikiem TIMDR i odszumianiem falkowym.",
    version="2.0.0"
)

class ForecastRequest(BaseModel):
    region: str = "poland_south"
    station: str = "Krakow_Centrum"
    days: int = 7

@app.get("/")
def read_root():
    return {
        "system": "Synoptyk-v2.0",
        "engine": "TIMDR Wavelet Analyzer",
        "status": "online"
    }

@app.get("/api/v1/forecast")
def get_forecast(
    station: str = Query("Krakow_Centrum", description="Nazwa węzła pomiarowego"),
    days: int = Query(7, ge=1, le=14, description="Liczba dni wstecz do analizy")
):
    try:
        if station not in NODE_COORDS:
            raise HTTPException(status_code=404, detail=f"Nie znaleziono stacji: {station}")
            
        lat, lon = NODE_COORDS[station]
        meta = get_node_metadata(station)

        # Pobieranie danych pogodowych
        fetcher = WeatherFetcher(lat=lat, lon=lon)
        df = fetcher.fetch_last_n_days(days)

        # Analiza TIMDR
        analyzer = TIMDRAnalyzer(station=station)
        timdr_results = analyzer.analyze(df)

        # Odszumianie i predykcja falkowa
        engine = SynoptykFEngine(wavelet="db4")
        result = engine.predict_temperature_timdr(
            df,
            uhi_factor=meta["uhi_factor"],
            topo_alt=meta["altitude"],
            timdr_results=timdr_results
        )

        return {
            "station": station,
            "altitude_m": meta["altitude"],
            "uhi_factor_c": meta["uhi_factor"],
            "forecast": {
                "point_temperature": round(result['point'], 2),
                "lower_bound": round(result['lower'], 2),
                "upper_bound": round(result['upper'], 2),
            },
            "timdr_analysis": result.get('timdr_note', 'Brak szczegółowych wykryć')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))