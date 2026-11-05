"""Exploratory checks, water indicators and honest 1/7-day baselines on real Cantareira data."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.quality import inspect_csv


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/cantareira_daily.csv"
OUT = ROOT / "reports"
SPLIT = pd.Timestamp("2025-07-01")
# Rolling-origin backtest: each fold trains on targets before the origin and tests the next 3 months.
BACKTEST_ORIGINS = [pd.Timestamp(d) for d in ("2024-10-01", "2025-01-01", "2025-04-01", "2025-07-01", "2025-10-01")]
FEATURES = ["storage_pct", "storage_7d_mean", "storage_7d_delta", "rain_mm", "rain_7d_sum"]

# Documented indicators (DSA-04): formula, unit, periodicity and interpretation.
INDICATORS = {
    "storage_pct": {
        "formula": "volumeUtilArmazenadoPorcentagem published by Sabesp for day t",
        "unit": "% of useful volume",
        "periodicity": "daily",
        "interpretation": "Current useful storage; level only, without official stage thresholds.",
    },
    "storage_change_7d_pp": {
        "formula": "storage_pct(t) - storage_pct(t-7)",
        "unit": "percentage points (p.p.)",
        "periodicity": "daily, 7-day window",
        "interpretation": "Negative values mean the reservoir lost useful volume in the last week.",
    },
    "storage_change_30d_pp": {
        "formula": "storage_pct(t) - storage_pct(t-30)",
        "unit": "percentage points (p.p.)",
        "periodicity": "daily, 30-day window",
        "interpretation": "Monthly trend; smooths daily noise. Sustained negative values deserve human review.",
    },
    "rain_30d_mm": {
        "formula": "sum of rain_mm from t-29 to t",
        "unit": "mm",
        "periodicity": "daily, 30-day window",
        "interpretation": "Recent rainfall context. Low totals with falling storage reinforce the need for review.",
    },
}


def feature_table(frame: pd.DataFrame, horizon_days: int = 1) -> pd.DataFrame:
    """Use observations available by date t to predict storage on date t+h."""
    if horizon_days < 1:
        raise ValueError("horizon_days must be positive")
    data = frame.sort_values("date").copy()
    if data["date"].duplicated().any():
        raise ValueError("Duplicate dates")
    if (data["date"].diff().dropna() != pd.Timedelta(days=1)).any():
        raise ValueError("This experiment requires consecutive daily dates")
    data["storage_7d_mean"] = data["storage_pct"].rolling(7, min_periods=7).mean()
    data["storage_7d_delta"] = data["storage_pct"] - data["storage_pct"].shift(7)
    data["rain_7d_sum"] = data["rain_mm"].rolling(7, min_periods=7).sum()
    data["target_date"] = data["date"].shift(-horizon_days)
    data["target_next_day"] = data["storage_pct"].shift(-horizon_days)
    # Models learn the change, not the level: trees cannot extrapolate levels outside the
    # training range (test volumes fell below anything seen in training), but changes stay comparable.
    data["target_delta"] = data["target_next_day"] - data["storage_pct"]
    return data.dropna(subset=FEATURES + ["target_next_day"]).copy()


def indicator_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Compute the documented indicators for each day (NaN until the window is complete)."""
    data = frame.sort_values("date").copy()
    data["storage_change_7d_pp"] = data["storage_pct"] - data["storage_pct"].shift(7)
    data["storage_change_30d_pp"] = data["storage_pct"] - data["storage_pct"].shift(30)
    data["rain_30d_mm"] = data["rain_mm"].rolling(30, min_periods=30).sum()
    return data[["date", *INDICATORS]]


