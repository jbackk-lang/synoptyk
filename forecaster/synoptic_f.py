# forecaster/synoptic_f.py
"""
SYNOPTIC‑F – Model Prognozowania Strukturalnego.
Opiera się na figurze zjawiska wyciągniętej z danych historycznych.
"""

from .j_compress import j_compress
from .j_decompress import j_decompress
import pandas as pd
from datetime import datetime, timedelta

class SynopticF:
    def __init__(self, figure_window=7):
        """
        figure_window – długość okna danych (w dniach) używana do wyciągnięcia figury.
        Zasięg prognozy = figure_window.
        """
        self.figure_window = figure_window
    
    def _extract_figure(self, df: pd.DataFrame, param: str):
        """Wyciąga figurę zjawiska dla danego parametru."""
        data = df[param].dropna().tolist()
        if len(data) < self.figure_window:
            # Jeśli za mało danych – użyj wszystkich dostępnych
            window = data
        else:
            window = data[-self.figure_window:]
        
        mean, std = j_compress(window)
        return {
            'param': param,
            'window': window,
            'mean': mean,
            'std': std,
            'length': len(window)
        }
    
    def _generate_forecast(self, figure, steps):
        """Generuje prognozę na podstawie figury."""
        mean, std = figure['mean'], figure['std']
        # Prognoza = dekompresja figury na zadaną liczbę kroków
        return j_decompress(mean, std, steps)
    
    def predict(self, df: pd.DataFrame, horizon_days: int = None) -> dict:
        """
        Prognozuje dla wszystkich parametrów w DataFrame.
        Jeśli horizon_days nie jest podany, używa figure_window (zasada: zasięg = długość okna).
        """
        if horizon_days is None:
            horizon_days = self.figure_window
        
        # Parametry do prognozy
        params = ['temp', 'pressure', 'humidity', 'wind_speed']
        results = {}
        
        for param in params:
            if param not in df.columns:
                continue
            
            figure = self._extract_figure(df, param)
            forecast = self._generate_forecast(figure, horizon_days * 24)  # prognoza godzinowa
            
            # Generuj daty dla prognozy
            last_date = pd.to_datetime(df['datetime'].iloc[-1])
            forecast_dates = [last_date + timedelta(hours=i+1) for i in range(len(forecast))]
            
            results[param] = {
                'figure': figure,
                'forecast': forecast,
                'dates': forecast_dates,
                'horizon_days': horizon_days
            }
        
        return results
    
    def predict_daily(self, df: pd.DataFrame, horizon_days: int = None) -> dict:
        """
        Prognozuje w skali dziennej (agreguje prognozę godzinową do średnich dobowych).
        """
        results = self.predict(df, horizon_days)
        daily_results = {}
        
        for param, data in results.items():
            forecast = data['forecast']
            dates = data['dates']
            
            # Agreguj do dni
            daily_forecast = []
            daily_dates = []
            for i in range(0, len(forecast), 24):
                chunk = forecast[i:i+24]
                if chunk:
                    daily_forecast.append(sum(chunk) / len(chunk))
                    daily_dates.append(dates[i].date() if i < len(dates) else None)
            
            daily_results[param] = {
                'daily_forecast': daily_forecast,
                'dates': daily_dates,
                'horizon_days': len(daily_forecast)
            }
        
        return daily_results
