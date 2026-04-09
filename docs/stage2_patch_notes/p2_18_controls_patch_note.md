# P2.18 Stage 0 → Stage 2 rerun with size proxy and quarterly controls

This step addresses the second major limitation from the earlier preliminary Stage 2 rerun.

## What changed

The earlier patch used a constant size proxy, so the nominal Stage 2 size control was not economically meaningful.
This rerun replaces that with two additions:

1. A market-based size proxy from the price file:
   - `prccd` → `logP`

2. Quarterly fundamentals merged from `Financial Ratios_Ticker.csv` using the most recent available `public_date` at or before each firm-day:
   - `bm`
   - `debt_assets`
   - `curr_ratio`
   - `roa`

The controls enter the regression as:

- standardized numeric controls:
  - `bm_z`
  - `debt_assets_z`
  - `curr_ratio_z`
  - `roa_z`

- missingness flags:
  - `bm_missing`
  - `debt_assets_missing`
  - `curr_ratio_missing`
  - `roa_missing`

## Important limitation that remains

This still does **not** create a true market-cap control, because the current price file does not contain a shares-outstanding field and the ratios file does not expose a directly usable market-cap level.

So the second limitation is only partially solved:

- solved: the regression no longer uses a constant size proxy
- not fully solved: the size term is still a price-based proxy rather than `log(market_cap)`

## Practical implication

This rerun is better than the earlier constant-size version for a preliminary specification test, but it should still be described as a control-enhanced prototype rather than a final production Stage 2 result.

## Files produced

- `stage2_mechanism_outputs_v4_controls/`
- `p2_18_stage0_stage2_results_with_policy_daily_and_controls.csv`
- `p2_18_stage2_control_coverage_summary.csv`
- `p2_18_stage0_stage2_comparison_policy_daily_vs_controls.csv`
- `stage2_mechanism_specific_twfe_panel_patch_v4_controls.py`
