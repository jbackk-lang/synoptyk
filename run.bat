@echo off
chcp 65001 > nul
title SYNOPTYK-F Launcher

echo ===================================================
echo   🌀 Uruchamianie SYNOPTYK-F Web Service & API
echo ===================================================
echo.

:: 1. Przejście do katalogu skryptu
cd /d "%~dp0"

:: 2. Weryfikacja i instalacja wymaganych pakietów przez interpreter Pythona
echo [1/2] Sprawdzanie i instalacja zależności (FastAPI, Uvicorn, Requests)...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet fastapi uvicorn pydantic requests

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ BŁĄD: Nie udało się zainstalować pakietów. Upewnij się, że Python jest dodany do PATH.
    pause
    exit /b %ERRORLEVEL%
)

:: 3. Uruchomienie serwera API i Dashboardu WWW
echo [2/2] Uruchamianie serwera pod adresem http://localhost:8000 ...
echo.
echo Naciśnij CTRL+C, aby zatrzymać serwer.
echo ---------------------------------------------------

python -m uvicorn main_api:app --host 127.0.0.1 --port 8000 --reload

pause