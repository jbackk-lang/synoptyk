# forecaster/j_compress.py
"""
Kompresja J – redukcja danych do parametrów opisujących rdzeń zjawiska.
"""

def j_compress(data):
    """
    Kompresja J – rdzeń danych:
    - średnia
    - odchylenie standardowe
    """
    if not data or len(data) == 0:
        return 0, 0
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std = variance ** 0.5
    return mean, std
