"""R&D Portfolio Decision Intelligence | Strategic screening and resource feasibility.

All programs and values are synthetic. This app is not a valuation or optimization model.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="R&D Portfolio Explorer", page_icon="🧬", layout="wide")
ROOT = Path(__file__).resolve().parent

PROJECT_FIELDS = {
    "project_id", "therapeutic_area", "stage", "medical_need_score",
    "market_demand_score", "strategic_fit_score", "competitive_position_score",
    "next_stage_funding_usd_m", "illustrative_peak_sales_usd_m",
    "illustrative_probability_of_approval",
}


@st.cache_data
def load_projects():
    df = pd.read_csv(ROOT / "portfolio_projects.csv")
    missing = PROJECT_FIELDS.difference(df.columns)
    if missing:
        raise ValueError(f"portfolio_projects.csv missing columns: {', '.join(sorted(missing))}")
    if df.project_id.isna().any() or df.project_id.duplicated().any():
        raise ValueError("project_id must be unique and nonempty")
    for col in ["medical_need_score", "market_demand_score", "strategic_fit_score", "competitive_position_score"]:
        if not df[col].between(0, 100).all():
            raise ValueError(f"{col} must be between 0 and 100")
    if not df.illustrative_probability_of_approval.between(0, 1).all():
        raise ValueError("Approval probabilities must be between 0 and 1")
    if (df.next_stage_funding_usd_m < 0).any():
        raise ValueError("Funding amounts must be nonnegative")
    return df


@st.cache_data
def load_resources():
    capacity = pd.read_csv(ROOT / "resource_capacity.csv")
    requirements = pd.read_csv(ROOT / "project_resource_requirements.csv")
    capacity_cols = {"quarter", "resource_type", "capacity_unit", "available_capacity"}
    requirement_cols = {"project_id", "quarter", "resource_type", "capacity_unit", "required_capacity"}
    for filename, frame, expected in [
        ("resource_capacity.csv", capacity, capacity_cols),
        ("project_resource_requirements.csv", requirements, requirement_cols),
    ]:
        missing = expected.difference(frame.columns)
        if missing:
            raise ValueError(f"{filename} missing columns: {', '.join(sorted(missing))}")
        if frame[list(expected)].isna().any().any():
            raise ValueError(f"{filename} has missing values in required columns")
    capacity_key = ["quarter", "resource_type", "capacity_unit"]
    requirement_key = ["project_id", *capacity_key]
    if capacity.duplicated(capacity_key).any() or requirements.duplicated(requirement_key).any():
        raise ValueError("Duplicate quarter/resource/project combinations in resource data")
    if (capacity.available_capacity < 0).any() or (requirements.required_capacity < 0).any():
        raise ValueError("Resource capacity and requirements must be nonnegative")
    unknown_projects = set(requirements.project_id) - set(projects.project_id)
    if unknown_projects:
        raise ValueError(f"Unknown project IDs in requirements: {', '.join(sorted(unknown_projects))}")
    missing_capacity = requirements[requirement_key].merge(
        capacity[capacity_key], on=capacity_key, how="left", indicator=True
    )
    if (missing_capacity["_merge"] != "both").any():
        raise ValueError("Some project requirements have no matching resource capacity/unit")
    return capacity, requirements


try:
    projects = load_projects()
    capacity, requirements = load_resources()
except (OSError, ValueError, pd.errors.ParserError) as exc:
    st.error(f"Could not load portfolio data: {exc}")
    st.stop()

st.title("R&D Portfolio Decision Intelligence")
st.caption("Strategic screening + resource feasibility | Fictional biotech portfolio | All data synthetic")
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
    st.caption("Budget is an exploratory comparison only, not a project-selection constraint. "
               "Resource feasibility assumes programs have their planned funding.")

visible = projects[
    projects.therapeutic_area.isin(selected_areas) & projects.stage.isin(selected_stages)
].copy()
visible["screening_quadrant"] = visible.apply(
    lambda r: ("High" if r.medical_need_score >= need_cutoff else "Low")
    + " need / " + ("High" if r.market_demand_score >= demand_cutoff else "Low")
    + " demand", axis=1
)

requested = float(visible.next_stage_funding_usd_m.sum())
col1, col2, col3, col4 = st.columns(4)
col1.metric("Programs in view", len(visible))
col2.metric("Funding requests", f"${requested:,.0f}M")
col3.metric("Available budget", f"${budget:,.0f}M")
col4.metric("Funding gap / (surplus)", f"${requested - budget:+,.0f}M")
st.caption("Metrics reflect current filters. A positive gap means requests exceed the exploratory budget; "
           "no program selection is implied.")

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
    st.caption("Bubble size = next-stage funding request. Quadrants change with cutoffs, "
               "but do not determine invest / partner / stop actions.")

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

st.divider()
st.header("Resource Capacity & Manufacturing Feasibility")
st.caption("Capacity is compared with demand for the programs currently selected in the sidebar. "
           "Funding is assumed to be available; no projects are automatically removed.")
quarters = sorted(capacity.quarter.unique().tolist())
quarter = st.selectbox("Analysis quarter", quarters, index=0)
resource_types = sorted(capacity.resource_type.unique().tolist())
chosen_resources = st.multiselect("Resource categories", resource_types, default=resource_types)

selected_requirements = requirements[
    requirements.project_id.isin(visible.project_id)
    & requirements.quarter.eq(quarter)
    & requirements.resource_type.isin(chosen_resources)
].copy()
selected_capacity = capacity[
    capacity.quarter.eq(quarter) & capacity.resource_type.isin(chosen_resources)
].copy()

demand = selected_requirements.groupby(
    ["quarter", "resource_type", "capacity_unit"], as_index=False
).required_capacity.sum()
comparison = selected_capacity.merge(
    demand, on=["quarter", "resource_type", "capacity_unit"], how="left"
)
comparison["required_capacity"] = comparison["required_capacity"].fillna(0)
comparison["shortfall"] = (comparison.required_capacity - comparison.available_capacity).clip(lower=0)
comparison["utilization_pct"] = comparison.apply(
    lambda r: 100 * r.required_capacity / r.available_capacity
    if r.available_capacity > 0 else (0.0 if r.required_capacity == 0 else float("inf")),
    axis=1,
)
comparison["status"] = comparison.apply(
    lambda r: "Capacity gap" if r.shortfall > 0 else "Within capacity", axis=1
)

if not chosen_resources:
    st.warning("Select at least one resource category.")
else:
    gaps = comparison[comparison.shortfall > 0]
    c1, c2 = st.columns(2)
    c1.metric("Resource categories with gaps", f"{len(gaps)} / {len(comparison)}")
    c2.metric("Programs included", len(visible))
    if gaps.empty:
        st.success("No capacity gaps for the selected programs, quarter, and resource categories.")
    else:
        st.warning("At least one resource category exceeds available capacity. "
                   "This is a scheduling / feasibility flag, not a recommendation to stop programs.")

    if not comparison.empty:
        chart_data = comparison.melt(
            id_vars=["resource_type", "capacity_unit"],
            value_vars=["available_capacity", "required_capacity"],
            var_name="measure", value_name="capacity",
        )
        chart_data["resource_label"] = chart_data.resource_type + " (" + chart_data.capacity_unit + ")"
        chart = px.bar(
            chart_data, x="resource_label", y="capacity", color="measure", barmode="group",
            labels={"resource_label": "Resource", "capacity": "Capacity / demand",
                    "measure": "Series"},
            title=f"Available capacity vs. project demand — {quarter}",
        )
        chart.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(chart, use_container_width=True)
        st.dataframe(
            comparison[["resource_type", "capacity_unit", "available_capacity",
                        "required_capacity", "shortfall", "utilization_pct", "status"]].round(1),
            hide_index=True, use_container_width=True,
        )

        st.subheader("Project-level demand")
        project_view = selected_requirements.merge(
            visible[["project_id", "therapeutic_area", "stage"]], on="project_id", how="left"
        )
        st.dataframe(
            project_view[["project_id", "therapeutic_area", "stage", "resource_type",
                          "capacity_unit", "required_capacity"]].sort_values(
                ["resource_type", "required_capacity"], ascending=[True, False]
            ),
            hide_index=True, use_container_width=True,
        )
        st.download_button(
            "Download capacity comparison (CSV)",
            comparison.to_csv(index=False).encode("utf-8"),
            file_name=f"capacity_comparison_{quarter}.csv", mime="text/csv",
        )

with st.expander("Assumptions and limitations"):
    st.markdown("""
- **All data are synthetic** and represent an educational case study, not an actual company.
- Screening scores are illustrative, not validated clinical or commercial assessments.
- Funding requests cover the next development stage; peak sales and approval probability are not rNPV.
- Resource analysis compares **quarterly aggregate demand** with **quarterly available capacity**.
- FTE and manufacturing batch slots are **different units** and are never summed together.
- Manufacturing batch slots are a simplified proxy: no plant-specific equipment, product compatibility,
  batch duration, yields, CDMO commitments, or detailed production scheduling is modeled.
- No project dependencies, skill-level allocation, project prioritization, automatic scheduling,
  portfolio optimization, or AI agent is implemented yet.
- A capacity gap is not a recommendation to stop a program; management can explore staffing,
  outsourcing, manufacturing partnerships, and schedule changes.
""")
