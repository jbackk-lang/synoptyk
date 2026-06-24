#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from urllib.error import URLError


def _fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def _geocode_city(city: str) -> tuple[float, float]:
    query = urllib.parse.urlencode({"name": city, "count": 1, "language": "pl"})
    payload = _fetch_json(f"https://geocoding-api.open-meteo.com/v1/search?{query}")
    results = payload.get("results") or []
    if not results:
        raise ValueError(f"Nie znaleziono miasta: {city}")
    first = results[0]
    return float(first["latitude"]), float(first["longitude"])


def get_forecast(city: str) -> str:
    latitude, longitude = _geocode_city(city)
    query = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "Europe/Warsaw",
            "forecast_days": 1,
        }
    )
    payload = _fetch_json(f"https://api.open-meteo.com/v1/forecast?{query}")
    daily = payload["daily"]
    date = daily["time"][0]
    temp_max = daily["temperature_2m_max"][0]
    temp_min = daily["temperature_2m_min"][0]
    rain = daily["precipitation_probability_max"][0]
    return (
        f"Prognoza pogody dla {city} ({date}): "
        f"min {temp_min}°C, max {temp_max}°C, opady {rain}%."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Pobierz prognozę pogody dla miasta.")
    parser.add_argument("city", help="Nazwa miasta, np. Warszawa")
    args = parser.parse_args()
    try:
        print(get_forecast(args.city))
        return 0
    except (ValueError, URLError) as exc:
        print(f"Błąd: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
