# 🌀 SYNOPTYK-F – Atmospheric Wavelet & Field Analysis Engine

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

**Synoptyk-F** to zaawansowany silnik analizy i prognozowania pól meteorologicznych wykorzystujący filtrowanie falkowe (Wavelet Transform), transformatę Fouriera oraz korekty mikroklimatyczne dla Miejskich Wysp Ciepła (UHI) i ukształtowania terenu (orografii).

---

## 🚀 Główne funkcjonalności

* **Filtrowanie falkowe (Wavelet Decomposition):** Izolacja mikrofluktuacji i szumów mezoskalowych z surowych pól ciśnienia i temperatury.
* **Detekcja Rezonansu Opadowego:** Wychwytywanie stref zbieżności wiatru i wymuszeń orograficznych (np. barier Karpat i Beskidów).
* **Moduł UHI (Urban Heat Island):** Precyzyjne szacowanie ekstremów temperatur dla obszarów zurbanizowanych (np. Kraków, Warszawa, Berlin).
* **Wielkoskalowe prognozy regionalne:** Automatyczna generacja siatek numerycznych dla Małopolski, Polski oraz całej Europy (35°N–71°N, 10°W–40°E).

---

## 🛠️ Architektura i pliki modułu

```text
synoptyk/
├── synoptyk_f.py        # Główny silnik obliczeniowy i transformacja falkowa
├── grid_engine.py       # Generator siatek przestrzennych (Spatial Mesh Engine)
├── topomap_data.py      # Dane cyfrowego modelu terenu (DEM / Topografia)
├── config.json          # Parametry macierzy i rzędu falki (domyślnie: Daubechies db4)
└── run_synoptyk.py      # Skrypt wykonawczy dla symulacji i raportów
