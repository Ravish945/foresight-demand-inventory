from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

PROCESSED.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)


def read_csv(filename):
    path = RAW / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    return pd.read_csv(path)


def clean_sku(series):
    return series.astype("string").str.strip().str.upper()


sales = read_csv("sales_daily.csv")
products = read_csv("sku_master.csv")
calendar = read_csv("calendar.csv")
inventory = read_csv("inventory_snapshots.csv")

quality = {
    "source_rows": {
        "sales_daily": len(sales),
        "sku_master": len(products),
        "calendar": len(calendar),
        "inventory_snapshots": len(inventory),
    },
    "missing_values_before_cleaning": {
        name: {str(k): int(v) for k, v in frame.isna().sum().items() if v}
        for name, frame in {
            "sales_daily": sales,
            "sku_master": products,
            "calendar": calendar,
            "inventory_snapshots": inventory,
        }.items()
    },
    "exact_duplicate_rows_removed": {},
}

# Remove exact duplicate rows and record how many were found.
tables = {
    "sales_daily": sales,
    "sku_master": products,
    "calendar": calendar,
    "inventory_snapshots": inventory,
}
for name, frame in tables.items():
    duplicate_count = int(frame.duplicated().sum())
    quality["exact_duplicate_rows_removed"][name] = duplicate_count
    tables[name] = frame.drop_duplicates().copy()

sales = tables["sales_daily"]
products = tables["sku_master"]
calendar = tables["calendar"]
inventory = tables["inventory_snapshots"]

# Standardize IDs, dates, and numeric fields.
sales["Date"] = pd.to_datetime(sales["Date"], errors="coerce")
sales["SKU"] = clean_sku(sales["SKU"])
for col in ["Units_Sold", "Revenue", "Price", "Promotion"]:
    sales[col] = pd.to_numeric(sales[col], errors="coerce")

products["SKU"] = clean_sku(products["SKU"])
products["Launch_Date"] = pd.to_datetime(products["Launch_Date"], errors="coerce")
for col in ["Cost_Price", "Selling_Price", "Gross_Margin_Per_Unit"]:
    products[col] = pd.to_numeric(products[col], errors="coerce")

calendar["date"] = pd.to_datetime(calendar["date"], errors="coerce")
inventory["Snapshot_Date"] = pd.to_datetime(
    inventory["Snapshot_Date"], errors="coerce"
)
inventory["SKU"] = clean_sku(inventory["SKU"])
for col in [
    "Current_Stock", "On_Order", "Lead_Time_Days",
    "Safety_Stock", "Reorder_Point", "Inventory_Value",
]:
    inventory[col] = pd.to_numeric(inventory[col], errors="coerce")

# Remove rows that cannot be joined or interpreted.
sales = sales.dropna(subset=["Date", "SKU", "Units_Sold"]).copy()
products = products.dropna(subset=["SKU"]).copy()
calendar = calendar.dropna(subset=["date"]).copy()
inventory = inventory.dropna(subset=["Snapshot_Date", "SKU"]).copy()

# These tables are defined at one row per key. Stop if keys are duplicated.
checks = [
    (sales, ["Date", "SKU"], "sales_daily"),
    (products, ["SKU"], "sku_master"),
    (calendar, ["date"], "calendar"),
    (inventory, ["Snapshot_Date", "SKU"], "inventory_snapshots"),
]
for frame, keys, name in checks:
    if frame.duplicated(keys).any():
        raise ValueError(f"{name} has duplicate key rows for {keys}; review before joining.")

# Blank holiday/event labels mean no label was supplied; retain that explicitly.
for col in ["holiday", "promotion_event"]:
    if col in calendar.columns:
        calendar[col] = calendar[col].fillna("Not recorded")

# Check that sales can be matched to the product and calendar tables.
unknown_skus = sorted(set(sales["SKU"]) - set(products["SKU"]))
unknown_dates = sorted(set(sales["Date"]) - set(calendar["date"]))
quality["sales_skus_missing_from_master"] = unknown_skus
quality["sales_dates_missing_from_calendar"] = len(unknown_dates)

if unknown_skus or unknown_dates:
    raise ValueError("Some sales rows do not match the SKU master or calendar.")

# Add product and calendar details to each sales row.
enriched = sales.merge(products, on="SKU", how="left", validate="many_to_one")
enriched = enriched.merge(
    calendar, left_on="Date", right_on="date",
    how="left", validate="many_to_one"
)

# Aggregate daily sales into Monday-start weeks by SKU.
enriched["Week_Start"] = (
    enriched["Date"].dt.to_period("W-SUN").dt.start_time
)
weekly = (
    enriched.groupby(["Week_Start", "SKU", "Product_Name", "Category"], as_index=False)
    .agg(
        Units_Sold=("Units_Sold", "sum"),
        Revenue=("Revenue", "sum"),
        Average_Price=("Price", "mean"),
        Promotion=("Promotion", "max"),
    )
)

sales.to_csv(PROCESSED / "sales_daily_clean.csv", index=False)
products.to_csv(PROCESSED / "sku_master_clean.csv", index=False)
calendar.to_csv(PROCESSED / "calendar_clean.csv", index=False)
inventory.to_csv(PROCESSED / "inventory_snapshots_clean.csv", index=False)
enriched.to_csv(PROCESSED / "sales_enriched.csv", index=False)
weekly.to_csv(PROCESSED / "weekly_sales.csv", index=False)
master_skus = set(products["SKU"])
sales_skus = set(sales["SKU"])
inventory_skus = set(inventory["SKU"])

quality["inventory_skus_missing_from_master"] = sorted(
    inventory_skus - master_skus
)
quality["inventory_skus_without_sales"] = sorted(
    inventory_skus - sales_skus
)
quality["inventory_skus_linked_to_sales_and_master"] = len(
    inventory_skus & sales_skus & master_skus
)
quality["inventory_latest_snapshot_date"] = (
    inventory["Snapshot_Date"].max().strftime("%Y-%m-%d")
)
quality["days_between_latest_sales_and_inventory"] = (
    sales["Date"].max() - inventory["Snapshot_Date"].max()
).days
quality["cleaned_rows"] = {
    "sales_daily": len(sales),
    "sku_master": len(products),
    "calendar": len(calendar),
    "inventory_snapshots": len(inventory),
    "sales_enriched": len(enriched),
    "weekly_sales": len(weekly),
}
(REPORTS / "data_quality_report.json").write_text(
    json.dumps(quality, indent=2, default=str),
    encoding="utf-8",
)

print("Pipeline complete.")
print(f"Cleaned weekly sales: {len(weekly):,} rows")
print(f"Outputs saved in: {PROCESSED}")
print(f"Data-quality report saved in: {REPORTS}")