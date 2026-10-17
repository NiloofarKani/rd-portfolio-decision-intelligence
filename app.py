"""R&D Portfolio Decision Intelligence | Phase 1: strategic screening.

All programs and values are synthetic. This app is not a valuation model.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="R&D Portfolio Explorer", page_icon="🧬", layout="wide")

DATA_FILE = Path(__file__).resolve().parent / "portfolio_projects.csv"
REQUIRED = {
    "project_id", "therapeutic_area", "stage", "medical_need_score",
    "market_demand_score", "strategic_fit_score", "competitive_position_score",
    "next_stage_funding_usd_m", "illustrative_peak_sales_usd_m",
    "illustrative_probability_of_approval",
}


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)
    missing = REQUIRED.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    if df.project_id.duplicated().any():
        raise ValueError("project_id must be unique")
    score_cols = ["medical_need_score", "market_demand_score", "strategic_fit_score", "competitive_position_score"]
    for col in score_cols:
        if not df[col].between(0, 100).all():
            raise ValueError(f"{col} must be between 0 and 100")
    if not df.illustrative_probability_of_approval.between(0, 1).all():
        raise ValueError("Approval probabilities must be between 0 and 1")
    if (df.next_stage_funding_usd_m < 0).any():
        raise ValueError("Funding amounts must be nonnegative")
    return df


try:
    projects = load_data()
except (OSError, ValueError, pd.errors.ParserError) as exc:
    st.error(f"Could not load portfolio_projects.csv: {exc}")
    st.stop()

st.title("R&D Portfolio Decision Intelligence")
st.caption("Phase 1 · Strategic screening | Fictional mid-sized biotech portfolio · All data synthetic")
st.info("Screening is **not** a funding recommendation, financial valuation, or optimized portfolio. "
        "Medical need and market demand are illustrative scores; peak sales are not rNPV.")

with st.sidebar:
    st.header("Scenario controls")
    budget = st.slider("Available next-stage budget ($M)", 0, 650, 300, 10)
    need_cutoff = st.slider("High medical need cutoff", 0, 100, 70, 5)
    demand_cutoff = st.slider("High market demand cutoff", 0, 100, 70, 5)
    areas = sorted(projects.therapeutic_area.unique().tolist())
    selected_areas = st.multiselect("Therapeutic areas", areas, default=areas)
    stages = sorted(projects.stage.unique().tolist())
    selected_stages = st.multiselect("Development stages", stages, default=stages)
    st.caption("Budget is compared with funding requests only. It does not automatically select programs.")

visible = projects[
    projects.therapeutic_area.isin(selected_areas) & projects.stage.isin(selected_stages)
].copy()
visible["screening_quadrant"] = visible.apply(
    lambda r: ("High" if r.medical_need_score >= need_cutoff else "Low")
    + " need / "
    + ("High" if r.market_demand_score >= demand_cutoff else "Low")
    + " demand", axis=1
)

requested = float(visible.next_stage_funding_usd_m.sum())
col1, col2, col3, col4 = st.columns(4)
col1.metric("Programs in view", len(visible))
col2.metric("Funding requests", f"${requested:,.0f}M")
col3.metric("Available budget", f"${budget:,.0f}M")
col4.metric("Funding gap / (surplus)", f"${requested - budget:+,.0f}M")
st.caption("Metrics reflect the current filters. A positive gap means requests exceed available budget; "
           "a negative gap means a surplus. No program selection is implied.")

st.subheader("Medical need × market demand")
if visible.empty:
    st.warning("No programs match these filters. Choose at least one area and stage.")
else:
    fig = px.scatter(
        visible,
        x="market_demand_score", y="medical_need_score",
        color="screening_quadrant", size="next_stage_funding_usd_m",
        text="project_id", hover_name="project_id",
        hover_data={
            "therapeutic_area": True, "stage": True,
            "strategic_fit_score": True, "competitive_position_score": True,
            "next_stage_funding_usd_m": ":.0f", "screening_quadrant": False,
        },
        category_orders={"screening_quadrant": [
            "High need / High demand", "High need / Low demand",
            "Low need / High demand", "Low need / Low demand"]},
        labels={"market_demand_score": "Market demand (illustrative score)",
                "medical_need_score": "Medical need (illustrative score)",
                "screening_quadrant": "Screening quadrant",
                "next_stage_funding_usd_m": "Next-stage funding ($M)"},
    )
    fig.add_vline(x=demand_cutoff, line_dash="dash", line_color="gray")
    fig.add_hline(y=need_cutoff, line_dash="dash", line_color="gray")
    fig.update_traces(textposition="top center")
    fig.update_xaxes(range=[-5, 105])
    fig.update_yaxes(range=[-5, 110])
    fig.update_layout(height=570, legend_title_text="Screening quadrant")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Bubble size = next-stage funding request. Quadrants change when you adjust the cutoffs. "
               "They do not determine whether to invest, partner, or stop.")

    st.subheader("Quadrant summary")
    summary = visible.groupby("screening_quadrant", as_index=False).agg(
        programs=("project_id", "count"),
        funding_request_usd_m=("next_stage_funding_usd_m", "sum"),
    )
    st.dataframe(summary, hide_index=True, use_container_width=True)

st.subheader("Explore the underlying programs")
st.dataframe(visible, hide_index=True, use_container_width=True)
st.download_button("Download filtered dataset (CSV)",
                   data=visible.to_csv(index=False).encode("utf-8"),
                   file_name="filtered_portfolio.csv", mime="text/csv")

with st.expander("Assumptions and limitations"):
    st.markdown("""
- **All data are fictional**, for an educational portfolio case study.
- Scores are subjective illustrations on a 0–100 scale, not validated clinical or commercial assessments.
- Cutoffs are exploratory and have no clinical or investment significance.
- Funding requests cover only the **next development stage**, not full lifecycle costs.
- Peak sales and probability of approval are shown as context, not used to calculate rNPV.
- No portfolio optimization, cash-flow discounting, project dependencies, or resource constraints are modeled yet.
- Strategic action recommendations (invest / monitor / partner / stop) require additional evidence and explicit decision rules.
""")
