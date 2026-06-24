def synoptic_f(data):
    """
    SYNOPTIC-F — projekcja strukturalna.
    Zasięg projekcji = długość okna danych wejściowych.
    """
    length = len(data)

    # Kompresja
    mean, std = j_compress(data)

    # Dekompresja
    decompressed = j_decompress(mean, std, length)

    # Figura (Λ–τ–ρ)
    figure = lambda_tau_rho(decompressed)

    # Projekcja = figura o tej samej długości
    return figure
