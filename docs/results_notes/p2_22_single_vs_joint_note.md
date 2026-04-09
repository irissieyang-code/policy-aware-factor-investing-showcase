# P2.22 single-mechanism vs joint-mechanism specification pack

This step tests whether the weak mechanism results are mainly coming from:
1. mechanism overlap within the same regression, or
2. dilution from boundary (`edge`) issuers.

## Specification grid

Two sample sets:
- `main_only`
- `main_plus_edge`

Three model types:
- `baseline`
- `single_mechanism`
- `joint_mechanism`

The control stack follows the de-collinearized version from P2.21:
- `logP`
- `mom20`
- `beta60`
- `ivol60`
- `bm`
- `debt_assets`
- `curr_ratio`
- `roa`
- missing flags for the accounting controls

## Interpretation logic

- If a mechanism is visible in `single_mechanism` but disappears in `joint_mechanism`, that points to overlap across channels.
- If a mechanism is stronger in `main_only` than in `main_plus_edge`, that points to dilution from boundary issuers.
- If a mechanism is weak in all four combinations, then the current signal is simply not stable enough under the strengthened specification.

## Files produced

- `p2_22_stage0_stage2_single_vs_joint_results.csv`
- `p2_22_stage0_stage2_single_vs_joint_comparison.csv`
- `p2_22_stage0_stage2_spec_panel_metadata.csv`
- `p2_22_single_vs_joint_note.md`
- `p2_22_readme_update_snippet.md`
- detailed text outputs in `stage2_mechanism_outputs_v6_specs/`
