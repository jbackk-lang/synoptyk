# api/main.py – fragment z nowym endpointem

from analyzer.wind_analyzer import WindAnalyzer

# ... reszta kodu ...

@app.post("/wind")
def wind_analysis(request: FetchRequest):
    """
    Analiza wiatru dla podanej stacji.
    Zwraca średni kierunek, prędkość, nagłe zmiany i różę wiatrów.
    """
    try:
        df = fetch_data(request.station, request.days)
        wind = WindAnalyzer(df)
        
        return {
            "status": "success",
            "station": request.station,
            "days": request.days,
            "wind": {
                "avg_speed": wind.average_speed(),
                "avg_direction": wind.average_direction(),
                "sudden_change": wind.sudden_direction_change(),
                "front_detected": wind.detect_front(),
                "wind_rose": wind.wind_rose_data().to_dict()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
