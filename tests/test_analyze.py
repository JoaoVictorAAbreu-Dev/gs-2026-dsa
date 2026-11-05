import unittest

import pandas as pd

from src.analyze import feature_table


class FeatureTests(unittest.TestCase):
    def test_next_day_target_uses_future_only_for_label(self):
        dates = pd.date_range("2024-01-01", periods=10)
        frame = pd.DataFrame({"date": dates, "storage_pct": list(range(10)), "rain_mm": [0] * 10})
        table = feature_table(frame)
        first = table.iloc[0]
        self.assertEqual(first["storage_pct"], 7)
        self.assertEqual(first["target_next_day"], 8)
        self.assertEqual(first["target_date"], dates[8])

    def test_gap_rejected(self):
        frame = pd.DataFrame({
            "date": pd.to_datetime(["2024-01-01", "2024-01-03"]),
            "storage_pct": [1, 2],
            "rain_mm": [0, 0],
        })
        with self.assertRaisesRegex(ValueError, "consecutive"):
            feature_table(frame)

    def test_seven_day_horizon(self):
        dates = pd.date_range("2024-01-01", periods=16)
        frame = pd.DataFrame({"date": dates, "storage_pct": list(range(16)), "rain_mm": [0] * 16})
        table = feature_table(frame, horizon_days=7)
        first = table.iloc[0]
        self.assertEqual(first["storage_pct"], 7)
        self.assertEqual(first["target_next_day"], 14)
        self.assertEqual(first["target_date"], dates[14])


if __name__ == "__main__":
    unittest.main()
