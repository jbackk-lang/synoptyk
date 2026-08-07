"""
Grid Engine – Generator przestrzennych siatek geograficznych
"""

from typing import Dict, Tuple
import numpy as np


class SpatialGridEngine:
    def __init__(self, bbox: Tuple[float, float, float, float], resolution: float):
        """
        bbox: (min_lat, max_lat, min_lon, max_lon)
        resolution: krok siatki w stopniach (np. 0.125)
        """
        self.min_lat, self.max_lat, self.min_lon, self.max_lon = bbox
        self.resolution = resolution

    def generate_mesh(self) -> Dict[str, np.ndarray]:
        """Generuje współrzędne siatki geograficznej."""
        lats = np.arange(self.min_lat, self.max_lat + self.resolution, self.resolution)
        lons = np.arange(self.min_lon, self.max_lon + self.resolution, self.resolution)
        grid_lon, grid_lat = np.meshgrid(lons, lats)
        return {
            "latitudes": grid_lat,
            "longitudes": grid_lon,
            "shape": grid_lat.shape,
        }


def get_region_bbox(region_name: str) -> Tuple[float, float, float, float]:
    """Zwraca granice przestrzenne dla wybranego regionu."""
    regions = {
        "malopolska": (49.1, 50.5, 19.0, 21.5),
        "poland": (49.0, 54.8, 14.1, 24.1),
        "europe": (35.0, 71.0, -10.0, 40.0),
    }
    return regions.get(region_name.lower(), regions["malopolska"])