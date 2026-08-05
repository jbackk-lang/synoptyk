@echo off
title SYNOPTYK API Launcher
echo ========================================
echo   SYNOPTYK API Launcher
echo   (c) 2026
echo ========================================
echo.
echo [1/3] Sprawdzanie zaleznosci...
pip install -r requirements.txt > nul 2>&1
echo [OK] Zaleznosci zainstalowane.
echo.
echo [2/3] Uruchamianie API na porcie 8000...
echo.
echo ========================================
echo   API uruchomione!
echo   Dokumentacja: http://localhost:8000/docs
echo   Endpointy:
echo     /health     - status
echo     /stations   - lista stacji
echo     /fetch      - pobierz dane
echo     /analyze    - analiza TIMDR
echo     /forecast   - prognoza SYNOPTIC-F
echo     /full       - pelna analiza
echo ========================================
echo.
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
pause
