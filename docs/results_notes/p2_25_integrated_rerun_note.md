# P2.25 integrated rerun with RFS2 timing fix

This step folds the corrected RFS2 timing layer from P2.24 back into the full refined Stage 0 → Stage 2 result pack.

## What changed

- All IRA and LCFS rows are carried over from P2.23 unchanged.
- All RFS2 rows are replaced with the timing-corrected outputs from P2.24.
- The integrated result table, comparison table, interpretation summary, and panel metadata are all refreshed.

## Why this matters

Before P2.24, the RFS2 policy-side mechanism intensities were zero inside the event window, so the RFS2 mechanism regressors were mechanically shut off.

After the timing correction:
- RFS2 coefficients are now mechanically interpretable.
- The lack of significance should now be read as a substantive result under the current specification, not a timing bug.

## Updated broad reading

- **IRA**: baseline negative result remains the most stable finding. Mechanism-level signals exist, but are still weaker than the baseline channel.
- **LCFS**: main-only specifications still carry the strongest mechanism evidence; main-plus-edge remains heavily diluted.
- **RFS2**: after fixing timing, coefficients are no longer forced to zero, but the mechanism signals remain below conventional significance thresholds in the current design.

## Files produced

- `p2_25_stage0_stage2_refined_results_with_rfs2_fix.csv`
- `p2_25_stage0_stage2_refined_results_comparison_vs_p23.csv`
- `p2_25_stage0_stage2_refined_interpretation_summary.csv`
- `p2_25_stage0_stage2_refined_panel_metadata.csv`
- `p2_25_rfs2_delta_vs_p23.csv`
- `p2_25_integrated_rerun_note.md`
- `p2_25_readme_update_snippet.md`
