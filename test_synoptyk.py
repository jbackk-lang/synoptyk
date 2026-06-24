import unittest
from unittest.mock import patch

import synoptyk


class SynoptykTests(unittest.TestCase):
    def test_get_forecast_returns_polish_summary(self):
        responses = [
            {"results": [{"latitude": 52.2297, "longitude": 21.0122}]},
            {
                "daily": {
                    "time": ["2026-06-24"],
                    "temperature_2m_max": [24.5],
                    "temperature_2m_min": [14.2],
                    "precipitation_probability_max": [20],
                }
            },
        ]

        with patch("synoptyk._fetch_json", side_effect=responses):
            text = synoptyk.get_forecast("Warszawa")

        self.assertIn("Prognoza pogody dla Warszawa (2026-06-24)", text)
        self.assertIn("min 14.2°C, max 24.5°C, opady 20%.", text)

    def test_get_forecast_raises_for_unknown_city(self):
        with patch("synoptyk._fetch_json", return_value={"results": []}):
            with self.assertRaisesRegex(ValueError, "Nie znaleziono miasta"):
                synoptyk.get_forecast("NieistniejaceMiasto")

    def test_get_forecast_raises_for_malformed_forecast_payload(self):
        responses = [
            {"results": [{"latitude": 52.2297, "longitude": 21.0122}]},
            {"daily": {}},
        ]
        with patch("synoptyk._fetch_json", side_effect=responses):
            with self.assertRaisesRegex(ValueError, "Nieprawidłowa odpowiedź prognozy pogody"):
                synoptyk.get_forecast("Warszawa")

    def test_main_returns_non_zero_on_error(self):
        with patch("synoptyk.get_forecast", side_effect=ValueError("x")):
            with patch("sys.argv", ["synoptyk.py", "Warszawa"]):
                self.assertEqual(1, synoptyk.main())


if __name__ == "__main__":
    unittest.main()
