# P2.8 firm-side manual calibration queue closure

This note closes the current issuer-by-issuer manual-calibration queue for the SEC-direct universe.

## Final status after P2.8

- Total SEC-direct issuers reviewed in the master table: 45
- `keep`: 10
- `edge`: 25
- `control`: 7
- `drop`: 3

## What changed in this step

1. Closed the remaining Tier 3 adjacent queue with official-materials review.
2. Closed the Tier 4 control queue with official business-identity review.
3. Tightened obvious universe noise in the drop set.
4. Reclassified BioLargo from adjacent edge to non-core control.
5. Reclassified Plastic2Oil from edge to drop after confirming revoked SEC registration.

## Interpretation

At this point, the firm-side layer has a complete issuer-by-issuer calibration table across the full SEC-direct queue.
The table is now suitable for three uses:

- defining the main operating sample (`keep`)
- testing spillovers and boundary cases (`edge`)
- running false-positive checks (`control`) and universe cleanup (`drop`)

## Suggested next technical step

Use the calibrated primary and secondary mechanisms to build mechanism-specific firm exposure columns before reintegrating the text layer into Stage 2.

## Files produced at this step

- `outputs/firm_text_wip/p2_sec_direct_issuers_manual_calibration_template_v6_full_queue_reviewed.csv`
- `outputs/firm_text_wip/p2_sec_direct_issuers_final_status_summary.csv`
- `docs/p2_8_firm_side_queue_closure.md`
- `docs/p2_8_readme_update_snippet.md`