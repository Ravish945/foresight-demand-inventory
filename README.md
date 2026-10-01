# FORESIGHT — Demand & Inventory Intelligence

FORESIGHT is a retail planning prototype that brings weekly SKU demand forecasts and inventory risk recommendations into one Streamlit dashboard.

## What it does

- Cleans and joins daily sales, SKU, calendar, and inventory data.
- Summarises sales by product and category.
- Forecasts demand for six weeks using a 52-week seasonal-naive baseline.
- Compares the baseline with a Random Forest using rolling-origin backtesting.
- Flags inventory for reorder or overstock review.
- Provides filters, charts, an action queue, and CSV downloads in the dashboard.

## Project structure

- `data/raw/` — original input CSV files
- `data/processed/` — cleaned sales data and forecasts
- `src/` — data pipeline, analysis, forecasting, and risk scripts
- `app/dashboard.py` — Streamlit dashboard
- `reports/` — findings, model metrics, and inventory risk outputs

## Run locally

From the project folder, activate the virtual environment and run:

```bash
source .venv/bin/activate
python src/pipeline.py
python src/eda.py
python src/model_comparison.py
python src/risk.py
python -m streamlit run app/dashboard.py