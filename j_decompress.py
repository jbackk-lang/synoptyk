def j_decompress(mean, std, length):
    """
    Dekompresja J — odtworzenie figury o długości 'length'
    na podstawie średniej i odchylenia.
    """
    import numpy as np
    return list(mean + np.linspace(-std, std, length))
