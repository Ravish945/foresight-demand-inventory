from pathlib import Path
import json
import math

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"

forecast = pd.read_csv(
    DATA / "selected_forecast.csv",
    parse_dates=["Week_Start"],
)
inventory = pd.read_csv(
    RAW / "inventory_snapshots.csv",
    parse_dates=["Snapshot_Date"],
)
products = pd.read_csv(RAW / "sku_master.csv")

for frame in [forecast, inventory, products]:
    frame["SKU"] = frame["SKU"].astype(str).str.strip().str.upper()

# Keep the latest available stock snapshot for each SKU.
latest_inventory = (
    inventory.sort_values("Snapshot_Date")
    .groupby("SKU", as_index=False)
    .tail(1)
    .copy()
)

# Keep a separate record of inventory SKUs that lack sales/product data.
known_skus = set(products["SKU"])
forecast_skus = set(forecast["SKU"])
inventory_skus = set(latest_inventory["SKU"])
unmatched_skus = sorted(inventory_skus - known_skus - forecast_skus)
pd.DataFrame({"Unmatched_Inventory_SKU": unmatched_skus}).to_csv(
    REPORTS / "unmatched_inventory_skus.csv",
    index=False,
)

# Summarize the six-week forecast for each SKU.
forecast = forecast.sort_values(["SKU", "Week_Start"])
forecast_summary = (
    forecast.groupby("SKU", as_index=False)
    .agg(
        Six_Week_Forecast=("Forecast_Units", "sum"),
        Forecast_Weeks=("Week_Start", "nunique"),
        First_Forecast_Week=("Week_Start", "min"),
    )
)

# Keep only SKUs present in all three required sources.
risk = latest_inventory.merge(
    products,
    on="SKU",
    how="inner",
    validate="one_to_one",
).merge(
    forecast_summary,
    on="SKU",
    how="inner",
    validate="one_to_one",
)

if risk.empty:
    raise ValueError("No SKUs match across inventory, product, and forecast data.")

# Estimate demand during lead time by prorating weekly forecasts by day.
forecast_by_sku = {
    sku: group.sort_values("Week_Start")["Forecast_Units"].tolist()
    for sku, group in forecast.groupby("SKU")
}

def lead_time_demand(sku, lead_days):
    remaining_days = int(lead_days)
    demand = 0.0

    for weekly_units in forecast_by_sku.get(sku, []):
        days_in_week = min(7, remaining_days)
        demand += float(weekly_units) * days_in_week / 7
        remaining_days -= days_in_week
        if remaining_days <= 0:
            break

    return demand

risk["Lead_Time_Demand"] = risk.apply(
    lambda row: lead_time_demand(row["SKU"], row["Lead_Time_Days"]),
    axis=1,
)
risk["Available_Units"] = risk["Current_Stock"] + risk["On_Order"]
risk["Projected_Stock_After_Lead_Time"] = (
    risk["Available_Units"] - risk["Lead_Time_Demand"]
)

risk["Stockout_Risk"] = (
    (risk["Available_Units"] <= risk["Reorder_Point"])
    | (risk["Projected_Stock_After_Lead_Time"] < risk["Safety_Stock"])
)

# Flag stock above 12 weeks of expected demand as potential overstock.
risk["Overstock_Threshold_Units"] = 2 * risk["Six_Week_Forecast"]
risk["Overstock_Risk"] = (
    risk["Current_Stock"] > risk["Overstock_Threshold_Units"]
)

risk["Lost_Sales_Units_At_Risk"] = (
    risk["Lead_Time_Demand"] - risk["Available_Units"]
).clip(lower=0)
risk["Estimated_Sales_At_Risk"] = (
    risk["Lost_Sales_Units_At_Risk"] * risk["Selling_Price"]
)

risk["Potential_Excess_Units"] = (
    risk["Current_Stock"] - risk["Overstock_Threshold_Units"]
).clip(lower=0)
risk["Estimated_Capital_Locked"] = (
    risk["Potential_Excess_Units"] * risk["Cost_Price"]
)

risk["Recommended_Order_Units"] = risk.apply(
    lambda row: (
        math.ceil(
            max(row["Reorder_Point"], row["Lead_Time_Demand"] + row["Safety_Stock"])
            - row["Available_Units"]
        )
        if row["Stockout_Risk"] else 0
    ),
    axis=1,
)

def choose_action(row):
    if row["Stockout_Risk"] and row["Overstock_Risk"]:
        return "Watch / investigate"
    if row["Stockout_Risk"]:
        return "Reorder now"
    if row["Overstock_Risk"]:
        return "Markdown / clear"
    return "Healthy"

risk["Recommended_Action"] = risk.apply(choose_action, axis=1)
risk["Risk_Level"] = risk["Recommended_Action"].map({
    "Reorder now": "High stockout",
    "Markdown / clear": "High overstock",
    "Watch / investigate": "High on both",
    "Healthy": "Low",
})

risk["Inventory_As_Of"] = risk["Snapshot_Date"].dt.strftime("%Y-%m-%d")
risk["Snapshot_Age_Days_At_Forecast_Start"] = (
    risk["First_Forecast_Week"] - risk["Snapshot_Date"]
).dt.days

columns_to_save = [
    "SKU", "Product_Name", "Category", "Snapshot_Date",
    "Current_Stock", "On_Order", "Available_Units",
    "Lead_Time_Days", "Safety_Stock", "Reorder_Point",
    "Lead_Time_Demand", "Projected_Stock_After_Lead_Time",
    "Six_Week_Forecast", "Stockout_Risk", "Overstock_Risk",
    "Risk_Level", "Recommended_Action", "Recommended_Order_Units",
    "Estimated_Sales_At_Risk", "Potential_Excess_Units",
    "Estimated_Capital_Locked", "Snapshot_Age_Days_At_Forecast_Start",
]
risk[columns_to_save].to_csv(REPORTS / "inventory_risk_scores.csv", index=False)

summary = {
    "matched_skus_scored": int(len(risk)),
    "inventory_skus_without_sales_and_product_match": int(len(unmatched_skus)),
    "inventory_as_of": str(risk["Snapshot_Date"].max().date()),
    "first_forecast_week": str(risk["First_Forecast_Week"].min().date()),
    "stockout_risk_skus": int(risk["Stockout_Risk"].sum()),
    "overstock_risk_skus": int(risk["Overstock_Risk"].sum()),
    "recommended_actions": {
        str(action): int(count)
        for action, count in risk["Recommended_Action"].value_counts().items()
    },
    "estimated_sales_at_risk_rupees": round(
        float(risk["Estimated_Sales_At_Risk"].sum()), 2
    ),
    "estimated_capital_locked_rupees": round(
        float(risk["Estimated_Capital_Locked"].sum()), 2
    ),
    "overstock_rule": "On-hand stock exceeds twice the six-week forecast.",
    "stockout_rule": (
        "Available stock is at/below reorder point, or projected stock "
        "after lead-time demand is below safety stock."
    ),
}
(REPORTS / "inventory_risk_summary.json").write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8",
)

print(f"Risk scores created for {len(risk)} matched SKUs.")
print(f"Unmatched inventory SKUs saved separately: {len(unmatched_skus)}")
print(f"Inventory snapshot date: {risk['Snapshot_Date'].max().date()}")
print(f"Results saved in: {REPORTS}")