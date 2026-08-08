import argparse
import sys
import pandas as pd
import numpy as np
import gradio as gr

# Importy z Twojego środowiska synoptyk-v2.0
try:
    from grid_engine import SpatialGridEngine, get_region_bbox
    from synoptyk_f import SynoptykFEngine
    from topomap_data import TOPOGRAPHY_DATABASE, get_node_metadata, NODE_COORDS
    from data.fetcher import WeatherFetcher
    from analyzer.timdr_analyzer import TIMDRAnalyzer
except ImportError as e:
    print(f"Uwaga: Niektóre moduły lokalne nie są dostępne w ścieżce ({e}). "
          f"Upewnij się, że uruchamiasz skrypt z katalogu głównego repozytorium.")

# ============================================
# REGIONY I WEZŁY (Rozszerzone o USA & PL)
# ============================================
REGIONS = {
    "poland": ["Warszawa", "Krakow_Centrum", "Gdansk", "Wroclaw", "Poznan", "Szczecin"],
    "poland_south": ["Krakow_Centrum", "Tarnow", "Nowy_Sacz", "Zakopane", "Katowice", "Rzeszow", "Bielsko_Biala"],
    "poland_north": ["Gdansk", "Gdynia", "Sopot", "Suwalki", "Olsztyn", "Elblag", "Koszalin"],
    "poland_central": ["Warszawa", "Lodz", "Radom", "Plock", "Wloclawek", "Czestochowa"],
    "poland_west": ["Poznan", "Szczecin", "Zielona_Gora", "Gorzow_Wlkp", "Leszno", "Pila"],
    "poland_east": ["Lublin", "Bialystok", "Zamosc", "Przemysl", "Terespol", "Sandomierz"],
    "usa_northeast": ["New_York_City", "Boston", "Philadelphia", "Baltimore", "Hartford"],
    "usa_southeast": ["Miami", "Atlanta", "Charlotte", "Charleston", "Jacksonville"],
    "usa_midwest": ["Chicago", "Detroit", "Columbus", "Indianapolis", "Milwaukee"],
    "usa_south": ["Houston", "Dallas", "Austin", "San_Antonio", "New_Orleans"],
    "usa_west": ["Los_Angeles", "San_Francisco", "Seattle", "Portland_OR", "Las_Vegas"],
    "usa_mountains": ["Denver", "Salt_Lake_City", "Boise", "Billings", "Cheyenne"]
}

def resolve_nodes_for_region(region_key: str):
    """Pobiera listę węzłów dla wskazanego regionu."""
    region_key = region_key.lower()
    if region_key in REGIONS:
        data = REGIONS[region_key]
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return list(data.values())
    return REGIONS.get("poland_south", [])

def execute_timdr_simulation(region: str, days: int, grid_res: float, offline_demo: bool):
    """Główna funkcja analityczno-symulacyjna podłączona pod GUI."""
    summary_logs = []
    results_table = []
    chart_data = {}

    summary_logs.append(f"=== SYNOPTYK-F v2.0 (Silnik TIMDR) ===")
    summary_logs.append(f"Region: {region.upper()} | Okno: {days} dni | Siatka: {grid_res}°")

    # 1. Inicjalizacja siatki przestrzennej
    try:
        bbox = get_region_bbox(region)
        grid = SpatialGridEngine(bbox, grid_res).generate_mesh()
        summary_logs.append(f"Siatka przestrzenna wygenerowana: Kształt {grid['shape']}")
    except Exception as e:
        bbox = None
        summary_logs.append(f"Ostrzeżenie siatki: {e}")

    engine = SynoptykFEngine(wavelet="db4")
    nodes = resolve_nodes_for_region(region)

    for node in nodes:
        # Metadane i pozycjonowanie stacji
        try:
            meta = get_node_metadata(node)
            lat, lon = NODE_COORDS[node]
        except Exception:
            meta = {"altitude": 200, "uhi_factor": 1.2}
            lat, lon = 50.0, 20.0

        if offline_demo:
            results_table.append({
                "Stacja": node,
                "Wysokość (m)": meta["altitude"],
                "UHI Factor": meta["uhi_factor"],
                "Prognoza (°C)": "DEMO",
                "Przedział Niepewności": "[DEMO]",
                "Analiza TIMDR": "Tryb offline — symulacja bez API"
            })
            continue

        # Pobieranie realnych danych (Open-Meteo)
        try:
            fetcher = WeatherFetcher(lat=lat, lon=lon)
            df = fetcher.fetch_last_n_days(days)
        except Exception as e:
            summary_logs.append(f"Błąd pobierania danych dla {node}: {e}")
            continue

        # Analiza silnikiem TIMDR
        analyzer = TIMDRAnalyzer(station=node)
        timdr_results = analyzer.analyze(df)

        # Odszumianie falkowe + Predykcja UHI
        result = engine.predict_temperature_timdr(
            df,
            uhi_factor=meta["uhi_factor"],
            topo_alt=meta["altitude"],
            timdr_results=timdr_results
        )

        results_table.append({
            "Stacja": node,
            "Wysokość (m)": meta["altitude"],
            "UHI Factor": f"+{meta['uhi_factor']}°C",
            "Prognoza (°C)": round(result['point'], 2),
            "Przedział Niepewności": f"[{round(result['lower'], 2)} .. {round(result['upper'], 2)}]",
            "Analiza TIMDR": result['timdr_note']
        })

        if "temperature_2m" in df.columns:
            chart_data[node] = df["temperature_2m"].tolist()

    df_results = pd.DataFrame(results_table)
    log_output = "\n".join(summary_logs)
    
    return log_output, df_results

# ============================================
# INTERFEJS GRAFICZNY (Gradio)
# ============================================
def build_gui():
    theme = gr.themes.Soft(
        primary_hue="cyan",
        secondary_hue="slate",
        neutral_hue="slate"
    )

    with gr.Blocks(theme=theme, title="Synoptyk v2.0 - TIMDR Global Weather Engine") as app:
        gr.Markdown(
            """
            # 🌪️ Synoptyk v2.0 — Globalna Analiza Pogody
            ### Silnik TIMDR & Odszumianie Falkowe (SynoptykFEngine)
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ Parametry Symulacji")
                region_dropdown = gr.Dropdown(
                    choices=list(REGIONS.keys()),
                    value="poland_south",
                    label="Region Meteorologiczny"
                )
                days_slider = gr.Slider(
                    minimum=1, maximum=14, value=7, step=1,
                    label="Okno danych wejściowych (dni)"
                )
                grid_res_input = gr.Number(
                    value=0.125,
                    label="Krok siatki (°)"
                )
                offline_checkbox = gr.Checkbox(
                    value=False,
                    label="Tryb Offline (Demo)"
                )
                btn_run = gr.Button("🚀 Uruchom Analizę TIMDR", variant="primary")

            with gr.Column(scale=2):
                gr.Markdown("### 📊 Wyniki Analizy i Prognozy")
                logs_output = gr.Textbox(
                    label="Logi Silnika Synoptyk-F",
                    lines=4,
                    interactive=False
                )
                results_dataframe = gr.Dataframe(
                    label="Wskaźniki Stacji, Korekty UHI i Niepewność TIMDR",
                    interactive=False
                )

        btn_run.click(
            fn=execute_timdr_simulation,
            inputs=[region_dropdown, days_slider, grid_res_input, offline_checkbox],
            outputs=[logs_output, results_dataframe]
        )

    return app

if __name__ == "__main__":
    gui = build_gui()
    gui.launch(server_name="127.0.0.1", server_port=7860, share=False)
