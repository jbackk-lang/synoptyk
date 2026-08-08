# 🌀 Synoptyk — analiza pogody oparta o sygnały TIMDR

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Synoptyk pobiera dane pogodowe (Open-Meteo, pokrycie globalne), wykrywa w nich
strukturalne sygnały (nagłe skoki, odwrócenia trendu, jednoczesne anomalie
kilku parametrów) i na tej podstawie liczy prognozę krótkoterminową —
**deterministyczną, z jawnym pasmem niepewności**, a nie pojedynczą "magiczną"
liczbą.

Projekt zawiera **dwa silniki**, różne pod względem podejścia:

| | `TIMDRForecast` (`forecaster/`) | `SynoptykFEngine` (`synoptyk_f.py`) |
|---|---|---|
| Dane wejściowe | pełen szereg godzinowy (temp/ciśnienie/wilgotność/wiatr) | głównie temperatura + wilgotność |
| Metoda | ekstrapolacja trendu (regresja liniowa) korygowana sygnałami TIMDR | odszumianie falkowe (Daubechies db4) + statyczna korekta UHI/wysokość, korygowana sygnałami TIMDR |
| Horyzont | godzinowy → agregowany do dziennego, wielodniowy | pojedynczy punkt (bieżąca korekta stacyjna) |
| Wynik | `forecast` + `lower`/`upper` (pasmo niepewności) | `point` + `lower`/`upper` + wskaźnik rezonansu |

Oba są zasilane tym samym `TIMDRAnalyzer` (moduł `analyzer/`), więc "TIMDR" w
nazwie odnosi się realnie do tego samego mechanizmu wykrywania sygnałów w obu
przypadkach — to nie jest tylko wspólna marka.

## ⚠️ Stan projektu — przeczytaj przed użyciem

To repozytorium było wielokrotnie naprawiane (patrz `CHANGELOG.md` jeśli
istnieje / historia commitów) — kilka poważnych błędów zostało usuniętych:
brakujące importy (`numpy`), urwany plik uruchomieniowy (`SyntaxError` w
`synoptyk.py`), oraz **stary silnik prognozy, który generował czysty szum
losowy** (`random.gauss`) zamiast realnej ekstrapolacji — ten kod
(`forecaster/synoptic_f.py`, klasa `SynopticF`) nadal jest w repo dla
porównania/historii, ale **nie jest już domyślnie używany**. Domyślny silnik
to `TIMDRForecast`, w pełni deterministyczny (te same dane wejściowe zawsze
dają ten sam wynik).