def scores(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    """MAE/RMSE plus bias and worst case; bias > 0 means the model is optimistic (predicts more water)."""
    errors = np.asarray(predicted) - np.asarray(actual)
    return {
        "mae_percentage_points": float(mean_absolute_error(actual, predicted)),
        "rmse_percentage_points": float(np.sqrt(mean_squared_error(actual, predicted))),
        "bias_percentage_points": float(errors.mean()),
        "max_abs_error_percentage_points": float(np.abs(errors).max()),
    }


def _models() -> dict:
    return {
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "random_forest": RandomForestRegressor(
            n_estimators=150, max_depth=6, min_samples_leaf=4, random_state=2026, n_jobs=1
        ),
    }


def _fit_predict(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, np.ndarray]:
    predictions = {"persistence": test["storage_pct"].to_numpy()}
    for name, model in _models().items():
        model.fit(train[FEATURES], train["target_delta"])
        predictions[name] = test["storage_pct"].to_numpy() + model.predict(test[FEATURES])
    return predictions


def evaluate_horizon(
    frame: pd.DataFrame, horizon_days: int, split: pd.Timestamp = SPLIT, test_end: pd.Timestamp | None = None
) -> tuple[dict, pd.DataFrame, dict]:
    table = feature_table(frame, horizon_days=horizon_days)
    train = table[table["target_date"] < split]
    test = table[table["target_date"] >= split]
    if test_end is not None:
        test = test[test["target_date"] < test_end]
    if len(train) < 100 or len(test) < 30:
        raise ValueError("Not enough chronological training/test observations")

    predictions = _fit_predict(train, test)
    y_test = test["target_next_day"].to_numpy()
    evaluation = {
        "horizon_days": horizon_days,
        "target": f"volumeUtilArmazenadoPorcentagem {horizon_days} day(s) after prediction date",
        "model_target": "change in percentage points, added back to storage_pct(t)",
        "train_rows": len(train),
        "test_rows": len(test),
        "test_target_from": test["target_date"].min().date().isoformat(),
        "test_target_to": test["target_date"].max().date().isoformat(),
        "metrics": {name: scores(y_test, predicted) for name, predicted in predictions.items()},
    }
    return evaluation, test, predictions


def backtest(frame: pd.DataFrame, horizon_days: int, origins: list[pd.Timestamp] = BACKTEST_ORIGINS) -> dict:
    """Rolling-origin evaluation: one fold per origin, each testing the following three months."""
    folds = []
    for origin in origins:
        evaluation, _, _ = evaluate_horizon(frame, horizon_days, origin, origin + pd.DateOffset(months=3))
        folds.append({
            "origin": origin.date().isoformat(),
            "train_rows": evaluation["train_rows"],
            "test_rows": evaluation["test_rows"],
            "mae_percentage_points": {
                name: metric["mae_percentage_points"] for name, metric in evaluation["metrics"].items()
            },
        })
    names = folds[0]["mae_percentage_points"].keys()
    return {
        "horizon_days": horizon_days,
        "folds": folds,
        "mean_mae_percentage_points": {
            name: float(np.mean([fold["mae_percentage_points"][name] for fold in folds])) for name in names
        },
        "folds_beating_persistence": {
            name: sum(fold["mae_percentage_points"][name] < fold["mae_percentage_points"]["persistence"] for fold in folds)
            for name in names if name != "persistence"
        },
    }


def run(data_path: Path = DATA, out_dir: Path = OUT) -> dict:
    report = inspect_csv(data_path, "Sabesp Portal dos Mananciais, local normalized copy")
    if not report.usable or any(report.date_gaps.values()):
        raise ValueError(f"Data quality check failed: {report}")
    frame = pd.read_csv(data_path, parse_dates=["date"])
    if frame[["storage_pct", "rain_mm"]].isna().any().any():
        raise ValueError("Missing storage or rain values; choose/document handling first")
    one_day, test, predictions = evaluate_horizon(frame, 1)
    seven_day, _, _ = evaluate_horizon(frame, 7)
    indicators = indicator_table(frame)
    latest = indicators.dropna().iloc[-1]
    y_test = test["target_next_day"]
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "question": "How accurately can Cantareira useful storage percentage be estimated 1 and 7 days ahead?",
        "scope": "Single system, daily observations, 1- and 7-day horizons; no neighborhood supply prediction",
        "source": "Sabesp Portal dos Mananciais; see docs/DATA_SOURCE.md",
        "period": [report.first_date, report.last_date],
        "rows": report.rows,
        "missing_daily_dates": report.date_gaps,
        "storage_pct_summary": {
            "min": float(frame["storage_pct"].min()),
            "median": float(frame["storage_pct"].median()),
            "max": float(frame["storage_pct"].max()),
        },
        "rain_mm_summary": {
            "sum": float(frame["rain_mm"].sum()),
            "zero_days": int((frame["rain_mm"] == 0).sum()),
        },
        "indicators": {
            "definitions": INDICATORS,
            "latest_date": latest["date"].date().isoformat(),
            "latest": {name: float(latest[name]) for name in INDICATORS},
            "worst_30d_change_pp": float(indicators["storage_change_30d_pp"].min()),
        },
        "target": "volumeUtilArmazenadoPorcentagem on the following day",
        "feature_date_constraint": "all features observed on or before prediction date",
        "split": {
            "train_target_before": SPLIT.date().isoformat(),
            "train_rows": one_day["train_rows"],
            "test_rows": one_day["test_rows"],
            "test_target_from": test["target_date"].min().date().isoformat(),
            "test_target_to": test["target_date"].max().date().isoformat(),
        },
        "metrics": one_day["metrics"],
        "seven_day_horizon": seven_day,
        "backtest": {"one_day": backtest(frame, 1), "seven_day": backtest(frame, 7)},
        "warning": "These are exploratory regression results, not validated risk alerts or racionamento decisions.",
    }
    (out_dir / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    figure, axes = plt.subplots(3, 1, figsize=(12, 10), constrained_layout=True)
    axes[0].plot(frame["date"], frame["storage_pct"], color="#146c94")
    axes[0].axvline(SPLIT, color="#d97706", linestyle="--", label="Train/test boundary")
    axes[0].set(title="Cantareira: useful storage (Sabesp daily data)", ylabel="% useful volume")
    axes[0].legend()
    axes[1].plot(indicators["date"], indicators["storage_change_30d_pp"], color="#9b2226", label="30-day change (p.p.)")
    axes[1].axhline(0, color="#555", linewidth=0.8)
    rain_axis = axes[1].twinx()
    rain_axis.bar(indicators["date"], indicators["rain_30d_mm"], color="#94d2bd", alpha=0.4, width=1.0)
    rain_axis.set_ylabel("30-day rain (mm)")
    axes[1].set(title="Indicators: 30-day storage change and 30-day rain", ylabel="p.p.")
    axes[1].legend(loc="upper left")
    axes[2].plot(test["target_date"], y_test, label="Observed", color="#146c94")
    axes[2].plot(test["target_date"], predictions["ridge"], label="Ridge", alpha=0.7)
    axes[2].plot(test["target_date"], predictions["random_forest"], label="Random forest", alpha=0.7)
    axes[2].set(title="One-day-ahead test period", ylabel="% useful volume", xlabel="Date")
    axes[2].legend()
    figure.savefig(out_dir / "overview.png", dpi=150)
    plt.close(figure)
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
