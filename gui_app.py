import sys
import os
import pandas as pd
import gradio as gr

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from grid_engine import SpatialGridEngine, get_region_bbox
from synoptyk_f import SynoptykFEngine
from topomap_data import TOPOGRAPHY_DATABASE, get_node_metadata
from data.fetcher import WeatherFetcher
from analyzer.timdr_analyzer import TIMDRAnalyzer

# Mapa regionów
REGIONS_MAP = {
    "cała_polska": [
        "Warszawa", "Krakow_Centrum", "Gdansk", "Wroclaw", "Poznan", "Lodz", "Szczecin", 
        "Bydgoszcz", "Lublin", "Bialystok", "Katowice", "Gdynia", "Czestochowa", 
        "Radom", "Rzeszow", "Torun", "Kielce", "Olsztyn", "Bielsko_Biala", 
        "Zielona_Gora", "Opole", "Gorzow_Wlkp", "Elblag", "Plock", "Tarnow", 
        "Koszalin", "Kalisz", "Legnica", "Nowy_Sacz", "Siedlce", "Suwalki", "Zakopane"
    ],
    "poland_south": ["Krakow_Centrum", "Tarnow", "Nowy_Sacz", "Zakopane", "Katowice", "Rzeszow", "Bielsko_Biala", "Opole"],
    "poland_north": ["Gdansk", "Gdynia", "Sopot", "Suwalki", "Olsztyn", "Elblag", "Koszalin", "Szczecin"],
    "poland_central": ["Warszawa", "Lodz", "Radom", "Plock", "Wloclawek", "Czestochowa", "Kielce"],
    "poland_west": ["Poznan", "Wroclaw", "Szczecin", "Zielona_Gora", "Gorzow_Wlkp", "Leszno", "Pila"],
    "poland_east": ["Lublin", "Bialystok", "Zamosc", "Przemysl", "Terespol", "Sandomierz", "Siedlce"],
    "usa_northeast": ["New_York_City", "Boston", "Philadelphia", "Baltimore", "Hartford"],
    "usa_west": ["Los_Angeles", "San_Francisco", "Seattle", "Portland_OR", "Las_Vegas"]
}

# Pełna lista miast w Polsce dostępnych w bazie i rozszerzonych
POLISH_CITIES = sorted(list(set(
    list(TOPOGRAPHY_DATABASE.keys()) + [
        "Warszawa", "Krakow_Centrum", "Gdansk", "Wroclaw", "Poznan", "Lodz", "Szczecin", 
        "Bydgoszcz", "Lublin", "Bialystok", "Katowice", "Gdynia", "Czestochowa", 
        "Radom", "Rzeszow", "Torun", "Kielce", "Olsztyn", "Bielsko_Biala", 
        "Zielona_Gora", "Opole", "Gorzow_Wlkp", "Elblag", "Plock", "Tarnow", 
        "Koszalin", "Kalisz", "Legnica", "Nowy_Sacz", "Siedlce", "Suwalki", "Zakopane",
        "Zamosc", "Przemysl", "Sandomierz", "Terespol", "Wloclawek", "Sopot", "Gdynia"
    ]
)))

def get_coords(node_name: str):
    """Pobiera współrzędne geograficzne stacji/miasta."""
    if node_name in TOPOGRAPHY_DATABASE:
        d = TOPOGRAPHY_DATABASE[node_name]
        return d.get("lat", 50.0), d.get("lon", 20.0)
    meta = get_node_metadata(node_name)
    return meta.get("lat", 50.0), meta.get("lon", 20.0)

