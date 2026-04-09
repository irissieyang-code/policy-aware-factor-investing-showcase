# P2.21 de-collinearized controls pass

This step strengthens the control layer by removing a clear multicollinearity problem.

## Diagnostic finding

The previous control stack contained both:
- `vol60`
- `ivol60`

In the current panel these two were almost redundant, which created very high VIF values.

## Change made

This version drops `vol60` and keeps:
- `logP`
- `mom20`
- `beta60`
- `ivol60`

plus the same accounting controls and missing flags.

## Why this matters

This is not about forcing significance.
It is about making the control architecture less fragile and easier to interpret.

A cleaner control stack gives more credible inference even when the resulting coefficients remain weak.

## Files produced

- `p2_21_control_vif_diagnostic.csv`
- `stage2_mechanism_specific_twfe_panel_patch_v7_decollinearized_controls.py`
- `p2_21_stage0_stage2_results_decollinearized_controls.csv`
- `p2_21_stage0_stage2_comparison_decollinearized_vs_market_plus_fundamentals.csv`
- `p2_21_decollinearized_controls_note.md`
- `p2_21_readme_update_snippet.md`
