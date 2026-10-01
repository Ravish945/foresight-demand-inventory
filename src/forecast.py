from pathlib import Path
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "weekly_sales.csv"
OUTPUT = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

HORIZON = 6
SEASON_LENGTH = 52

weekly = pd.read_csv(INPUT, parse_dates=["Week_Start"])

# Put each SKU's weekly demand in its own column.
panel = weekly.pivot(
    index="Week_Start",
    columns="SKU",
    values="Units_Sold",
).sort_index()

weeks = panel.index
if len(weeks) < SEASON_LENGTH + HORIZON + 26:
    raise ValueError("Not enough weekly history for this baseline backtest.")

if panel.isna().any().any():
    raise ValueError("Some SKU-week values are missing; review the weekly data first.")

# Each origin predicts the next six weeks using the same weeks from the prior year.
first_origin = SEASON_LENGTH + 26
origins = range(first_origin, len(weeks) - HORIZON + 1, HORIZON)
backtest_rows = []

for origin in origins:
    for sku in panel.columns:
        values = panel[sku].to_numpy(dtype=float)

        for step in range(HORIZON):
            target_index = origin + step
            actual = values[target_index]
            forecast = values[target_index - SEASON_LENGTH]

            backtest_rows.append({
                "Origin_Week": weeks[origin - 1],
                "Week_Start": weeks[target_index],
                "SKU": sku,
                "Actual_Units": actual,
                "Forecast_Units": forecast,
            })

backtest = pd.DataFrame(backtest_rows)
backtest["Absolute_Error"] = (
    backtest["Actual_Units"] - backtest["Forecast_Units"]
).abs()

total_actual = backtest["Actual_Units"].sum()
wape = (
    backtest["Absolute_Error"].sum() / total_actual
    if total_actual != 0 else np.nan
)
bias = (
    (backtest["Forecast_Units"] - backtest["Actual_Units"]).sum()
    / total_actual
    if total_actual != 0 else np.nan
)

# Create the next six weeks of seasonal-naive forecasts.
future_weeks = pd.date_range(
    start=weeks[-1] + pd.Timedelta(weeks=1),
    periods=HORIZON,
    freq="W-MON",
)

future_rows = []
for sku in panel.columns:
    values = panel[sku].to_numpy(dtype=float)

    for step, forecast_week in enumerate(future_weeks):
        future_rows.append({
            "Week_Start": forecast_week,
            "SKU": sku,
            "Forecast_Units": max(0, values[len(values) - SEASON_LENGTH + step]),
            "Model": "Seasonal naive (52-week lag)",
        })

future = pd.DataFrame(future_rows)

backtest.to_csv(REPORTS / "seasonal_naive_backtest.csv", index=False)
future.to_csv(OUTPUT / "seasonal_naive_forecast.csv", index=False)

metrics = {
    "model": "Seasonal naive (52-week lag)",
    "forecast_horizon_weeks": HORIZON,
    "backtest_origins": len(list(origins)),
    "WAPE": float(wape),
    "Bias": float(bias),
    "bias_interpretation": (
        "positive means over-forecast; negative means under-forecast"
    ),
}
(REPORTS / "baseline_metrics.json").write_text(
    json.dumps(metrics, indent=2),
    encoding="utf-8",
)

print(f"Baseline backtest complete across {metrics['backtest_origins']} origins.")
print(f"WAPE: {wape:.1%}")
print(f"Bias: {bias:.1%} ({metrics['bias_interpretation']})")
print(f"Next-six-week forecasts saved to: {OUTPUT / 'seasonal_naive_forecast.csv'}")