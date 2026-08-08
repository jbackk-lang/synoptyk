@echo off
title Synoptyk-v2.0 -- TIMDR Full Performance Mode
color 0A
cls

:: Zawsze pracuj w katalogu, w ktorym faktycznie lezy ten plik .bat,
:: niezaleznie od tego, skad zostal uruchomiony (skrot, terminal, itp.)
cd /d "%~dp0"

echo ============================================================
echo   SYNOPTYK-v2.0: Uruchamianie Systemu (API + GUI)
echo   Katalog roboczy: %cd%
echo ============================================================
echo.

:: 1. ZDJECIE LIMITOW SYSTEMOWYCH I WATKOWYCH
set PYTHONUNBUFFERED=1
set OMP_NUM_THREADS=%NUMBER_OF_PROCESSORS%
set MKL_NUM_THREADS=%NUMBER_OF_PROCESSORS%
set OPENBLAS_NUM_THREADS=%NUMBER_OF_PROCESSORS%
set VECLIB_MAXIMUM_THREADS=%NUMBER_OF_PROCESSORS%
set NUMEXPR_NUM_THREADS=%NUMBER_OF_PROCESSORS%

:: 2. AKTYWACJA SRODOWISKA VENV
if exist "venv\Scripts\activate.bat" (
    echo [OK] Aktywacja venv...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo [OK] Aktywacja .venv...
    call .venv\Scripts\activate.bat
) else (
    echo [INFO] Uzywanie systemowej instalacji Pythona.
)

:: 3. AUTO-INSTALACJA WYMAGANYCH MODULOW
echo.
echo [1/2] Weryfikacja i instalacja pakietow pip...
python -m pip install --upgrade pip --disable-pip-version-check
python -m pip install gradio fastapi uvicorn pandas numpy requests pywavelets scipy openmeteo-requests

if %ERRORLEVEL% NEQ 0 (
    echo [BLAD] Nie udalo sie zainstalowac wymaganych pakietow.
    pause
    exit /b 1
)

:: 4. WERYFIKACJA PLIKOW WEJSCIOWYCH
if not exist "api\main.py" (
    echo [BLAD] Nie znaleziono pliku "%cd%\api\main.py"
    echo         Sprawdz, czy ten .bat lezy w tym samym folderze co api\, gui_app.py itd.
    pause
    exit /b 1
)
if not exist "gui_app.py" (
    echo [BLAD] Nie znaleziono pliku "%cd%\gui_app.py"
    echo         Sprawdz, czy ten .bat lezy w tym samym folderze co api\, gui_app.py itd.
    pause
    exit /b 1
)

:: 5. URUCHOMIENIE SERWERA API (w osobnym oknie) ORAZ GUI GRADIO (w tym oknie)
echo.
echo [2/2] Uruchamianie Uvicorn API oraz GUI Gradio...
echo Interfejs API: http://127.0.0.1:8000
echo Dokumentacja Swagger: http://127.0.0.1:8000/docs
echo GUI Gradio uruchomi sie zaraz w tym oknie (zwykle http://127.0.0.1:7860)
echo.

start "Synoptyk API (Uvicorn)" cmd /k python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

python gui_app.py

echo.
echo ============================================================
echo GUI zostalo zamkniete. Okno API dziala nadal osobno.
echo ============================================================
pause
