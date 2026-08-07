"""
Topomap Data Module – Baza ukształtowania terenu i Miejscowych Wysp Ciepła (UHI)
"""

from typing import Dict, Tuple


# Słownik stacji/węzłów: (wysokość n.p.m. w metrach, wskaźnik UHI w °C)
TOPOGRAPHY_DATABASE: Dict[str, Tuple[int, float]] = {
    "Krakow_Center": (220, 2.1),
    "Krakow_Balice": (241, 0.3),
    "Tarnow": (209, 1.4),
    "Zakopane": (838, -0.5),
    "Kasprowy_Wierch": (1987, -1.2),
    "Warszawa": (110, 2.5),
    "Berlin": (34, 1.8),
}


def get_node_metadata(node_name: str) -> Dict[str, float]:
    """Pobiera dane topograficzne dla podanego punktu."""
    alt, uhi = TOPOGRAPHY_DATABASE.get(node_name, (200, 0.0))
    return {"altitude": float(alt), "uhi_factor": uhi}