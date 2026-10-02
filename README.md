# FORESIGHT — Demand & Inventory Intelligence

<p align="center"><strong>A retail planning dashboard for weekly demand forecasts and inventory review.</strong></p>

<p align="center">
<a href="https://foresight-demand-inventory-gdzbkvidhzl37dztbrtd7s.streamlit.app/"><img src="https://img.shields.io/badge/OPEN-LIVE_DASHBOARD-6257E8?style=for-the-badge&logo=streamlit&logoColor=white" alt="Open live dashboard"></a>
<img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13">
<img src="https://img.shields.io/badge/Selected_WAPE-11.5%25-168C70?style=for-the-badge" alt="Selected model WAPE 11.5 percent">
<img src="https://img.shields.io/badge/Inventory_match-50_SKUs-E2A53A?style=for-the-badge" alt="50 matched SKUs">
</p>

FORESIGHT brings weekly sales forecasts and inventory review signals into one Streamlit app. I built it as an end-to-end retail planning project: clean the source files, check the data, compare two forecasting approaches, score inventory risk, then make the results easy to explore.

> **Project report:** [Read the 10-page report (PDF)](reports/FORESIGHT_Project_Report.pdf) · [Download the editable Word version](reports/FORESIGHT_Project_Report.docx)

## At a glance

| | Result |
|---|---|
| Forecast horizon | Six weeks, 5 January–9 February 2026 |
| Selected approach | 52-week seasonal-naive forecast |
| Backtest | 4 rolling forecast origins |
| Seasonal-naive WAPE | 11.47% (shown as 11.5% in the dashboard) |
| Random Forest WAPE | 12.00% |
| Selected forecast total | 29,571 units across 50 matched SKUs |
| Inventory review | 7 reorder · 2 overstock · 41 healthy |

The seasonal-naive model had lower WAPE and lower bias than the Random Forest in the available backtest, so it is the selected model in this version. The backtest is a comparison on historical periods; it does not guarantee future accuracy.

## What you can explore

- **Executive overview** — demand outlook, model quality, inventory flags, and estimated exposure.
- **Demand forecast** — six weekly periods with category and product filters.
- **Inventory actions** — a review queue with reorder and overstock signals.
- **Method and data** — model comparison, metric definitions, and data coverage notes.
- **Downloads** — filtered forecast and inventory tables as CSV files.

## How it is put together

The data/raw/ folder holds the input CSVs. The scripts in src/ clean and analyse those inputs, write prepared outputs to data/processed/ and reports/, and the Streamlit dashboard in app/dashboard.py reads those outputs. Keeping those steps separate makes the results easier to reproduce and inspect.

| Stage | Script | Output |
|---|---|---|
| Prepare | src/pipeline.py | Clean tables and data-quality report |
| Explore | src/eda.py | Summary tables, charts, and findings |
| Forecast | src/forecast.py | Seasonal-naive and Random Forest forecasts |
| Compare | src/model_comparison.py | Rolling backtest and selected forecast |
| Review stock | src/risk.py | SKU risk scores and action summary |
| Present | app/dashboard.py | Interactive Streamlit dashboard |

## Data coverage and assumptions

The source files contain 36,550 daily sales rows, 50 products, 731 calendar dates, and 4,800 inventory snapshot rows for 200 SKUs. Sales data runs through 31 December 2025. The latest inventory snapshot is dated 1 December 2025.

Only 50 inventory SKUs match the sales and product records; the remaining 150 are listed in the unmatched-SKU report and are not included in inventory risk results. The stock snapshot is historical, so the action labels are planning estimates. Refresh stock and confirm lead times and safety-stock settings before using a recommendation operationally. Blank holiday or promotion fields mean the event was not recorded; they do not prove that no event happened.

## Run it locally

Use Python 3.13 and run these commands from the repository folder:

    python3.13 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    python src/pipeline.py
    python src/eda.py
    python src/model_comparison.py
    python src/risk.py
    python -m streamlit run app/dashboard.py

Streamlit prints a local URL (usually http://localhost:8501). Open it in your browser to use the dashboard.

## Repository map

    app/                  Streamlit dashboard
    data/raw/             Source CSV files
    data/processed/       Cleaned tables and forecast outputs
    reports/              Metrics, findings, charts, and project report
    src/                  Data preparation, EDA, forecasting, and risk scripts
    README.md             Project overview and setup guide
    requirements.txt      Python dependencies

## Project files

- [10-page project report (PDF)](reports/FORESIGHT_Project_Report.pdf)
- [Editable project report (Word)](reports/FORESIGHT_Project_Report.docx)
- [Data quality notes](reports/data_quality_notes.md)
- [Exploratory findings](reports/eda_findings.md)
- [Model comparison](reports/model_comparison.json)
- [Inventory risk summary](reports/inventory_risk_summary.json)

## Built with

Python · pandas · NumPy · scikit-learn · Streamlit · Plotly

---

**Ravish Patel** · [Source code](https://github.com/Ravish945/foresight-demand-inventory) · [Live dashboard](https://foresight-demand-inventory-gdzbkvidhzl37dztbrtd7s.streamlit.app/)
