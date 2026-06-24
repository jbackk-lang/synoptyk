def j_compress(data):
    """
    Kompresja J — redukcja danych do dwóch parametrów:
    - średnia
    - odchylenie standardowe
    """
    mean = sum(data) / len(data)
    variance = sum((x - mean)**2 for x in data) / len(data)
    std = variance**0.5
    return mean, std
