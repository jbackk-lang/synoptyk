@echo off
title Synoptyk-v2.0 -- TIMDR Full Performance Mode
color 0A
cls

echo ============================================================
echo   SYNOPTYK-v2.0: Uruchamianie Systemu (API + GUI)
echo ============================================================
echo.

:: 1. ZDJĘCIE LIMITÓW SYSTEMOWYCH I WĄTKOWYCH
set PYTHONUNBUFFERED=1
set OMP_NUM_THREADS=%NUMBER_OF_PROCESSORS%
set MKL_NUM_THREADS=%NUMBER_OF_PROCESSORS%
set OPENBLAS_NUM_THREADS=%NUMBER_OF_PROCESSORS%
set VECLIB_MAXIMUM_THREADS=%NUMBER_OF_PROCESSORS%
set NUMEXPR_NUM_THREADS=%NUMBER_OF_PROCESSORS%

:: 2. AKTYWACJA ŚRODOWISKA VENV
if exist "venv\Scripts\activate.bat" (
    echo [OK] Aktywacja venv...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo [OK] Aktywacja .venv...
    call .venv\Scripts\activate.bat
) else (
    echo [INFO] Używanie systemowej instalacji Pythona.
)

:: 3. AUTO-INSTALACJA WYMAGANYCH MODUŁÓW
echo.
echo [1/2] Weryfikacja i instalacja pakietow pip...
python -m pip install --upgrade pip --disable-pip-version-check
python -m pip install gradio fastapi uvicorn pandas numpy requests pywavelets scipy openmeteo-requests

if %ERRORLEVEL% NEQ 0 (
    echo [BŁĄD] Nie udalo sie zainstalowac wymaganych pakietow.
    pause
    exit /b 1
)

:: 4. URUCHOMIENIE SERWERA API / GUI
echo.
echo [2/2] Uruchamianie Uvicorn API oraz GUI Gradio...
echo Interfejs API: http://127.0.0.1:8000
echo Dokumentacja Swagger: http://127.0.0.1:8000/docs
echo.

if exist "api\main.py" (
    python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
) else if exist "gui_app.py" (
    python gui_app.py
) else (
    echo [BŁĄD] Nie znaleziono pliku api\main.py ani gui_app.py!
)

echo.
echo ============================================================
pause