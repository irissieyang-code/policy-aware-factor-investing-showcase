# P2.15 mechanism-specific Stage 2 code patch

This step adds a code-level bridge from the issuer-level manual calibration outputs into the Stage 2 panel workflow.

## What the patch does

The new script, `stage2_mechanism_specific_twfe_panel_patch.py`, extends the original Stage 2 logic in three ways:

1. It reads the merged issuer-level integration map:
   - `p2_stage2_integration_map_v2_with_alt_bridge.csv`

2. It preserves the original `Exposure_pre` construction:
   - average pre-event industry share
   - multiplied by the original NAICS-based policy weight

3. It replaces the single shared text regressor with mechanism-specific exposure terms:
   - `subsidy_expo_it`
   - `compliance_expo_it`
   - `credit_market_expo_it`
   - `demand_pull_expo_it`

Each mechanism regressor is built as:

`Exposure_pre_j × mechanism_weight_j × mechanism_intensity_t`

## Important design choice

The patch does **not** discard the original Stage 2 exposure logic.  
Instead, it layers the issuer-level manual mechanism weights on top of the existing `Exposure_pre` structure.

This keeps two things at once:

- the original within-industry pre-event exposure logic
- the new issuer-level mechanism separation from the manual calibration layer

## Fallback rule

The script looks for policy-side mechanism intensity columns in the policy file.

If they do not yet exist, the script falls back to the shared normalized daily policy index `dpi01` for all mechanisms.

That means the code is immediately runnable as a structural patch, while still leaving room for a later upgrade once policy-side mechanism-specific daily intensities are finalized.

## Outputs

The script writes:
- mechanism-ready panel files
- baseline Stage 2 regression results
- mechanism-specific Stage 2 regression results

to:

`stage2_mechanism_outputs/`

## Why this matters

This is the first code-level step that directly addresses the earlier diagnostic problem:

the text-enhanced Stage 2 layer had been re-scaling one shared base regressor instead of identifying distinct channels.

This patch creates the correct interface for:

- issuer-level mechanism separation
- sample-specific inclusion logic
- controlled alt-source inclusion through the bridge map
- later interaction with policy-side text intensities
