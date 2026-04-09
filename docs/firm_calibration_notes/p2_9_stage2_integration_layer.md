# P2.9 Stage 2 integration layer from manual firm-side calibration

This step converts the full issuer-by-issuer manual calibration table into a Stage-2-ready integration layer.

## What this step adds

1. A compact integration map for each SEC-direct issuer.
2. Mechanism-specific manual weights based on the calibrated primary and secondary mechanisms.
3. Confidence-adjusted and sample-adjusted weights for future Stage 2 specifications.
4. Explicit sample splits for main operating, boundary spillover, false-positive control, and excluded drop sets.

## Weighting rule used

- Primary mechanism = 1.0
- Secondary mechanism = 0.5
- Manual confidence score:
  - high = 1.00
  - medium_high = 0.85
  - medium = 0.70
  - medium_low = 0.55
  - low = 0.40
- Sample inclusion weight:
  - keep = 1.00
  - edge = 0.60
  - control = 0.35
  - drop = 0.00

## Intended use

The integration map is designed to sit between the manual-calibration layer and the next Stage 2 specification update. It can be merged by ticker into the firm-day panel and used to construct mechanism-specific exposure terms such as:

- `SubsidyExposure_j`
- `ComplianceExposure_j`
- `CreditMarketExposure_j`
- `DemandPullExposure_j`

These can then be interacted with matching policy-side text intensities instead of relying on a single shared `Exposure_pre` regressor.

## Files produced

- `outputs/firm_text_wip/p2_sec_direct_issuers_stage2_integration_map.csv`
- `outputs/firm_text_wip/p2_main_operating_sample.csv`
- `outputs/firm_text_wip/p2_boundary_spillover_sample.csv`
- `outputs/firm_text_wip/p2_false_positive_control_sample.csv`
- `outputs/firm_text_wip/p2_excluded_drop_sample.csv`
- `outputs/firm_text_wip/p2_mechanism_weight_summary.csv`
- `docs/p2_9_stage2_integration_layer.md`