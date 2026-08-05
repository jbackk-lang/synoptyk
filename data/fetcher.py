# data/fetcher.py
import requests
import pandas as pd
from datetime import datetime, timedelta

class WeatherFetcher:
    def __init__(self, lat=50.083, lon=19.917):  # domyślnie Kraków-Balice
        self.lat = lat
        self.lon = lon
        self.base_url = "https://archive-api.open-meteo.com/v1/archive"
    
    def fetch_hourly(self, start_date: str, end_date: str):
        """
        Pobiera dane godzinowe z Open-Meteo.
        start_date, end_date: 'YYYY-MM-DD'
        """
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,pressure_msl,wind_speed_10m,wind_direction_10m",
            "timezone": "Europe/Warsaw"
        }
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        if "hourly" not in data:
            raise ValueError("Błąd pobierania danych: brak klucza 'hourly'")
        
        # Konwersja do DataFrame
        df = pd.DataFrame({
            "datetime": data["hourly"]["time"],
            "temp": data["hourly"]["temperature_2m"],
            "pressure": data["hourly"]["pressure_msl"],
            "humidity": data["hourly"]["relative_humidity_2m"],
            "wind_speed": data["hourly"]["wind_speed_10m"],
            "wind_dir": data["hourly"]["wind_direction_10m"],
            "precip": data["hourly"]["precipitation"]
        })
        return df

    def fetch_last_n_days(self, n=7):
        """Pobiera ostatnie n dni (do dzisiaj)."""
        end = datetime.now()
        start = end - timedelta(days=n)
        return self.fetch_hourly(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
