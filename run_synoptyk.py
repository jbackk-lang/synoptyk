"""
Run Synoptyk – Skrypt wykonawczy, teraz faktycznie oparty o silnik TIMDR:
  1. pobiera realne dane (Open-Meteo) dla wybranego regionu,
  2. odpala TIMDRAnalyzer (skręt/anomalia/rezonans/defekt) na tych danych,
  3. odszumia szereg temperatury filtrem falkowym (SynoptykFEngine),
  4. liczy korektę UHI/wysokość ZASILONĄ sygnałami TIMDR (szersza
     niepewność i ostrzeżenie, jeśli TIMDR wykrył coś niestabilnego),
  zamiast wcześniejszego stałego base_temp=28.0 niezależnego od danych.
"""
import argparse
import sys

from grid_engine import SpatialGridEngine, get_region_bbox
from synoptyk_f import SynoptykFEngine
from topomap_data import TOPOGRAPHY_DATABASE, get_node_metadata
from data.fetcher import WeatherFetcher
from analyzer.timdr_analyzer import TIMDRAnalyzer

# Węzły dostępne per region — żeby nie próbować liczyć "Krakow_Center" dla USA
REGION_NODES = {
    "malopolska": ["Krakow_Center", "Tarnow", "Zakopane"],
    "poland": ["Krakow_Center", "Warszawa", "Tarnow"],
    "europe": ["Berlin", "Krakow_Center"],
    "usa_northeast": ["New_York_Manhattan", "Chicago"],
    "usa_west": ["Denver", "Phoenix", "Los_Angeles", "Seattle"],
    "usa": ["New_York_Manhattan", "Chicago", "Denver", "Phoenix", "Los_Angeles", "Miami", "Seattle"],
}

# Przybliżone lat/lon dla węzłów — do pobrania realnych danych pogodowych
NODE_COORDS = {
    "Krakow_Center": (50.06, 19.95),
    "Krakow_Balice": (50.08, 19.79),
    "Tarnow": (50.01, 20.99),
    "Zakopane": (49.30, 19.95),
    "Warszawa": (52.23, 21.01),
    "Berlin": (52.52, 13.41),
    "New_York_Manhattan": (40.78, -73.97),
    "Chicago": (41.88, -87.63),
    "Denver": (39.74, -104.99),
    "Phoenix": (33.45, -112.07),
    "Los_Angeles": (34.05, -118.24),
    "Miami": (25.76, -80.19),
    "Seattle": (47.61, -122.33),
}


def run_simulation(region: str, days: int, grid_res: float, offline_demo: bool = False):
    print("=== Uruchamianie SYNOPTYK-F (zintegrowany z TIMDR) ===")
    print(f"Region: {region.upper()} | Dni: {days} | Siatka: {grid_res}°")

    try:
        bbox = get_region_bbox(region)
    except ValueError as e:
        print(f"BŁĄD: {e}")
        sys.exit(1)

    grid = SpatialGridEngine(bbox, grid_res).generate_mesh()
    engine = SynoptykFEngine(wavelet="db4")
    print(f"Wygenerowano siatkę o wymiarach: {grid['shape']}")

    nodes = REGION_NODES.get(region.lower())
    if not nodes:
        print(f"BŁĄD: brak zdefiniowanych węzłów pomiarowych dla regionu {region!r}.")
        sys.exit(1)

    print("\n--- Wybrane punkty węzłowe ---")
    for node in nodes:
        meta = get_node_metadata(node)
        lat, lon = NODE_COORDS[node]

        if offline_demo:
            print(f"Stacja: {node:<20} | [DEMO offline — brak realnych danych]")
            continue

        try:
            fetcher = WeatherFetcher(lat=lat, lon=lon)
            df = fetcher.fetch_last_n_days(days)
        except Exception as e:
            print(f"Stacja: {node:<20} | BŁĄD pobierania danych: {e}")
            continue

        analyzer = TIMDRAnalyzer(station=node)
        timdr_results = analyzer.analyze(df)

        result = engine.predict_temperature_timdr(
            df, uhi_factor=meta["uhi_factor"], topo_alt=meta["altitude"],
            timdr_results=timdr_results,
        )
        print(
            f"Stacja: {node:<20} | Alt: {meta['altitude']}m | UHI: +{meta['uhi_factor']}°C | "
            f"Prognoza: {result['point']}°C [{result['lower']} .. {result['upper']}] | {result['timdr_note']}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Synoptyk-F Weather Engine (TIMDR-integrated)")
    parser.add_argument("--region", type=str, default="malopolska",
                         help="Region: malopolska, poland, europe, usa, usa_northeast, usa_west")
    parser.add_argument("--days", type=int, default=7, help="Okno danych wejściowych w dniach")
    parser.add_argument("--grid", type=float, default=0.125, help="Krok siatki w stopniach")
    parser.add_argument("--offline-demo", action="store_true",
                         help="Pokaż tylko strukturę (siatka + węzły) bez pobierania danych na żywo")

    args = parser.parse_args()
    run_simulation(args.region, args.days, args.grid, offline_demo=args.offline_demo)
