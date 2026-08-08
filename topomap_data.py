"""
Topomap Data Module – Baza ukształtowania terenu i Miejscowych Wysp Ciepła (UHI)

UWAGA O ŹRÓDLE DANYCH: wysokości n.p.m. poniżej są przybliżone (dane
publiczne, zaokrąglone). Wskaźniki UHI (Urban Heat Island) są orientacyjne
i NIE pochodzą z pomiarów — to szacunki rzędu wielkości na podstawie
wielkości miasta i gęstości zabudowy, do czasu podłączenia realnego źródła
(np. lokalnych stacji miejskich vs. podmiejskich). Nie traktować jako
zwalidowanych wartości pomiarowych.
"""

from typing import Dict, Tuple


# Słownik stacji/węzłów: (wysokość n.p.m. w metrach, wskaźnik UHI w °C)
TOPOGRAPHY_DATABASE: Dict[str, Tuple[int, float]] = {
    # Polska / Europa Środkowa
    "Krakow_Center": (220, 2.1),
    "Krakow_Balice": (241, 0.3),
    "Tarnow": (209, 1.4),
    "Zakopane": (838, -0.5),
    "Kasprowy_Wierch": (1987, -1.2),
    "Warszawa": (110, 2.5),
    "Berlin": (34, 1.8),
    # USA — przybliżone wysokości, UHI orientacyjne (patrz uwaga u góry pliku)
    "New_York_Manhattan": (10, 3.0),
    "Chicago": (181, 2.4),
    "Denver": (1655, 1.2),
    "Phoenix": (331, 3.3),
    "Los_Angeles": (71, 2.0),
    "Miami": (2, 1.6),
    "Seattle": (56, 1.3),
}


def get_node_metadata(node_name: str) -> Dict[str, float]:
    """Pobiera dane topograficzne dla podanego punktu.

    Rzuca KeyError dla nieznanego węzła zamiast po cichu zwracać wartości
    domyślne — cicha wartość domyślna (200m, 0.0°C UHI) sprawiała, że
    zapytanie o nierozpoznaną stację dawało wynik wyglądający na poprawny,
    a w rzeczywistości był bez znaczenia."""
    if node_name not in TOPOGRAPHY_DATABASE:
        raise KeyError(
            f"Brak danych topograficznych dla węzła {node_name!r}. "
            f"Dostępne węzły: {sorted(TOPOGRAPHY_DATABASE)}"
        )
    alt, uhi = TOPOGRAPHY_DATABASE[node_name]
    return {"altitude": float(alt), "uhi_factor": uhi}