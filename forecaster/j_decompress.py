# forecaster/j_decompress.py
"""
Dekompresja J – odtworzenie struktury o tej samej długości co dane wejściowe.
"""

def j_decompress(mean, std, length):
    """
    Odtwarza strukturę o zadanej długości na podstawie średniej i odchylenia.
    """
    if length <= 0:
        return []
    # Generuje losowe wartości z rozkładu normalnego o zadanej średniej i std
    import random
    return [random.gauss(mean, std) for _ in range(length)]
