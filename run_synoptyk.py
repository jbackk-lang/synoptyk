"""
Run Synoptyk – Skrypt wykonawczy symulacji
"""

import argparse
from grid_engine import SpatialGridEngine, get_region_bbox
from synoptyk_f import SynoptykFEngine
from topomap_data import TOPOGRAPHY_DATABASE, get_node_metadata


def run_simulation(region: str, days: int, grid_res: float):
    print(f"=== Uruchamianie SYNOPTYK-F ===")
    print(f"Region: {region.upper()} | Dni: {days} | Siatka: {grid_res}°")

    bbox = get_region_bbox(region)
    grid = SpatialGridEngine(bbox, grid_res).generate_mesh()
    engine = SynoptykFEngine(wavelet="db4")

    print(f"Wygenerowano siatkę o wymiarach: {grid['shape']}")

    # Przykładowa symulacja punktowa dla węzłów
    print("\n--- Wybrane punkty węzłowe ---")
    base_temp = 28.0
    for node in ["Krakow_Center", "Tarnow", "Zakopane"]:
        meta = get_node_metadata(node)
        pred_temp = engine.predict_temperature_step(
            base_temp, meta["uhi_factor"], meta["altitude"]
        )
        print(
            f"Stacja: {node:<15} | Alt: {meta['altitude']}m | UHI: +{meta['uhi_factor']}°C | Prognoza: {pred_temp}°C"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Synoptyk-F Weather Engine"
    )
    parser.add_argument(
        "--region", type=str, default="malopolska", help="Region symulacji"
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Horyzont czasowy w dniach"
    )
    parser.add_argument(
        "--grid", type=float, default=0.125, help="Krok siatki w stopniach"
    )

    args = parser.parse_args()
    run_simulation(args.region, args.days, args.grid)