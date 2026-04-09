# P2.19 hybrid-controls strengthening pass

This step strengthens the second limitation in the Stage 0 → Stage 2 pipeline.

## What changed

The control layer now uses a hybrid design:

- `logP` as a broad-coverage price-level size proxy
- `vol60` as a 60-day rolling volatility control
- `mom20` as a 20-day lagged momentum control
- `bm`, `debt_assets`, `curr_ratio`, `roa` from the ratios file
- date-by-industry median imputation for the fundamentals
- explicit missing flags for the imputed accounting controls

## Why this is stronger

The model no longer depends on sparse fundamentals alone.
The market-based controls are available for almost the whole panel, so the regression stays estimable while still keeping the fundamentals in the specification.

## What this does not solve

This is still not a full market-cap architecture.
`logP` is economically better than `constant_1`, but it is not the same thing as `log(market_cap)`.

So this pass should be read as a stronger prototype, not a final production specification.

## Empirical takeaway from this pass

Compared with the earlier control-enhanced pass, the hybrid-controls rerun is more conservative.

- IRA baseline stays negative and significant.
- The IRA mechanism split weakens under the stronger control stack.
- LCFS remains weak.
- RFS2 keeps a positive subsidy tendency, but does not cross conventional significance in this pass.

## Files produced

- `stage2_mechanism_specific_twfe_panel_patch_v5_hybrid_controls.py`
- `p2_19_stage0_stage2_results_hybrid_controls.csv`
- `p2_19_control_coverage_hybrid_summary.csv`
- `p2_19_stage0_stage2_comparison_hybrid_vs_v4_controls.csv`
- `p2_19_hybrid_controls_patch_note.md`
- `p2_19_readme_update_snippet.md`
