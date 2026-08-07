"""
SYNOPTYK-F Engine – Filtrowanie falkowe i analiza strukturalna
"""

import numpy as np
import pywt


class SynoptykFEngine:
    def __init__(self, wavelet: str = "db4", mode: str = "symmetric"):
        self.wavelet = wavelet
        self.mode = mode

    def filter_signal(self, data: np.ndarray, level: int = 2) -> np.ndarray:
        """Usuwa szum z szeregu czasowego za pomocą falki Daubechies."""
        coeffs = pywt.wavedec(data, self.wavelet, mode=self.mode, level=level)
        # Tłumienie wysokich częstotliwości (szumu)
        threshold = np.std(coeffs[-1]) * np.sqrt(2 * np.log(len(data)))
        coeffs[1:] = [pywt.threshold(c, threshold, mode="soft") for c in coeffs[1:]]
        reconstructed = pywt.waverec(coeffs, self.wavelet, mode=self.mode)
        return reconstructed[: len(data)]

    def calculate_resonance(
        self, temp_field: np.ndarray, humidity_field: np.ndarray
    ) -> np.ndarray:
        """Oblicza wskaźnik rezonansu opadowego/konwekcyjnego."""
        gradient_t = np.gradient(temp_field)
        gradient_h = np.gradient(humidity_field)
        resonance = np.sqrt(gradient_t**2 + gradient_h**2) * (humidity_field / 100.0)
        return np.round(resonance, 3)

    def predict_temperature_step(
        self, base_temp: float, uhi_factor: float, topo_alt: float
    ) -> float:
        """Korekta temperatury o Miejską Wyspę Ciepła (UHI) oraz wysokość n.p.m."""
        # Gradient termiczny: -0.65°C na 100m wysokości
        lapse_rate = (topo_alt / 100.0) * 0.65
        predicted = base_temp + uhi_factor - lapse_rate
        return round(predicted, 2)


if __name__ == "__main__":
    engine = SynoptykFEngine()
    test_data = np.array([35.0, 34.5, 25.0, 26.0, 27.0, 30.0, 28.0])
    filtered = engine.filter_signal(test_data)
    print("Sygnał po filtrowaniu falkowym:", filtered)