def run_gui_simulation(mode: str, selected_region: str, selected_city: str, days: int, grid_res: float, offline_demo: bool):
    logs = []
    results = []

    if mode == "Pojedyncze miasto":
        nodes = [selected_city]
        logs.append(f"=== Uruchomiono Synoptyk-F dla miasta: {selected_city} ===")
    else:
        reg_key = selected_region.lower()
        nodes = REGIONS_MAP.get(reg_key, REGIONS_MAP["poland_south"])
        logs.append(f"=== Uruchomiono Synoptyk-F dla regionu: {selected_region.upper()} ===")

    logs.append(f"Dni: {days} | Siatka: {grid_res}° | Liczba wybranych stacji: {len(nodes)}")

    if mode != "Pojedyncze miasto":
        try:
            bbox_region = "poland" if selected_region == "cała_polska" else selected_region
            bbox = get_region_bbox(bbox_region)
            grid = SpatialGridEngine(bbox, grid_res).generate_mesh()
            logs.append(f"Wygenerowano siatkę przestrzenną: {grid['shape']}")
        except Exception as e:
            logs.append(f"Uwaga siatki: {e}")

    engine = SynoptykFEngine(wavelet="db4")

    for node in nodes:
        meta = get_node_metadata(node)
        lat, lon = get_coords(node)

        if offline_demo:
            results.append({
                "Stacja / Miasto": node,
                "Szerokość (Lat)": lat,
                "Długość (Lon)": lon,
                "Wysokość": f"{meta.get('altitude', 200)}m",
                "UHI": f"+{meta.get('uhi_factor', 1.0)}°C",
                "Prognoza": "DEMO",
                "Przedział": "[DEMO]",
                "Status TIMDR": "Tryb offline"
            })
            continue

        try:
            fetcher = WeatherFetcher(lat=lat, lon=lon)
            df = fetcher.fetch_last_n_days(days)
            analyzer = TIMDRAnalyzer(station=node)
            timdr_results = analyzer.analyze(df)

            res = engine.predict_temperature_timdr(
                df, uhi_factor=meta.get("uhi_factor", 1.0), topo_alt=meta.get("altitude", 200),
                timdr_results=timdr_results
            )

            results.append({
                "Stacja / Miasto": node,
                "Szerokość (Lat)": lat,
                "Długość (Lon)": lon,
                "Wysokość": f"{meta.get('altitude', 200)}m",
                "UHI": f"+{meta.get('uhi_factor', 1.0)}°C",
                "Prognoza": f"{round(res['point'], 2)}°C",
                "Przedział": f"[{round(res['lower'], 2)} .. {round(res['upper'], 2)}]",
                "Status TIMDR": res.get('timdr_note', 'OK')
            })
        except Exception as e:
            logs.append(f"Błąd przetwarzania miasta {node}: {e}")

    return "\n".join(logs), pd.DataFrame(results)

def update_visibility(mode):
    if mode == "Pojedyncze miasto":
        return gr.update(visible=False), gr.update(visible=True)
    else:
        return gr.update(visible=True), gr.update(visible=False)

def create_app():
    theme = gr.themes.Soft(primary_hue="cyan", neutral_hue="slate")
    with gr.Blocks(theme=theme, title="Synoptyk-v2.0 TIMDR") as demo:
        gr.Markdown("# 🌪️ Synoptyk-v2.0 — Analiza Pogodowa i Wybór Miast w Polsce")
        
        with gr.Row():
            with gr.Column(scale=1):
                mode = gr.Radio(
                    choices=["Cały Region", "Pojedyncze miasto"],
                    value="Cały Region",
                    label="Tryb analizy"
                )
                
                region = gr.Dropdown(
                    choices=list(REGIONS_MAP.keys()),
                    value="poland_south",
                    label="Wybierz Region",
                    visible=True
                )
                
                city = gr.Dropdown(
                    choices=POLISH_CITIES,
                    value="Krakow_Centrum",
                    label="Wybierz Miasto w Polsce",
                    visible=False
                )
                
                days = gr.Slider(minimum=1, maximum=14, value=7, step=1, label="Dni danych (okno)")
                grid_res = gr.Number(value=0.125, label="Rozdzielczość siatki (°)")
                offline = gr.Checkbox(value=False, label="Tryb Offline (Demo)")
                btn = gr.Button("Uruchom Analizę", variant="primary")
            
            with gr.Column(scale=2):
                logs = gr.Textbox(label="Dziennik Zdarzeń Silnika", lines=5)
                table = gr.Dataframe(label="Wyniki Analizy Falkowej & TIMDR")

        mode.change(
            fn=update_visibility,
            inputs=[mode],
            outputs=[region, city]
        )

        btn.click(
            fn=run_gui_simulation,
            inputs=[mode, region, city, days, grid_res, offline],
            outputs=[logs, table]
        )

    return demo

if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="127.0.0.1", server_port=7860)