**Żadna liczba dokładności (np. "96% zgodności") nie jest obecnie
zweryfikowana w tym repo.** Sekcja [Walidacja](#-walidacja-i-metodologia)
niżej opisuje dokładnie, jak to zrobić rzetelnie — i że dopóki tego nie
zrobisz, żadnego procentu nie da się uczciwie podać.

## 🚀 Co program faktycznie robi

* **Pobieranie danych** (`data/fetcher.py`) — Open-Meteo Archive API, dowolna
  lokalizacja na świecie (nie tylko Polska), dane godzinowe: temperatura,
  ciśnienie, wilgotność, prędkość i kierunek wiatru, opady.
* **Wykrywanie sygnałów TIMDR** (`analyzer/timdr_analyzer.py`):
  * *skręt* — odwrócenie trendu parametru w krótkim oknie,
  * *anomalia* — wartość poza progiem klimatologicznym (adaptacyjnym,
    liczonym per stacja/miesiąc — `analyzer/adaptive_thresholds.py`),
  * *defekt* — nagły skok wartości między kolejnymi odczytami,
  * *rezonans* — jednoczesna anomalia ≥3 parametrów (możliwa zmiana frontu).
* **Analiza wiatru** (`analyzer/wind_analyzer.py`) — średnia kierunku metodą
  wektorową (poprawną dla wielkości kołowych), detekcja nagłej zmiany
  kierunku, wykrywanie przejścia frontu.
* **Prognoza deterministyczna** — patrz tabela wyżej. Sygnały TIMDR
  **realnie zmieniają** wynik: skręt trendu → liczony od punktu odwrócenia,
  nie z całego okna; anomalia/defekt/rezonans → prognoza ściągana w stronę
  średniej i poszerzone pasmo niepewności, zamiast milczącej pojedynczej
  liczby.
* **Walidacja** (`forecaster/validator.py`) — porównanie prognozy z danymi,
  które faktycznie nadeszły (MAE, RMSE) — patrz sekcja niżej.

## 🌍 Obsługiwane regiony

`run_synoptyk.py` obsługuje regiony z jawnie zdefiniowanymi stacjami węzłowymi
(nieznany region kończy się czytelnym błędem, nie cichym podstawieniem innego
obszaru):

| Region | Stacje |
|---|---|
| `malopolska` | Kraków-Centrum, Tarnów, Zakopane |
| `poland` | Kraków-Centrum, Warszawa, Tarnów |
| `europe` | Berlin, Kraków-Centrum |
| `usa` | Nowy Jork (Manhattan), Chicago, Denver, Phoenix, Los Angeles, Miami, Seattle |
| `usa_northeast` | Nowy Jork, Chicago |
| `usa_west` | Denver, Phoenix, Los Angeles, Seattle |

Wysokości n.p.m. stacji (`topomap_data.py`) są przybliżone (dane publiczne,
zaokrąglone). **Wskaźniki UHI (Miejska Wyspa Ciepła) są orientacyjne — nie
pochodzą z pomiarów**, to szacunki rzędu wielkości do czasu podłączenia
realnego źródła (np. porównania stacji miejskiej vs. podmiejskiej z tego
samego okresu). Traktuj je jako punkt wyjścia do kalibracji, nie jako gotowy
wynik pomiarowy.

## 🛠️ Instalacja

```bash
git clone https://github.com/jbackk-lang/synoptyk.git
cd synoptyk
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Wymaga Pythona 3.10+. Zależności: `requests`, `pandas`, `numpy`,
`PyWavelets`, `pyyaml`, `plotly`, `streamlit`, `fastapi`, `uvicorn`,
`pydantic` (pełna lista w `requirements.txt`).

Program wymaga dostępu do internetu (Open-Meteo Archive API) do pobrania
realnych danych — bez tego dostępu dostępny jest tylko tryb
`--offline-demo`, pokazujący strukturę regionu/siatki bez liczenia prognozy.

## ⚡ Szybki start

### 1. Pełna analiza TIMDR + prognoza (jedna stacja, `synoptyk.py`)

```bash
python synoptyk.py
```

Domyślnie liczy dla stacji zdefiniowanej w `config/config.yaml`
(`krakow_balice`). Wypisuje: wykryte sygnały TIMDR, analizę wiatru z ostatnich
24h, oraz prognozę wielodniową z pasmem niepewności dla każdego parametru.

### 2. Symulacja regionalna z topografią (`run_synoptyk.py`)

```bash
# Sprawdzenie struktury regionu bez pobierania danych
python run_synoptyk.py --region usa --offline-demo

# Pełne uruchomienie z realnymi danymi
python run_synoptyk.py --region usa --days 7
python run_synoptyk.py --region malopolska --days 7 --grid 0.125

# Nieznany region -> czytelny błąd, nie ciche przełączenie na inny obszar
python run_synoptyk.py --region ameryka
# BŁĄD: Nieznany region: 'ameryka'. Dostępne regiony: [...]
```

### 3. Programowo (Python)

```python
from data.fetcher import WeatherFetcher
from analyzer.timdr_analyzer import TIMDRAnalyzer
from forecaster import TIMDRForecast

fetcher = WeatherFetcher(lat=40.78, lon=-73.97)   # Nowy Jork
df = fetcher.fetch_last_n_days(7)

analyzer = TIMDRAnalyzer(station="New_York_Manhattan")
timdr_results = analyzer.analyze(df)

forecaster = TIMDRForecast(figure_window_days=7)
forecast = forecaster.predict_daily(df, timdr_results, horizon_days=3)

print(forecast["temp"]["daily_forecast"])   # punktowa prognoza
print(forecast["temp"]["daily_lower"])      # dolne pasmo niepewności
print(forecast["temp"]["daily_upper"])      # górne pasmo niepewności
print(forecast["temp"]["timdr_adjustment"]) # jakie sygnały TIMDR wpłynęły na wynik
```

## 📊 Walidacja i metodologia

To jest **najważniejsza sekcja tego README**, bo dotychczas jej brakowało.

`forecaster/validator.py` (`ForecastValidator`) liczy MAE i RMSE prognozy
względem danych, które faktycznie nadeszły:

```python
from forecaster import ForecastValidator

# forecast_data: wynik forecaster.predict(...) sprzed np. 3 dni
# actual_data: dane pobrane PO fakcie za ten sam okres
validator = ForecastValidator(forecast_data, actual_data)
result = validator.validate("temp", metric="mae")
print(result["mae"], result["rmse"], result["matched_dates"])
```

Żeby dowolna liczba skuteczności (np. "X% zgodności") była wiarygodna,
potrzeba **wszystkich** poniższych elementów — ich brak jest dokładnie tym,
co wcześniej sprawiało, że podawane liczby nie dało się zweryfikować:

1. **Jasna definicja metryki** — MAE w °C? % trafień w przedziale ±1°C?
   Zgodność kierunku trendu? Różne definicje dają bardzo różne liczby.
2. **Test out-of-sample** — model nie mógł "widzieć" danych, na których jest
   oceniany. Standardowo: trenuj/kalibruj na oknie [T-30d, T], testuj na
   [T, T+3d], przesuwaj okno i powtarzaj (walidacja krocząca).
3. **Baseline do porównania** — bez tego liczba nie ma punktu odniesienia:
   - *persystencja*: "jutro = dziś" (dla wielu zmiennych zaskakująco trudna
     do pobicia w krótkim horyzoncie),
   - *klimatologia*: "jutro = średnia z tego dnia roku z poprzednich lat",
   - opcjonalnie oficjalna prognoza (IMGW / NWS) dla tej samej lokalizacji
     i okresu, jeśli celem jest porównanie z istniejącym standardem.
4. **Wystarczająca próba** — pojedyncze sprawdzenie "wyszło 96%" nie mówi nic
   o typowej skuteczności; potrzeba wielu niezależnych okien czasowych
   (najlepiej obejmujących różne pory roku i różne stacje).
5. **Odtwarzalność** — ktoś inny, uruchamiając ten sam kod na tych samych
   datach, powinien dostać ten sam wynik. (To jest już spełnione dla
   `TIMDRForecast` — patrz wyżej — ale nie było spełnione dla starego
   `SynopticF`.)

Dopóki wynik walidacji nie jest opublikowany z powyższymi elementami, każdą
liczbę procentową w tym README czy w materiałach promocyjnych należy
traktować jako niepotwierdzoną.

## 🏗️ Struktura repo

```
synoptyk/
├── synoptyk.py                  # główny punkt wejścia: TIMDR + TIMDRForecast dla jednej stacji
├── run_synoptyk.py              # symulacja regionalna z topografią (grid + stacje węzłowe)
├── synoptyk_f.py                # SynoptykFEngine: filtr falkowy + korekta UHI/wysokość, zintegrowany z TIMDR
├── grid_engine.py                # generator siatki przestrzennej dla regionu
├── topomap_data.py              # baza wysokości/UHI dla stacji węzłowych (PL/EU/USA)
├── config/config.yaml           # domyślna stacja, okno figury, horyzont prognozy
├── data/
│   ├── fetcher.py                # pobieranie danych z Open-Meteo Archive API
│   └── cache.py                  # cache SQLite (dane godzinowe + klimatologia)
├── analyzer/
│   ├── timdr_analyzer.py         # główna logika sygnałów: skręt/anomalia/rezonans/defekt
│   ├── adaptive_thresholds.py   # progi anomalii adaptacyjne per stacja/miesiąc
│   └── wind_analyzer.py          # analiza kierunku/prędkości wiatru, detekcja frontu
├── forecaster/
│   ├── timdr_forecast.py        # domyślny silnik prognozy (deterministyczny, zasilany TIMDR)
│   ├── synoptic_f.py             # STARY silnik (losowy) — zachowany dla porównania, nie domyślny
│   ├── j_compress.py / j_decompress.py  # pomocnicze funkcje starego silnika
│   └── validator.py              # MAE/RMSE prognozy vs dane rzeczywiste
└── scripts/update_climatology.py # aktualizacja progów klimatologicznych w cache
```

## 📝 Licencja

MIT.
