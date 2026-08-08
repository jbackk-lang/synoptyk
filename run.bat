@echo off
title Synoptyk-v2.0 -- TIMDR Engine (Full Power)
color 0A
cls

echo ============================================================
echo   SYNOPTYK-v2.0: Uruchamianie w trybie pelnej wydajnosci
echo ============================================================
echo.

:: 1. ZDJECIE LIMITOW SYSTEMOWYCH I WĄTKOWYCH (Win/Python)
set PYTHONUNBUFFERED=1
set OMP_NUM_THREADS=%NUMBER_OF_PROCESSORS%
set MKL_NUM_THREADS=%NUMBER_OF_PROCESSORS%
set OPENBLAS_NUM_THREADS=%NUMBER_OF_PROCESSORS%
set VECLIB_MAXIMUM_THREADS=%NUMBER_OF_PROCESSORS%
set NUMEXPR_NUM_THREADS=%NUMBER_OF_PROCESSORS%

:: 2. SPRAWDZENIE I AKTYWACJA VENV (jesli istnieje)
if exist "venv\Scripts\activate.bat" (
    echo [OK] Aktywacja wirtualnego srodowiska (venv)...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo [OK] Aktywacja wirtualnego srodowiska (.venv)...
    call .venv\Scripts\activate.bat
) else (
    echo [INFO] Brak wirtualnego srodowiska. Uruchamianie z globalnego Pythona.
)

echo [OK] Alokacja watkow procesora: %NUMBER_OF_PROCESSORS% watkow.
echo.

:: 3. URUCHOMIENIE APLIKACJI GUI
if exist "gui_app.py" (
    echo Uruchamianie gui_app.py...
    python gui_app.py
) else if exist "synoptyk.py" (
    echo Uruchamianie synoptyk.py...
    python synoptyk.py
) else (
    echo [BŁĄD] Nie znaleziono pliku gui_app.py ani synoptyk.py!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Sesja zostala zakonczona.
echo ============================================================
pause
