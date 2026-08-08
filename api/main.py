from fastapi import FastAPI, HTTPException
from api.regions import REGIONS
from synoptyk.engine import SynoptykEngine   # dopasowane do repo
from synoptyk.data_sources.real_weather import fetch_real_weather
from synoptyk.data_sources.model_ecmwf import fetch_ecmwf
from synoptyk.data_sources.model_icon import fetch_icon
from synoptyk.compare import compare
from synoptyk.trend import trend

app = FastAPI(title="Synoptyk API v2.0")

@app.get("/api/regions")
def get_regions():
    return REGIONS

@app.get("/api/forecast")
def get_forecast(region: str):
    if region not in REGIONS:
        raise HTTPException(status_code=404, detail="Nieznany region")

    stations = REGIONS[region]

    results = {}

    for station in stations:
        lat, lon = SynoptykEngine.resolve_coords(station)

        real = fetch_real_weather(lat, lon)
        ecmwf = fetch_ecmwf(lat, lon)
        icon = fetch_icon(lat, lon)

        comp_ecmwf = compare(real, ecmwf)
        comp_icon = compare(real, icon)
        tr = trend(real)

        results[station] = {
            "trend": tr,
            "delta_ecmwf": comp_ecmwf[["ΔT", "ΔPrec", "ΔWind"]].mean().to_dict(),
            "delta_icon": comp_icon[["ΔT", "ΔPrec", "ΔWind"]].mean().to_dict()
        }

    return results
