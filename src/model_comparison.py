from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

HORIZON = 6
SEASON_LENGTH = 52
CATEGORICAL = ["SKU", "Category"]
NUMERIC = [
    "lag_1", "lag_4", "lag_13", "lag_52",
    "mean_4", "mean_13", "week_sin", "week_cos",
]
FEATURES = CATEGORICAL + NUMERIC

weekly = pd.read_csv(DATA / "weekly_sales.csv", parse_dates=["Week_Start"])
weekly = weekly.sort_values(["SKU", "Week_Start"]).copy()

# Build every feature from earlier weeks only.
grouped = weekly.groupby("SKU")["Units_Sold"]
for lag in [1, 4, 13, 52]:
    weekly[f"lag_{lag}"] = grouped.shift(lag)

for window in [4, 13]:
    weekly[f"mean_{window}"] = grouped.transform(
        lambda values: values.shift(1).rolling(window).mean()
    )

week_number = weekly["Week_Start"].dt.isocalendar().week.astype(int)
weekly["week_sin"] = np.sin(2 * np.pi * week_number / 52)
weekly["week_cos"] = np.cos(2 * np.pi * week_number / 52)

panel = weekly.pivot(
    index="Week_Start", columns="SKU", values="Units_Sold"
).sort_index()
weeks = panel.index
categories = weekly.drop_duplicates("SKU").set_index("SKU")["Category"].to_dict()

# Use the same rolling origins and baseline results as the earlier backtest.
first_origin = SEASON_LENGTH + 26
origins = list(range(first_origin, len(weeks) - HORIZON + 1, HORIZON))
feature_rows = weekly.dropna(subset=FEATURES).copy()
model_results = []

def make_model():
    encoder = ColumnTransformer(
        [("product", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)],
        remainder="passthrough",
    )
    forest = RandomForestRegressor(
        n_estimators=200,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    return make_pipeline(encoder, forest)

def make_future_features(history, sku, category, week):
    week_number = int(week.isocalendar().week)
    return pd.DataFrame([{
        "SKU": sku,
        "Category": category,
        "lag_1": history[-1],
        "lag_4": history[-4],
        "lag_13": history[-13],
        "lag_52": history[-52],
        "mean_4": float(np.mean(history[-4:])),
        "mean_13": float(np.mean(history[-13:])),
        "week_sin": np.sin(2 * np.pi * week_number / 52),
        "week_cos": np.cos(2 * np.pi * week_number / 52),
    }], columns=FEATURES)

for origin in origins:
    origin_week = weeks[origin]
    train = feature_rows[feature_rows["Week_Start"] < origin_week]
    model = make_model()
    model.fit(train[FEATURES], train["Units_Sold"])

    for sku in panel.columns:
        history = panel[sku].iloc[:origin].astype(float).tolist()

        for step in range(HORIZON):
            target_week = weeks[origin + step]
            row = make_future_features(
                history, sku, categories[sku], target_week
            )
            prediction = max(0.0, float(model.predict(row)[0]))
            actual = float(panel.loc[target_week, sku])

            model_results.append({
                "Origin_Week": weeks[origin - 1],
                "Week_Start": target_week,
                "SKU": sku,
                "Actual_Units": actual,
                "Forecast_Units": prediction,
            })
            history.append(prediction)

model_backtest = pd.DataFrame(model_results)
baseline = pd.read_csv(
    REPORTS / "seasonal_naive_backtest.csv",
    parse_dates=["Origin_Week", "Week_Start"],
)

def calculate_metrics(frame):
    actual_total = frame["Actual_Units"].sum()
    wape = (
        (frame["Actual_Units"] - frame["Forecast_Units"]).abs().sum()
        / actual_total
    )
    bias = (
        (frame["Forecast_Units"] - frame["Actual_Units"]).sum()
        / actual_total
    )
    return float(wape), float(bias)

baseline_wape, baseline_bias = calculate_metrics(baseline)
model_wape, model_bias = calculate_metrics(model_backtest)

# Train on all available history for the next six weeks.
final_train = feature_rows[feature_rows["Week_Start"] <= weeks[-1]]
final_model = make_model()
final_model.fit(final_train[FEATURES], final_train["Units_Sold"])

future_weeks = pd.date_range(
    start=weeks[-1] + pd.Timedelta(weeks=1),
    periods=HORIZON,
    freq="W-MON",
)
future_rows = []

for sku in panel.columns:
    history = panel[sku].astype(float).tolist()

    for forecast_week in future_weeks:
        row = make_future_features(
            history, sku, categories[sku], forecast_week
        )
        prediction = max(0.0, float(final_model.predict(row)[0]))
        future_rows.append({
            "Week_Start": forecast_week,
            "SKU": sku,
            "Forecast_Units": prediction,
        })
        history.append(prediction)

model_future = pd.DataFrame(future_rows)
baseline_future = pd.read_csv(
    DATA / "seasonal_naive_forecast.csv",
    parse_dates=["Week_Start"],
)

if model_wape < baseline_wape:
    selected = model_future.copy()
    selected_model = "Random Forest"
else:
    selected = baseline_future[["Week_Start", "SKU", "Forecast_Units"]].copy()
    selected_model = "Seasonal naive (52-week lag)"

selected["Selected_Model"] = selected_model

model_backtest.to_csv(REPORTS / "model_backtest.csv", index=False)
model_future.to_csv(DATA / "random_forest_forecast.csv", index=False)
selected.to_csv(DATA / "selected_forecast.csv", index=False)

comparison = {
    "backtest_origins": len(origins),
    "seasonal_naive_WAPE": baseline_wape,
    "seasonal_naive_bias": baseline_bias,
    "random_forest_WAPE": model_wape,
    "random_forest_bias": model_bias,
    "selected_model": selected_model,
}
(REPORTS / "model_comparison.json").write_text(
    json.dumps(comparison, indent=2),
    encoding="utf-8",
)

print(f"Seasonal-naive WAPE: {baseline_wape:.1%}; bias: {baseline_bias:.1%}")
print(f"Random Forest WAPE: {model_wape:.1%}; bias: {model_bias:.1%}")
print(f"Selected model: {selected_model}")
print(f"Forecasts saved to: {DATA / 'selected_forecast.csv'}")