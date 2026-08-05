# synoptyk.py – z prognozowaniem SYNOPTIC‑F
import sys
import yaml
from data.fetcher import WeatherFetcher
from data.cache import WeatherCache
from analyzer.timdr_analyzer import TIMDRAnalyzer
from forecaster import SynopticF, ForecastValidator

def load_config():
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    
    # 1. Pobierz dane
    fetcher = WeatherFetcher(
        lat=config['stations']['krakow_balice']['lat'],
        lon=config['stations']['krakow_balice']['lon']
    )
    df = fetcher.fetch_last_n_days(config['analysis']['default_days'])
    
    # 2. Zapisz w cache
    cache = WeatherCache()
    cache.save(df)
    
    # 3. Analiza TIMDR
    analyzer = TIMDRAnalyzer(station="krakow_balice")
    timdr_results = analyzer.analyze(df)
    
    # 4. Prognoza SYNOPTIC‑F
    forecaster = SynopticF(figure_window=config['analysis']['figure_window'])
    forecast = forecaster.predict_daily(df, horizon_days=config['analysis']['forecast_horizon'])
    
    # 5. Wyświetl wyniki
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
        print(f"   - {item[0].strftime('%Y-%m-%d %H:%M')}: {item[1]} = {item[2]:.1f}")
    
    print("\n" + "="*60)
    print("🌤️ PROGNOZA SYNOPTIC‑F (kolejne 7 dni):\n")
    
    for param, data in forecast.items():
        values = data['daily_forecast']
        dates = data['dates']
        if values:
            print(f"🔹 {param.upper()}:")
            for i, (d, v) in enumerate(zip(dates[:7], values[:7])):
                print(f"   - {d}: {v:.1f}")
            print()
    
    cache.close()

if __name__ == "__main__":
    main()
