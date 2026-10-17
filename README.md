# R&D Portfolio Decision Intelligence

A **synthetic**, educational case study for strategic screening and portfolio decision support in a hypothetical mid-sized biotech company.

## Phase 1: strategic screening

`portfolio_projects.csv` contains 10 fictional programs. `screening_matrix.csv` maps programs to a two-axis **Medical Need × Market Demand** matrix, using a provisional 70/100 cutoff on each axis. Scores are illustrative judgments, **not validated measurements**. Run `python build_project.py` to regenerate both CSV files.

This is **not a project ranking**, rNPV calculation, or funding recommendation. Medical need, demand, peak sales and commercial value are distinct concepts. The probability-of-approval and peak-sales inputs are illustrative and must not be multiplied together and presented as rNPV.

## Next development stages

1. Define transparent, evidence-based score rubrics and test sensitivity to cutoffs.
2. Add stage-specific costs, timelines, launch probabilities, operating margins, exclusivity and discounted cash flows to estimate rNPV.
3. Model constrained portfolio optimization and portfolio-level risks, avoiding double counting of probability and strategic benefits.
4. Generate candidate actions: invest/accelerate, maintain/monitor, partner/license, stop/divest. Require explicit decision rules and human review.
5. Add an interactive scenario dashboard, assumptions documentation, and reproducible tests.

**Data:** Entirely fictional; not sourced from or representative of any employer or real asset.
