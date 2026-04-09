# P2.16 preliminary Stage 2 results after Stage 0 integration

These results come from `stage2_mechanism_specific_twfe_panel_patch.py` using the current integration map and the current policy file.

## Caveat

The current policy file does not yet contain mechanism-specific daily text intensities, so the patch fell back to the shared normalized daily policy index (`dpi01`) for all mechanisms. This means the results are a **structural preliminary test** of the Stage 0 → Stage 2 interface, not the final mechanism-separated specification.

## Baseline vs mechanism-specific summary

### IRA
- Baseline `ExpoQuick_it`: coef=-0.3090, p=<0.001
- `subsidy_expo_it_dm`: coef=-0.3737, p=<0.001
- `compliance_expo_it_dm`: coef=-0.6208, p=0.053
- `credit_market_expo_it_dm`: coef=0.0409, p=0.863
- `demand_pull_expo_it_dm`: coef=-0.2778, p=0.066

### LCFS
- Baseline `ExpoQuick_it`: coef=-0.0303, p=0.617
- `subsidy_expo_it_dm`: coef=0.0712, p=0.604
- `compliance_expo_it_dm`: coef=0.0693, p=0.873
- `credit_market_expo_it_dm`: coef=-0.0369, p=0.736
- `demand_pull_expo_it_dm`: coef=-0.0855, p=0.736

### RFS2
- Baseline `ExpoQuick_it`: coef=0.3318, p=0.009
- `subsidy_expo_it_dm`: coef=0.6528, p=0.004
- `compliance_expo_it_dm`: coef=-0.0947, p=0.910
- `credit_market_expo_it_dm`: coef=0.3476, p=0.091
- `demand_pull_expo_it_dm`: coef=-0.1813, p=0.717

## Immediate read

- IRA: the negative signal remains and loads mainly on `subsidy_expo_it`, with weaker negative loading on `compliance_expo_it` and `demand_pull_expo_it`.
- LCFS: this run does **not** recover the earlier strong LCFS result. Both the baseline and mechanism-specific specifications are insignificant in the current patch run.
- RFS2: the positive signal remains and loads mainly on `subsidy_expo_it`, with a weaker positive `credit_market_expo_it` coefficient.

## Output files

- `stage2_mechanism_outputs/panel_results_baseline_*.txt`
- `stage2_mechanism_outputs/panel_results_mechanism_*.txt`
- `p2_16_stage0_stage2_preliminary_results_summary.csv`