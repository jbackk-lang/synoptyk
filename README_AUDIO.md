# AUDIO-SYNOPTYK
TIMDR + Λ–τ–ρ na metadanych akustycznych urządzeń audio.

## Cel
Moduł analizuje szum własny mikrofonu i wyciąga z niego sygnały pogodowe.
Nie korzysta z danych meteorologicznych — tylko z metadanych akustycznych.

## Jak to działa
1. Rejestracja szumu z mikrofonu.
2. FFT → widmo częstotliwości.
3. Wyciąganie metadanych:
   - energia w pasmach (low/mid/high),
   - szum tła,
   - dominująca częstotliwość.
4. TIMDR:
   - skręt → zmiana kierunku energii,
   - defekt → skok w paśmie lub szumie,
   - rezonans → jednoczesna zmiana wielu pasm.

## Przykłady interpretacji
- wzrost low + defekt → wiatr / burza,
- spadek high + rezonans → mgła,
- wzrost noise_floor → opady / wilgotność,
- skręt mid → zmiana masy powietrza.

## Uruchomienie
