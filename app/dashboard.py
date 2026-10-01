from pathlib import Path
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

st.set_page_config(
    page_title="FORESIGHT | Demand & Inventory Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink:#172033; --muted:#69758a; --line:#e6eaf1; --brand:#6257e8; --mint:#18a77a; }
.stApp { background:linear-gradient(180deg,#f6f8fc 0%,#f8f9fc 55%,#f5f7fb 100%); color:var(--ink); font-family:'DM Sans',sans-serif; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebar"] { background:#111a2d; border-right:1px solid #263149; }
[data-testid="stSidebar"] * { color:#e8edf7; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#aeb9ce; }
[data-testid="stSidebar"] [data-baseweb="select"] > div { background:#1d2940; border-color:#33415c; }
.block-container { padding-top:2.1rem; padding-bottom:3rem; max-width:1500px; }
h1,h2,h3 { font-family:'Manrope','DM Sans',sans-serif; letter-spacing:-.035em; color:var(--ink); }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color:#fff; }
.brandline { display:flex; align-items:center; gap:12px; margin:0 0 18px; }
.brandmark { width:42px;height:42px;border-radius:14px;background:linear-gradient(135deg,#8278ff,#5548dc);display:grid;place-items:center;color:white;font-size:21px;box-shadow:0 8px 22px #5348d844; }
.brandname { font:800 20px Manrope,sans-serif;letter-spacing:.09em;color:#fff; }
.brandmeta { color:#aab5ca;font-size:11px;letter-spacing:.12em;text-transform:uppercase;margin-top:1px; }
.sidebar-foot { border-top:1px solid #2b3650; padding-top:14px; margin-top:22px; font-size:12px; color:#aeb9ce; line-height:1.7; }
.hero { border-radius:24px; padding:30px 34px; background:radial-gradient(circle at 88% 15%,#8276ff66,transparent 30%),linear-gradient(120deg,#161e35,#26395a 70%,#344971); color:white; box-shadow:0 16px 40px #1a27401c; margin:2px 0 22px; }
.hero-kicker { color:#bdc5ff; font-size:11px; font-weight:700; letter-spacing:.17em; text-transform:uppercase; }
.hero h1 { color:#fff; font-size:34px; margin:8px 0 7px; }
.hero p { color:#d4dced; font-size:14px; margin:0; max-width:780px; line-height:1.6; }
.hero-chip { display:inline-block; margin-top:17px; border:1px solid #ffffff33; background:#ffffff12; border-radius:999px; padding:7px 12px; font-size:12px; color:#e8edff; }
[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:18px; padding:17px 19px; box-shadow:0 5px 18px #192b4608; min-height:116px; }
[data-testid="stMetricLabel"] { color:var(--muted); font-size:12px; font-weight:600; }
[data-testid="stMetricValue"] { color:var(--ink); font:750 27px Manrope,sans-serif; }
[data-testid="stMetricDelta"] { font-size:11px; }
[data-testid="stTabs"] [role="tablist"] { gap:8px; border-bottom:1px solid var(--line); }
[data-testid="stTabs"] button[role="tab"] { background:transparent; border-radius:11px 11px 0 0; padding:12px 17px; font-weight:650; color:#78849a; }
[data-testid="stTabs"] button[aria-selected="true"] { color:var(--brand); border-bottom:3px solid var(--brand); }
[data-testid="stVerticalBlock"] > div:has(> [data-testid="stPlotlyChart"]) { background:#fff; border:1px solid var(--line); border-radius:18px; padding:12px 12px 2px; }
[data-testid="stDataFrame"] { background:white; border:1px solid var(--line); border-radius:14px; overflow:hidden; }
.section-title { font:750 19px Manrope,sans-serif; color:var(--ink); margin:13px 0 4px; }
.section-sub { color:var(--muted); font-size:12px; margin:0 0 13px; }
.notice { border-radius:14px; padding:13px 16px; background:#fff8e8; border:1px solid #f5dfaa; color:#775814; font-size:13px; line-height:1.55; }
.small-note { color:#8993a5; font-size:11px; line-height:1.5; }
div[data-testid="stDownloadButton"] button { border-radius:10px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    weekly = pd.read_csv(ROOT / "data" / "processed" / "weekly_sales.csv", parse_dates=["Week_Start"])
    forecast = pd.read_csv(ROOT / "data" / "processed" / "selected_forecast.csv", parse_dates=["Week_Start"])
    risk = pd.read_csv(ROOT / "reports" / "inventory_risk_scores.csv", parse_dates=["Snapshot_Date"])
    comparison = json.loads((ROOT / "reports" / "model_comparison.json").read_text(encoding="utf-8"))
    return weekly, forecast, risk, comparison


weekly, forecast, risk, comparison = load_data()


def rupees_lakh(value):
    return f"₹{value / 100000:,.1f} L"


def chart_layout(fig, height=350):
    fig.update_layout(
        height=height, margin=dict(l=12, r=12, t=44, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#536078", size=11),
        title=dict(font=dict(family="Manrope, sans-serif", size=15, color="#172033")),
        xaxis=dict(showgrid=False, linecolor="#e8ecf2", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#edf0f5", zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
    )
    return fig


snapshot_date = risk["Snapshot_Date"].max()
forecast_start = forecast["Week_Start"].min()
forecast_end = forecast["Week_Start"].max()

st.sidebar.markdown("""
<div class="brandline"><div class="brandmark">✦</div><div><div class="brandname">FORESIGHT</div><div class="brandmeta">Planning intelligence</div></div></div>
""", unsafe_allow_html=True)
st.sidebar.markdown("### Workspace")
categories = ["All categories"] + sorted(risk["Category"].dropna().unique())
selected_category = st.sidebar.selectbox("Product category", categories)
if selected_category == "All categories":
    sku_choices = sorted(risk["SKU"].unique())
else:
    sku_choices = sorted(risk.loc[risk["Category"] == selected_category, "SKU"].unique())
selected_sku = st.sidebar.selectbox("Product", ["All products"] + sku_choices)
st.sidebar.markdown("---")
st.sidebar.markdown("**Forecast quality**")
st.sidebar.metric("Selected model WAPE", f"{comparison['seasonal_naive_WAPE']:.1%}", help="Weighted Absolute Percentage Error from four rolling-origin backtests. Lower is better.")
st.sidebar.caption(f"Chosen model · {comparison['selected_model']}")
st.sidebar.markdown(f"""
<div class="sidebar-foot"><b>Data refresh</b><br>Sales through 31 Dec 2025<br>Inventory snapshot · {snapshot_date:%d %b %Y}<br><br>Internal planning prototype<br>FORESIGHT · v1.0</div>
""", unsafe_allow_html=True)

risk_view, forecast_view, history_view = risk.copy(), forecast.copy(), weekly.copy()
if selected_category != "All categories":
    risk_view = risk_view[risk_view["Category"] == selected_category]
    category_skus = set(risk_view["SKU"])
    forecast_view = forecast_view[forecast_view["SKU"].isin(category_skus)]
    history_view = history_view[history_view["SKU"].isin(category_skus)]
if selected_sku != "All products":
    risk_view = risk_view[risk_view["SKU"] == selected_sku]
    forecast_view = forecast_view[forecast_view["SKU"] == selected_sku]
    history_view = history_view[history_view["SKU"] == selected_sku]

st.markdown(f"""
<div class="hero"><div class="hero-kicker">Demand · Stock · Decisions</div>
<h1>Plan ahead with confidence.</h1>
<p>One view of weekly demand, forecast performance, and inventory actions across your matched product range. Use the filters to focus on a category or SKU.</p>
<span class="hero-chip">Forecast window · {forecast_start:%d %b} — {forecast_end:%d %b %Y}</span>
<span class="hero-chip">{len(risk_view)} matched SKUs in view</span></div>
""", unsafe_allow_html=True)

st.markdown(f'<div class="notice"><b>Inventory data is historical:</b> stock is as of {snapshot_date:%d %B %Y}, about {int(risk["Snapshot_Age_Days_At_Forecast_Start"].max())} days before the forecast window. Treat actions as planning estimates and confirm live stock before ordering.</div>', unsafe_allow_html=True)
st.write("")

overview_tab, demand_tab, inventory_tab, methodology_tab = st.tabs(["◈  Executive overview", "⌁  Demand forecast", "▦  Inventory actions", "ⓘ  Method & data"])

with overview_tab:
    forecast_units = forecast_view["Forecast_Units"].sum()
    reorder_count = int((risk_view["Recommended_Action"] == "Reorder now").sum())
    clear_count = int((risk_view["Recommended_Action"] == "Markdown / clear").sum())
    sales_at_risk = risk_view["Estimated_Sales_At_Risk"].sum()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("6-week demand outlook", f"{forecast_units:,.0f} units", help="Sum of selected-model weekly predictions in current filter.")
    c2.metric("Reorder priority", f"{reorder_count} SKUs", help="SKUs flagged for reorder by the documented lead-time rule.")
    c3.metric("Overstock reviews", f"{clear_count} SKUs", help="Possible excess stock to review, not automatic markdown decisions.")
    c4.metric("Estimated sales at risk", rupees_lakh(sales_at_risk), help="Modelled exposure during supplier lead time using historical stock; not realised lost sales.")

    left, right = st.columns([1.65, 1])
    with left:
        actual = history_view.groupby("Week_Start", as_index=False)["Units_Sold"].sum()
        predicted = forecast_view.groupby("Week_Start", as_index=False)["Forecast_Units"].sum()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=actual["Week_Start"], y=actual["Units_Sold"], name="Observed sales", mode="lines", line=dict(color="#6257e8", width=2.5), fill="tozeroy", fillcolor="rgba(98,87,232,.08)"))
        fig.add_trace(go.Scatter(x=predicted["Week_Start"], y=predicted["Forecast_Units"], name="Forecast", mode="lines+markers", line=dict(color="#15a77b", width=2.5, dash="dash"), marker=dict(size=7)))
        fig.add_vline(x=forecast_start, line_dash="dot", line_color="#a7afbf", annotation_text="Forecast starts", annotation_position="top")
        fig.update_layout(title="Weekly demand · actuals and outlook", hovermode="x unified", yaxis_title="Units", xaxis_title="")
        st.plotly_chart(chart_layout(fig, 365), use_container_width=True)
    with right:
        action_counts = risk_view["Recommended_Action"].value_counts().rename_axis("Action").reset_index(name="SKUs")
        colors = {"Healthy":"#18a77a", "Reorder now":"#f0a52b", "Markdown / clear":"#ed6a71"}
        fig = px.pie(action_counts, names="Action", values="SKUs", hole=.70, color="Action", color_discrete_map=colors)
        fig.update_traces(textposition="outside", textinfo="label+value", marker=dict(line=dict(color="white", width=3)))
        fig.add_annotation(text=f"{len(risk_view)}<br><span style='font-size:11px'>SKUs</span>", x=.5, y=.5, showarrow=False, font=dict(size=23, color="#172033", family="Manrope"))
        fig.update_layout(title="Inventory action mix", showlegend=False)
        st.plotly_chart(chart_layout(fig, 365), use_container_width=True)
    st.markdown('<div class="section-title">What needs attention</div><div class="section-sub">Highest priority products by modelled stockout risk and sales exposure.</div>', unsafe_allow_html=True)
    priority = risk_view[risk_view["Recommended_Action"] != "Healthy"].sort_values(["Stockout_Risk", "Estimated_Sales_At_Risk"], ascending=False).head(6)
    if priority.empty:
        st.success("No non-healthy actions in this filter. Keep reviewing as fresh inventory arrives.")
    else:
        st.dataframe(priority[["SKU", "Product_Name", "Category", "Risk_Level", "Recommended_Action", "Recommended_Order_Units", "Estimated_Sales_At_Risk"]], hide_index=True, use_container_width=True, column_config={"Estimated_Sales_At_Risk":st.column_config.NumberColumn("Sales exposure (₹)",format="₹%,.0f"),"Recommended_Order_Units":st.column_config.NumberColumn("Suggested order (units)",format="%,.0f")})

with demand_tab:
    st.markdown('<div class="section-title">Demand forecast</div><div class="section-sub">A transparent seasonal-naive benchmark: each forecast week uses the corresponding week from the prior year.</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.metric("Forecast span", f"{len(forecast_view['Week_Start'].unique())} weeks")
    a.metric("First forecast week", f"{forecast_start:%d %b %Y}")
    b.metric("Seasonal-naive WAPE", f"{comparison['seasonal_naive_WAPE']:.1%}")
    b.metric("Seasonal-naive bias", f"{comparison['seasonal_naive_bias']:+.1%}")
    c.metric("Random Forest WAPE", f"{comparison['random_forest_WAPE']:.1%}")
    c.metric("Backtest origins", str(comparison["backtest_origins"]))
    by_week = forecast_view.groupby("Week_Start", as_index=False)["Forecast_Units"].sum()
    fig = px.area(by_week, x="Week_Start", y="Forecast_Units", markers=True, labels={"Week_Start":"Forecast week","Forecast_Units":"Predicted units"}, title="Six-week demand outlook")
    fig.update_traces(line_color="#6257e8", fillcolor="rgba(98,87,232,.15)", marker_color="#6257e8")
    st.plotly_chart(chart_layout(fig, 380), use_container_width=True)
    st.dataframe(by_week.rename(columns={"Week_Start":"Forecast week","Forecast_Units":"Predicted units"}), hide_index=True, use_container_width=True, column_config={"Forecast week":st.column_config.DateColumn(format="DD MMM YYYY"),"Predicted units":st.column_config.NumberColumn(format="%,.1f")})
    st.download_button("Download filtered forecast", forecast_view.to_csv(index=False), file_name="foresight_filtered_forecast.csv", mime="text/csv")
    st.caption("Backtest uses four rolling time origins. Random Forest scored worse than the simpler baseline (12.0% vs 11.5% WAPE), so the baseline is retained. Results are retrospective and do not guarantee future accuracy.")

with inventory_tab:
    st.markdown('<div class="section-title">Inventory action queue</div><div class="section-sub">Prioritise the exception list. Review supplier lead time and stock date before taking action.</div>', unsafe_allow_html=True)
    action_filter = st.multiselect("Show actions", options=["Reorder now", "Markdown / clear", "Healthy"], default=["Reorder now", "Markdown / clear"])
    actions = risk_view[risk_view["Recommended_Action"].isin(action_filter)].copy()
    actions = actions.sort_values(["Stockout_Risk", "Estimated_Sales_At_Risk"], ascending=False)
    if actions.empty:
        st.info("No products match the selected action filters.")
    else:
        st.dataframe(actions[["SKU", "Product_Name", "Category", "Snapshot_Date", "Current_Stock", "On_Order", "Lead_Time_Days", "Lead_Time_Demand", "Risk_Level", "Recommended_Action", "Recommended_Order_Units", "Estimated_Sales_At_Risk", "Estimated_Capital_Locked"]], hide_index=True, use_container_width=True, column_config={"Snapshot_Date":st.column_config.DateColumn("Stock as of",format="DD MMM YYYY"),"Estimated_Sales_At_Risk":st.column_config.NumberColumn("Sales exposure (₹)",format="₹%,.0f"),"Estimated_Capital_Locked":st.column_config.NumberColumn("Potential excess capital (₹)",format="₹%,.0f"),"Current_Stock":st.column_config.NumberColumn("On hand",format="%,.0f"),"On_Order":st.column_config.NumberColumn("On order",format="%,.0f"),"Lead_Time_Demand":st.column_config.NumberColumn("Lead-time demand",format="%,.0f"),"Recommended_Order_Units":st.column_config.NumberColumn("Suggested order",format="%,.0f")})
        st.download_button("Export action queue (CSV)", actions.to_csv(index=False), file_name="foresight_inventory_actions.csv", mime="text/csv")
    category = risk_view.groupby("Category", as_index=False).agg(SKUs=("SKU","count"), Sales_Exposure=("Estimated_Sales_At_Risk","sum"), Excess_Capital=("Estimated_Capital_Locked","sum"))
    bar = px.bar(category.sort_values("Sales_Exposure",ascending=True), x="Sales_Exposure", y="Category", orientation="h", title="Estimated sales exposure by category", labels={"Sales_Exposure":"Estimated exposure (₹)","Category":""}, color_discrete_sequence=["#6257e8"])
    st.plotly_chart(chart_layout(bar, 320), use_container_width=True)
    st.caption("Risk rules compare available stock with forecast demand over supplier lead time plus safety stock. Overstock review uses the documented threshold of on-hand stock above twice the six-week forecast.")

with methodology_tab:
    st.markdown('<div class="section-title">How to read these numbers</div><div class="section-sub">Definitions and known data boundaries—so decisions stay grounded in what the files actually support.</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Forecast evaluation")
        st.write(f"The selected **{comparison['selected_model']}** achieved **{comparison['seasonal_naive_WAPE']:.1%} WAPE** and **{comparison['seasonal_naive_bias']:+.1%} bias** across {comparison['backtest_origins']} rolling-origin backtests. Random Forest scored **{comparison['random_forest_WAPE']:.1%} WAPE** and was not selected.")
        st.markdown("#### Inventory risk rules")
        st.write("Stockout risk compares available units with forecast demand across supplier lead time and safety stock. Suggested order units are planning estimates for review, not purchase orders.")
        st.write("Estimated sales exposure is modelled revenue that could be affected during lead time; it is not measured lost revenue.")
    with col_b:
        st.markdown("#### Data coverage")
        st.write("Sales and product files contain 50 SKUs; inventory contains 200. Only 50 inventory SKUs match sales and product records. The other 150 are excluded from joined risk recommendations.")
        st.write(f"The latest stock snapshot is **{snapshot_date:%d %B %Y}**. Sales data runs through **31 December 2025**; inventory is therefore historical relative to the forecast.")
        st.write("Some holiday and promotion-event calendar labels are blank. They are treated as ‘not recorded’, not as proof no event occurred.")
    st.info("Refresh the inventory snapshots before using this prototype for operational ordering. This dashboard is a decision-support demonstration, not an inventory execution system.")
