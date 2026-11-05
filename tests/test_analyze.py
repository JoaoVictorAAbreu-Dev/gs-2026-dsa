import unittest

import pandas as pd

import numpy as np

from src.analyze import band_alerts, band_of, backtest, evaluate_horizon, feature_table, indicator_table, scores


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


    def test_target_delta_is_future_minus_current(self):
        dates = pd.date_range("2024-01-01", periods=16)
        frame = pd.DataFrame({"date": dates, "storage_pct": list(range(16)), "rain_mm": [0] * 16})
        table = feature_table(frame, horizon_days=7)
        self.assertTrue((table["target_delta"] == 7).all())


def declining_series(days: int = 700) -> pd.DataFrame:
    """Synthetic fixture: steady decline, so the test period is below the training range."""
    dates = pd.date_range("2024-01-01", periods=days)
    rng = np.random.default_rng(1)
    storage = np.linspace(80, 20, days) + rng.normal(0, 0.02, days)
    return pd.DataFrame({"date": dates, "storage_pct": storage, "rain_mm": rng.uniform(0, 5, days)})


class ModelTests(unittest.TestCase):
    def test_models_follow_decline_outside_training_range(self):
        frame = declining_series()
        evaluation, _, _ = evaluate_horizon(frame, 1, split=pd.Timestamp("2025-06-01"))
        metrics = evaluation["metrics"]
        # Predicting the change lets the forest track levels never seen in training.
        self.assertLess(metrics["random_forest"]["mae_percentage_points"], 1.0)
        self.assertLess(metrics["ridge"]["mae_percentage_points"], metrics["persistence"]["mae_percentage_points"])

    def test_backtest_has_one_fold_per_origin(self):
        frame = declining_series()
        origins = [pd.Timestamp("2024-08-01"), pd.Timestamp("2025-01-01")]
        result = backtest(frame, 1, origins)
        self.assertEqual([f["origin"] for f in result["folds"]], ["2024-08-01", "2025-01-01"])
        self.assertTrue(all(f["test_rows"] >= 30 for f in result["folds"]))

    def test_bias_sign_means_optimistic(self):
        result = scores(np.array([10.0, 10.0]), np.array([11.0, 12.0]))
        self.assertAlmostEqual(result["bias_percentage_points"], 1.5)
        self.assertAlmostEqual(result["max_abs_error_percentage_points"], 2.0)


class ReferenceVolumeBandTests(unittest.TestCase):
    def test_reference_band_boundaries_follow_resolution_thresholds(self):
        # >=60 Normal, [40,60) Atenção, [30,40) Alerta, [20,30) Restrição, <20 Especial
        self.assertEqual(list(band_of([60, 59.99, 40, 39.99, 30, 29.99, 20, 19.99])), [1, 2, 2, 3, 3, 4, 4, 5])

    def test_persistence_never_warns_and_transitions_are_found(self):
        result = band_alerts(declining_series(), 7)
        self.assertGreater(result["days_with_real_worsening"], 0)
        self.assertEqual(result["models"]["persistence"]["true_alerts"], 0)
        self.assertGreater(result["models"]["ridge"]["recall"], 0.5)
        self.assertTrue(all(t["new_band"] in (2, 3, 4, 5) for t in result["band_transitions_observed"]))


class IndicatorTests(unittest.TestCase):
    def test_indicator_formulas(self):
        dates = pd.date_range("2024-01-01", periods=31)
        frame = pd.DataFrame({"date": dates, "storage_pct": [50 - 0.5 * i for i in range(31)], "rain_mm": [2] * 31})
        last = indicator_table(frame).iloc[-1]
        self.assertAlmostEqual(last["storage_change_7d_pp"], -3.5)
        self.assertAlmostEqual(last["storage_change_30d_pp"], -15.0)
        self.assertAlmostEqual(last["rain_30d_mm"], 60.0)


if __name__ == "__main__":
    unittest.main()
