# P2.13 Alt-or-no-SEC queue closure

This note closes the current alt-source routing and manual-calibration pass for the 21 `Alt_or_no_SEC` issuers.

## Final status after P2.13

- Total alt-source issuers reviewed: 21
- provisional `keep`: 1
- provisional `edge`: 14
- provisional `drop`: 6

## Main takeaways

1. Only one alt-source issuer, `CRDE`, currently merits a provisional `keep` classification.
2. `REGX` remains fuel-relevant but is screened out of direct integration because of a family link to `GEVO`.
3. The tier-2 adjacent names are useful for future international extension work, but none of them should enter the main operating sample now.
4. Several names were resolved as identity-mismatch, duplicate-line, or stale legacy cases and should remain outside the main integration set.

## Recommended use

- Carry `CRDE` as the only serious alt-source candidate for future Stage 2 merge testing.
- Keep `REGX`, `REPYY`, `AIQUY`, and `MOTNF` on the watchlist for later extension work.
- Treat the remaining low-quality or duplicate names as out-of-scope unless the project explicitly expands beyond the current operating-universe standard.

## Files produced

- `outputs/firm_text_wip/p2_alt_or_no_sec_remaining_manual_calibration.csv`
- `outputs/firm_text_wip/p2_alt_or_no_sec_issuers_routing_queue_v4_closed.csv`
- `outputs/firm_text_wip/p2_alt_or_no_sec_final_status_summary.csv`
- `outputs/firm_text_wip/p2_alt_or_no_sec_final_candidate_screen.csv`
- `docs/p2_13_alt_or_no_sec_queue_closure.md`
- `docs/p2_13_readme_update_snippet.md`