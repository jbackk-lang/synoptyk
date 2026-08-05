# synoptyk.py – nowa wersja z modułami
import sys
import yaml
from data.fetcher import WeatherFetcher
from data.cache import WeatherCache
from analyzer.timdr_analyzer import TIMDRAnalyzer

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
    results = analyzer.analyze(df)
    
    # 4. Wyświetl wyniki
    print("\n📊 SYGNAŁY TIMDR:\n")
    print(f"🔹 Skręt: {len(results['skręt'])}")
    for item in results['skręt']:
        print(f"   - {item[0].strftime('%Y-%m-%d %H:%M')}: {item[1]} = {item[2]:.1f}")
    
    print(f"\n🔹 Anomalia: {len(results['anomalia'])}")
    for item in results['anomalia']:
        print(f"   - {item[0].strftime('%Y-%m-%d %H:%M')}: {item[1]} = {item[2]:.1f}")
    
    print(f"\n🔹 Rezonans: {len(results['rezonans'])}")
    for item in results['rezonans']:
        print(f"   - {item[0].strftime('%Y-%m-%d %H:%M')}: {', '.join(item[1])}")
    
    print(f"\n🔹 Defekt: {len(results['defekt'])}")
    for item in results['defekt']:
        print(f"   - {item[0].strftime('%Y-%m-%d %H:%M')}: {item[1]} = {item[2]:.1f}")
    
    cache.close()

if __name__ == "__main__":
    main()
