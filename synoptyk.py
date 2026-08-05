# synoptyk.py
import sys
import yaml
from data.fetcher import WeatherFetcher
from data.cache import WeatherCache
from analyzer.timdr_analyzer import TIMDRAnalyzer
from analyzer.wind_analyzer import WindAnalyzer
from forecaster import SynopticF

def load_config():
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    
    fetcher = WeatherFetcher(
        lat=config['stations']['krakow_balice']['lat'],
        lon=config['stations']['krakow_balice']['lon']
    )
    df = fetcher.fetch_last_n_days(config['analysis']['default_days'])
    
    cache = WeatherCache()
    cache.save(df)
    
    analyzer = TIMDRAnalyzer(station="krakow_balice")
    timdr_results = analyzer.analyze(df)
    
    forecaster = SynopticF(figure_window=config['analysis']['figure_window'])
    forecast = forecaster.predict_daily(df, horizon_days=config['analysis']['forecast_horizon'])
    
    wind = WindAnalyzer(df)
    avg_dir = wind.average_direction(24)
    avg_speed = wind.average_speed(24)
    sudden = wind.sudden_direction_change()
    front = wind.detect_front()
    
    print("\n" + "="*60)
    print("📊 SYGNAŁY TIMDR:\n")
    print(f"🔹 Skręt: {len(timdr_results['skręt'])}")
    for item in timdr_results['skręt'][:5]:
        print(f"   - {item[0].strftime('%Y-%m-%d %H:%M')}: {item[1]} = {item[2]:.1f}")
    
    print(f"\n🔹 Anomalia: {len(timdr_results['anomalia'])}")
    for item in timdr_results['anomalia'][:5]:
        print(f"   - {item[0].strftime('%Y-%m-%d %H:%M')}: {item[1]} = {item[2]:.1f}")
    
    print(f"\n🔹 Rezonans: {len(timdr_results['rezonans'])}")
    for item in timdr_results['rezonans'][:5]:
        print(f"   - {item[0].strftime('%Y-%m-%d %H:%M')}: {', '.join(item[1])}")
    
    print(f"\n🔹 Defekt: {len(timdr_results['defekt'])}")
    for item in timdr_results['defekt'][:5]:
        print(f"   - {item[0].strftime('%Y-%m-%d %H:%M')}: {item[1]} = {item[2] if len(item) > 2 else 'WIND_DIR'}")
    
    print("\n" + "="*60)
    print("🌬️ ANALIZA WIATRU (24h):")
    print(f"   Średnia prędkość: {avg_speed:.1f} m/s")
    print(f"   Średni kierunek: {avg_dir:.1f}°")
    print(f"   Nagła zmiana kierunku: {'TAK' if sudden else 'NIE'}")
    print(f"   Front: {front['type'] if front['front'] else 'brak'}")
    
    print("\n" + "="*60)
    print("🌤️ PROGNOZA SYNOPTIC‑F (kolejne 7 dni):\n")
    for param, data in forecast.items():
        values = data['daily_forecast']
        dates = data['dates']
        if values:
            print(f"🔹 {param.upper()}:")
            for i
