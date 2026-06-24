## Dokumentacja online
https://jbackk-lang.github.io/# SYNOPTYK  
TIMDR + Λ–τ–ρ na danych synoptycznych IMGW

## Opis
synoptyk to lekki analizator meteorologiczny działający na danych godzinowych IMGW  
(np. stacja Kraków–Balice).  
Nie liczy fizyki atmosfery — analizuje zmiany parametrów w czasie.

Wykrywa:
- odwrócenia trendu,
- anomalie,
- skoki,
- mikro-fronty,
- stabilizacje pogody.

## Świece (OHLC)
Dane godzinowe są przekształcane w świece:
- 1h – wilgotność (szybkie zmiany),
- 4h – temperatura (cykle dobowe),
- 12h – ciśnienie (fronty).

Świeca = open, high, low, close.

## Sygnały TIMDR (opis meteorologiczny)

### Skręt (trend reversal)
Zmiana kierunku zmian parametru:
- ciśnienie spadało → zaczyna rosnąć,
- temperatura rosła → zaczyna spadać.

Meteorologicznie: przejście frontu, zmiana masy powietrza, zmiana kierunku wiatru.

### Anomalia (anomaly)
Nagła zmiana wykraczająca poza normalne wahania:
- szybki spadek temperatury,
- skok ciśnienia po froncie,
- wzrost wilgotności przed opadami.

### Momentum (przyspieszenie zmian)
Kumulacja zmian w krótkim czasie:
- seria wzrostów temperatury → napływ cieplejszego powietrza,
- seria spadków ciśnienia → zbliżający się front.

### Defekt (defect)
Skok, który nie pasuje do trendu:
- wilgotność spada podczas burzy,
- ciśnienie rośnie w środku frontu.

Meteorologicznie: lokalne zaburzenie, nietypowe zjawisko.

### Rezonans (resonance)
Zgodność kilku parametrów naraz:
- spadek ciśnienia + wzrost wilgotności + zmiana wiatru → front,
- wzrost temperatury + spadek wilgotności → napływ suchego, ciepłego powietrza.

## Warstwy Λ–τ–ρ (opis meteorologiczny)

### Λ — struktura danych
Kontrola jakości:
- kompletność,
- brak szumu,
- stabilność pomiarów.

### τ — transformacja zmian
Charakter zmian:
- tempo spadku/ wzrostu ciśnienia,
- amplituda temperatury,
- dynamika wilgotności.

### ρ — defekt
Wykrywanie nagłych skoków:
- burze,
- mikro-fronty,
- lokalne zaburzenia.

## Prognoza 48h
Prognoza opiera się na:
- świecach ciśnienia (12h),
- świecach temperatury (4h),
- świecach wilgotności (1h),
- sygnałach TIMDR,
- warstwach Λ–τ–ρ.

Model nie przewiduje pogody fizycznie —  
wykrywa kierunek zmian na podstawie sygnałów.

## Uruchomienie
python3 synoptyk.py


Plik CSV musi zawierać:
datetime,temp,pressure,humidity,wind_speed,wind_dir,precip
2026-05-24 12:00,23.1,1012.4,45,3.2,270,0

## Wynik działania
Program wypisuje:
- Λ – jakość danych,
- τ – charakter zmian,
- ρ – defekty,
- sygnały TIMDR,
- prognozę 48h.

## Repozytorium
Kod źródłowy projektu znajduje się tutaj:

https://github.com/jbackk-lang/synoptyk

## Licencja
Projekt udostępniany jest na licencji MIT.

Oznacza to:
- możesz używać kodu w projektach prywatnych i komercyjnych,
- możesz modyfikować, kopiować i rozpowszechniać,
- musisz zachować informację o autorze i licencji w kopii kodu.

## Uwaga końcowa
synoptyk jest projektem otwartym i modularnym.  
Rdzeń (TIMDR + Λ–τ–ρ + świece) jest kompletny i stabilny —  
wszystko, co powstanie dalej, to już przestrzeń do eksperymentów, modyfikacji i zabawy dla społeczności.

Każdy może:
- dodawać własne rozszerzenia,
- tworzyć nowe moduły analizy,
- poprawiać algorytmy,
- rozwijać scoring,
- budować wizualizacje,
- albo po prostu korzystać z gotowego silnika.

synoptyk nie jest klasycznym modelem numerycznym.  
To narzędzie do analizy sygnałów pogodowych — lekkie, szybkie i zrozumiałe.  
Jeśli ktoś chce je rozwijać, droga wolna.  
Jeśli ktoś chce się nim bawić — jeszcze lepiej.


Pełna treść licencji MIT:

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights  
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell  
copies of the Software, and to permit persons to whom the Software is  
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in  
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,  
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE  
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER  
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,  
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN  
THE SOFTWARE.
