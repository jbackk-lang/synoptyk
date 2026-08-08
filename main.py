from data_sources.real_weather import fetch_all_regions
from synoptyk.compare import compare
from synoptyk.trend import trend

# model_ecmwf = ...
# model_icon = ...

real = fetch_all_regions()

# przykład dla Wieliczki:
# comp_ecmwf = compare(real["wieliczka"], model_ecmwf)
# comp_icon = compare(real["wieliczka"], model_icon)

# trend_wieliczka = trend(real["wieliczka"])
