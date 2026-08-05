# synoptyk.py – nowa wersja z automatycznym pobieraniem danych
import sys
from data.fetcher import WeatherFetcher
from data.cache import WeatherCache

def main():
    # 1. Pobierz dane
    fetcher = WeatherFetcher()
    df = fetcher.fetch_last_n_days(7)
    
    # 2. Zapisz w cache
    cache = WeatherCache()
    cache.save(df)
    
    # 3. Wczytaj z cache (dla pewności)
    df_cached = cache.load("2026-07-28", "2026-08-04")
    
    # 4. Analiza TIMDR i Λ–τ–ρ (dotychczasowa logika)
    # ... (tu wstawiamy istniejący kod analizy)
    print("Dane pobrane i zbuforowane:", len(df_cached), "rekordów")
    cache.close()

if __name__ == "__main__":
    main()
