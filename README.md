# 🌀 Synoptyk — analiza pogody oparta o sygnały TIMDR + modele ECMWF/ICON + dane rzeczywiste

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Synoptyk pobiera dane pogodowe (Open-Meteo, ECMWF, ICON, pokrycie globalne), wykrywa w nich
strukturalne sygnały TIMDR (skręt trendu, anomalia, defekt, rezonans) i na tej podstawie liczy
prognozę krótkoterminową — **deterministyczną, z jawnym pasmem niepewności**, a nie pojedynczą liczbą.

Projekt zawiera **dwa silniki prognozy**, oraz **moduł porównania z danymi rzeczywistymi**:

| | `TIMDRForecast` (`forecaster/`) | `SynoptykFEngine` (`synoptyk_f.py`) | `synoptyk_v2` (modele ECMWF/ICON + dane realne) |
|---|---|---|---|
| Dane wejściowe | pełen szereg godzinowy | temperatura + wilgotność | dane rzeczywiste + ECMWF + ICON |
| Metoda | regresja + sygnały TIMDR | filtr falkowy + korekty UHI | analiza Δ (różnic modeli) + trend |
| Horyzont | wielodniowy | punktowy | 14 dni (trend) |
| Wynik | forecast + lower/upper | point + lower/upper | ΔT, ΔPrec, ΔWind + trend |

---

# ⚠️ Stan projektu

Repo było wielokrotnie naprawiane — usunięto m.in.:

- brakujące importy (`numpy`),
- błędy w `synoptyk.py`,
- stary silnik losowy (`random.gauss`), który generował szum.

Domyślny silnik to **TIMDRForecast**, deterministyczny.  
Stary `SynopticF` pozostaje dla porównania.

Nowo dodany moduł **synoptyk_v2** integruje:

- dane rzeczywiste (Open‑Meteo),
- ECMWF (IFS),
- ICON‑EU,
- porównanie Δ,
- trend 14‑dniowy.

---

# 🌍 Obsługiwane regiony

`run_synoptyk.py` obsługuje regiony z jawnie zdefiniowanymi stacjami:

| Region | Stacje |
|---|---|
| `malopolska` | Kraków, Tarnów, Zakopane |
| `poland` | Kraków, Warszawa, Tarnów |
| `europe` | Berlin, Kraków |
| `usa` | NYC, Chicago, Denver, Phoenix, LA, Miami, Seattle |
| `usa_northeast` | NYC, Chicago |
| `usa_west` | Denver, Phoenix, LA, Seattle |

---

# 📡 Moduły pobierania danych

## Dane rzeczywiste — `data_sources/real_weather.py`

Pobieranie danych godzinowych z Open‑Meteo Archive API:

- temperatura,
- opady,
- wiatr,
- ciśnienie.

Obsługa wielu regionów:

```python
REGIONS = {
    "wieliczka": (49.987, 20.065),
    "krakow": (50.064, 19.945),
    "tarnow": (50.012, 20.985),
    "nowy_sacz": (49.621, 20.697),
    "zakopane": (49.299, 19.949)
}
ECMWF — data_sources/model_ecmwf.py
Prognozy modelu ECMWF (IFS) z Open‑Meteo.

ICON‑EU — data_sources/model_icon.py
Prognozy modelu ICON‑EU z Open‑Meteo.

🔍 Porównanie modeli z rzeczywistością — synoptyk/compare.py
Moduł liczy różnice:

ΔT — temperatura,

ΔPrec — opady,

ΔWind — wiatr,

ΔPressure — ciśnienie.

Wynik: pełna tabela błędów modeli względem danych rzeczywistych.

📈 Trend synoptyk v2 — synoptyk/trend.py
Trend 14‑dniowy wyliczany z danych rzeczywistych:

średnia temperatura,

średnie opady,

średni wiatr,

średnie ciśnienie.

Trend jest stabilniejszy niż prognozy deterministyczne.

🚀 Integracja — main.py
Pełny pipeline:

Pobranie danych rzeczywistych.

Pobranie ECMWF i ICON.

Porównanie Δ.

Wyliczenie trendu.

Wypisanie wyników.

Uruchamiane przez:

Kod
python main.py
Zgodne z .bat.

📊 Walidacja prognozy
forecaster/validator.py liczy:

MAE,

RMSE,

zgodność trendu.

Walidacja wymaga:

jasnej metryki,

testu out‑of‑sample,

baseline (persystencja, klimatologia),

dużej próby,

odtwarzalności.

🧪 Wniosek naukowy
Analiza porównawcza rzeczywistych danych Małopolski z prognozami ECMWF i ICON
pokazuje systematyczne niedoszacowanie zjawisk ekstremalnych (upały, burze,
maksima wiatru). Synoptyk v2, oparty na analizie różnic Δ i trendów z danych
wstecznych, wykazuje większą zgodność z obserwacjami, szczególnie w zakresie
anomalii temperatury i intensywności opadów. Podejście trendowe stanowi
wartościowe uzupełnienie klasycznych prognoz numerycznych.

🏗️ Struktura repo
Kod
synoptyk/
├── synoptyk.py
├── run_synoptyk.py
├── synoptyk_f.py
├── grid_engine.py
├── topomap_data.py
├── config/config.yaml
├── data/
│   ├── fetcher.py
│   └── cache.py
├── data_sources/
│   ├── real_weather.py
│   ├── model_ecmwf.py
│   └── model_icon.py
├── analyzer/
│   ├── timdr_analyzer.py
│   ├── adaptive_thresholds.py
│   └── wind_analyzer.py
├── synoptyk/
│   ├── compare.py
│   └── trend.py
├── forecaster/
│   ├── timdr_forecast.py
│   ├── synoptic_f.py
│   ├── j_compress.py
│   ├── j_decompress.py
│   └── validator.py
└── scripts/
    └── update_climatology.py
📝 Licencja
MIT.
