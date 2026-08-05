# analyzer/adaptive_thresholds.py
import pandas as pd
import numpy as np
from datetime import datetime
from data.cache import WeatherCache

class AdaptiveThresholds:
    def __init__(self, station="krakow_balice", db_path="weather_cache.db"):
        self.station = station
        self.cache = WeatherCache(db_path)
        self.climatology = self._load_climatology()
    
    def _load_climatology(self):
        """Ładuje normy wieloletnie z bazy."""
        query = f"""
            SELECT month, param, mean, std, p10, p90
            FROM climatology
            WHERE station = '{self.station}'
        """
        df = pd.read_sql_query(query, self.cache.conn)
        return df.set_index(['month', 'param'])
    
    def get_thresholds(self, dt: datetime, param: str) -> dict:
        """Zwraca progi dla danego dnia i parametru."""
        month = dt.month
        
        # Domyślnie – jeśli brak norm, używamy statystyk z ostatnich 30 dni
        row = self.climatology.loc[(month, param)] if (month, param) in self.climatology.index else None
        
        if row is not None:
            mean = row['mean']
            std = row['std']
            p10 = row['p10']
            p90 = row['p90']
        else:
            # Jeśli brak norm – użyj danych z ostatnich 30 dni (bufor)
            df_recent = self.cache.load_last_n_days(30)
            mean = df_recent[param].mean()
            std = df_recent[param].std()
            p10 = df_recent[param].quantile(0.1)
            p90 = df_recent[param].quantile(0.9)
        
        return {
            'mean': mean,
            'std': std,
            'low': mean - 2*std,      # anomalia niska
            'high': mean + 2*std,     # anomalia wysoka
            'p10': p10,
            'p90': p90,
            'threshold_skret': 1.5 * std,   # minimalna zmiana dla skrętu
            'threshold_defekt': 0.3 * (p90 - p10)  # nagły skok
        }
    
    def is_anomaly(self, value: float, dt: datetime, param: str) -> bool:
        """Sprawdza, czy wartość jest anomalna."""
        thresholds = self.get_thresholds(dt, param)
        return value > thresholds['high'] or value < thresholds['low']
    
    def is_defect(self, current: float, previous: float, dt: datetime, param: str) -> bool:
        """Sprawdza, czy skok jest defektem."""
        thresholds = self.get_thresholds(dt, param)
        return abs(current - previous) > thresholds['threshold_defekt']
    
    def is_trend_reversal(self, series: pd.Series, dt: datetime, param: str) -> bool:
        """Sprawdza, czy nastąpił skręt trendu."""
        if len(series) < 3:
            return False
        
        # Oblicz pochodną (zmiana między kolejnymi punktami)
        diff = series.diff()
        # Sprawdź, czy ostatnie dwie zmiany mają przeciwny znak
        if len(diff) >= 2 and diff.iloc[-1] is not None and diff.iloc[-2] is not None:
            sign_change = (diff.iloc[-1] > 0) != (diff.iloc[-2] > 0)
            thresholds = self.get_thresholds(dt, param)
            return sign_change and abs(diff.iloc[-1]) > thresholds['threshold_skret']
        return False
