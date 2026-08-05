# 🌤️ synoptyk – Niespotykana analiza globalnej pogody

WWW [https://github.com/jbackk-lang/jbackk-lang.github.io  ](https://jbackk-lang.github.io/)   

**TIMDR + Λ–τ–ρ na danych synoptycznych IMGW**

`synoptyk` to lekki, strukturalny analizator meteorologiczny. Nie oblicza fizyki atmosfery – analizuje **zmiany parametrów w czasie**, wychwytując odwrócenia trendu, anomalie, skoki, mikro-fronty i stabilizacje pogody. Projekt jest częścią ekosystemu **TIMDR** i łączy się z modelem prognostycznym **SYNOPTIC‑F**.

---

## 🎯 Opis

`synoptyk` działa na danych godzinowych (np. ze stacji Kraków–Balice) i przekształca je w sygnały opisujące dynamikę pogody.

**Wykrywa:**
- odwrócenia trendu (skręt)
- anomalie
- skoki (defekty)
- mikro-fronty
- stabilizacje pogody

---

## 🕯️ Świece (OHLC)

Dane godzinowe są zagregowane w świece dla trzech warstw czasowych:
- **1h** – wilgotność (szybkie zmiany)
- **4h** – temperatura (cykle dobowe)
- **12h** – ciśnienie (fronty atmosferyczne)

Świeca = **open, high, low, close** dla każdego okna.

---

## 📡 Sygnały TIMDR

| Sygnał | Opis meteorologiczny |
|--------|------------------------|
| **Skręt (trend reversal)** | Zmiana kierunku zmian: ciśnienie spadało → zaczyna rosnąć, temperatura rosła → zaczyna spadać. Przejście frontu, zmiana masy powietrza. |
| **Anomalia (anomaly)** | Nagła zmiana wykraczająca poza normalne wahania: szybki spadek temperatury, skok ciśnienia, wzrost wilgotności przed opadami. |
| **Momentum** | Kumulacja zmian w krótkim czasie: seria wzrostów temperatury (napływ ciepła) lub spadków ciśnienia (zbliżający się front). |
| **Defekt (defect)** | Skok, który nie pasuje do trendu: np. wilgotność spada podczas burzy, ciśnienie rośnie w środku frontu. Lokalne zaburzenie. |
| **Rezonans (resonance)** | Zgodność kilku parametrów naraz: spadek ciśnienia + wzrost wilgotności + zmiana wiatru → front. |

---

## 🧱 Warstwy Λ–τ–ρ

- **Λ (struktura danych)** – kontrola jakości: kompletność, brak szumu, stabilność pomiarów.
- **τ (transformacja zmian)** – charakter zmian: tempo spadku/wzrostu ciśnienia, amplituda temperatury, dynamika wilgotności.
- **ρ (defekt)** – wykrywanie nagłych skoków: burze, mikro-fronty, lokalne zaburzenia.

---

## 🧠 SYNOPTIC‑F – Model Prognozowania Strukturalnego

`SYNOPTIC‑F` to rozszerzenie `synoptyk` o rzeczywiste prognozowanie oparte na **figurze zjawiska** (inwariancie strukturalnym).

### Zasada działania
1. **Kompresja J** – redukcja danych do parametrów rdzenia (średnia, odchylenie standardowe).
2. **Dekompresja J** – odtworzenie struktury o tej samej długości.
3. **Filtr Λ–τ–ρ** – wydobycie figury zjawiska (struktury, transformacji, defektu).
4. **Prognoza** – figura staje się podstawą przewidywania kolejnych wartości.

### Kluczowa reguła
> **Zasięg prognozy SYNOPTIC‑F jest równy długości okna danych wejściowych.**

| Dane wejściowe | Prognoza |
|----------------|----------|
| 7 dni | 7 dni |
| 14 dni | 14 dni |
| 30 dni | 30 dni |

### Dlaczego to działa?
Figura zjawiska jest stabilna – reprezentuje rytm i kształt zmian, a nie chwilową dynamikę. Model przewiduje przyszłość na podstawie struktury wyciągniętej z danych historycznych.

---

## 🚀 Uruchomienie

### Wymagania
```bash
pip install -r requirements.txt

Uruchom analizę
bash
python3 synoptyk.py
Format danych wejściowych (CSV)
text
datetime,temp,pressure,humidity,wind_speed,wind_dir,precip
2026-05-24 12:00,23.1,1012.4,45,3.2,270,0
Wynik działania
Program wypisuje:

Λ – jakość danych

τ – charakter zmian

ρ – defekty

sygnały TIMDR

prognozę SYNOPTIC‑F (48h)

Uruchom API (opcjonalnie)
bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
Dokumentacja API: http://localhost:8000/docs

📂 Struktura repozytorium
text
synoptyk/
├── analyzer/          # Analiza TIMDR i warstwy Λ–τ–ρ
├── api/               # FastAPI
├── config/            # Konfiguracja (config.yaml)
├── data/              # Pobieranie i cache danych
├── forecaster/        # SYNOPTIC‑F
├── scripts/           # Narzędzia (np. update_climatology.py)
├── synoptyk.py        # Główny skrypt CLI
├── requirements.txt   # Zależności
├── run.bat            # Uruchomienie API (Windows)
└── README.md          # Ten plik
🔗 Powiązane projekty
synoptyk jest częścią ekosystemu TIMDR i współdzieli koncepcje z:

TRM-Geometry-Core – geometria skrętu informacji

FIELDCORE – struktura pola i rezonansów

probabilistic-timdr – rachunek prawdopodobieństwa i warunki brzegowe

Boundary-Matter – analiza topologiczna i geometryczna

