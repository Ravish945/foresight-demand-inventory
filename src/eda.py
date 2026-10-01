from pathlib import Path
import pandas as pd
import plotly.express as px

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "processed" / "weekly_sales.csv"
FIGURES = ROOT / "reports" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

weekly = pd.read_csv(DATA_FILE, parse_dates=["Week_Start"])

# Summarize sales by SKU and category.
sku_summary = (
    weekly.groupby(["SKU", "Product_Name", "Category"], as_index=False)
    .agg(
        Total_Units=("Units_Sold", "sum"),
        Total_Revenue=("Revenue", "sum"),
        Average_Weekly_Units=("Units_Sold", "mean"),
    )
)

category_summary = (
    weekly.groupby("Category", as_index=False)
    .agg(Total_Units=("Units_Sold", "sum"), Total_Revenue=("Revenue", "sum"))
    .sort_values("Total_Revenue", ascending=False)
)

# Check for SKUs with no sales in the latest 13 weeks.
latest_week = weekly["Week_Start"].max()
recent_start = latest_week - pd.Timedelta(weeks=12)
recent = weekly[weekly["Week_Start"] >= recent_start]
recent_activity = recent.groupby("SKU").agg(
    Weeks_Observed=("Units_Sold", "size"),
    Weeks_With_Sales=("Units_Sold", lambda values: int((values > 0).sum())),
)
no_recent_sales = recent_activity[recent_activity["Weeks_With_Sales"] == 0]

# Weekly sales trend.
trend = weekly.groupby("Week_Start", as_index=False)["Units_Sold"].sum()
fig = px.line(
    trend, x="Week_Start", y="Units_Sold",
    title="Total Units Sold by Week",
    labels={"Week_Start": "Week", "Units_Sold": "Units sold"},
)
fig.write_html(FIGURES / "weekly_sales_trend.html", include_plotlyjs="cdn")

# Ten highest-selling SKUs.
top_skus = sku_summary.nlargest(10, "Total_Units").sort_values("Total_Units")
fig = px.bar(
    top_skus, x="Total_Units", y="SKU", orientation="h",
    title="Top 10 SKUs by Units Sold",
    labels={"SKU": "Product SKU", "Total_Units": "Units sold"},
)
fig.write_html(FIGURES / "top_skus.html", include_plotlyjs="cdn")

# Sales by product category.
fig = px.bar(
    category_summary, x="Category", y="Total_Revenue",
    title="Revenue by Category",
    labels={"Category": "Category", "Total_Revenue": "Revenue"},
)
fig.write_html(FIGURES / "category_revenue.html", include_plotlyjs="cdn")

# Average weekly unit sales by calendar month.
weekly["Month_Number"] = weekly["Week_Start"].dt.month
seasonality = (
    weekly.groupby("Month_Number", as_index=False)["Units_Sold"]
    .mean()
    .rename(columns={"Units_Sold": "Average_Weekly_Units"})
)
fig = px.line(
    seasonality, x="Month_Number", y="Average_Weekly_Units",
    markers=True,
    title="Average Weekly Sales by Month of Year",
    labels={"Month_Number": "Month number", "Average_Weekly_Units": "Average units"},
)
fig.write_html(FIGURES / "monthly_seasonality.html", include_plotlyjs="cdn")

# Save tables that can be checked or reused in the dashboard.
sku_summary.to_csv(ROOT / "reports" / "sku_sales_summary.csv", index=False)
category_summary.to_csv(ROOT / "reports" / "category_sales_summary.csv", index=False)

top_sku = sku_summary.loc[sku_summary["Total_Units"].idxmax()]
top_category = category_summary.iloc[0]

summary = f"""# Initial EDA findings

- The highest-selling SKU by units is {top_sku['SKU']} ({top_sku['Product_Name']}), with {int(top_sku['Total_Units']):,} units.
- The highest-revenue category is {top_category['Category']}, with revenue of {top_category['Total_Revenue']:,.2f}.
- {len(no_recent_sales)} SKUs had no recorded sales in the latest 13 weeks. Treat this as a low-demand review flag, not proof that the products are dead stock.

Charts are saved in `reports/figures/`. These are descriptive findings; they do not establish why sales changed.
"""
(ROOT / "reports" / "eda_findings.md").write_text(summary, encoding="utf-8")

print("EDA complete.")
print(f"Charts saved in: {FIGURES}")
print(f"Summary saved in: {ROOT / 'reports' / 'eda_findings.md'}")