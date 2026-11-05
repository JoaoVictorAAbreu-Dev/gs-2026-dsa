"""Exploratory checks and honest one-day-ahead baselines on real Cantareira data."""

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
FEATURES = ["storage_pct", "storage_7d_mean", "storage_7d_delta", "rain_mm", "rain_7d_sum"]


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
    return data.dropna(subset=FEATURES + ["target_next_day"]).copy()


def scores(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae_percentage_points": float(mean_absolute_error(actual, predicted)),
        "rmse_percentage_points": float(np.sqrt(mean_squared_error(actual, predicted))),
    }


def evaluate_horizon(frame: pd.DataFrame, horizon_days: int) -> tuple[dict, pd.DataFrame, dict]:
    table = feature_table(frame, horizon_days=horizon_days)
    train = table[table["target_date"] < SPLIT]
    test = table[table["target_date"] >= SPLIT]
    if len(train) < 100 or len(test) < 30:
        raise ValueError("Not enough chronological training/test observations")

    x_train, y_train = train[FEATURES], train["target_next_day"]
    x_test, y_test = test[FEATURES], test["target_next_day"]
    models = {
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "random_forest": RandomForestRegressor(
            n_estimators=150, max_depth=6, min_samples_leaf=4, random_state=2026, n_jobs=1
        ),
    }
    predictions = {"persistence": test["storage_pct"].to_numpy()}
    for name, model in models.items():
        model.fit(x_train, y_train)
        predictions[name] = model.predict(x_test)
    evaluation = {
        "horizon_days": horizon_days,
        "target": f"volumeUtilArmazenadoPorcentagem {horizon_days} day(s) after prediction date",
        "train_rows": len(train),
        "test_rows": len(test),
        "test_target_from": test["target_date"].min().date().isoformat(),
        "test_target_to": test["target_date"].max().date().isoformat(),
        "metrics": {
            name: scores(y_test.to_numpy(), predicted)
            for name, predicted in predictions.items()
        },
    }
    return evaluation, test, predictions


def run(data_path: Path = DATA, out_dir: Path = OUT) -> dict:
    report = inspect_csv(data_path, "Sabesp Portal dos Mananciais, local normalized copy")
    if not report.usable or any(report.date_gaps.values()):
        raise ValueError(f"Data quality check failed: {report}")
    frame = pd.read_csv(data_path, parse_dates=["date"])
    if frame[["storage_pct", "rain_mm"]].isna().any().any():
        raise ValueError("Missing storage or rain values; choose/document handling first")
    one_day, test, predictions = evaluate_horizon(frame, 1)
    seven_day, _, _ = evaluate_horizon(frame, 7)
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
        "warning": "These are exploratory regression results, not validated risk alerts or racionamento decisions.",
    }
    (out_dir / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    figure, axes = plt.subplots(2, 1, figsize=(12, 7), constrained_layout=True)
    axes[0].plot(frame["date"], frame["storage_pct"], color="#146c94")
    axes[0].axvline(SPLIT, color="#d97706", linestyle="--", label="Train/test boundary")
    axes[0].set(title="Cantareira: useful storage (Sabesp daily data)", ylabel="% useful volume")
    axes[0].legend()
    axes[1].plot(test["target_date"], y_test, label="Observed", color="#146c94")
    axes[1].plot(test["target_date"], predictions["ridge"], label="Ridge", alpha=0.7)
    axes[1].plot(
        test["target_date"], predictions["random_forest"], label="Random forest", alpha=0.7
    )
    axes[1].set(title="One-day-ahead test period", ylabel="% useful volume", xlabel="Date")
    axes[1].legend()
    figure.savefig(out_dir / "overview.png", dpi=150)
    plt.close(figure)
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
