# P2.14 alt-source bridge into the Stage 2 integration layer

This step creates a bridge between the closed alt-source queue and the existing SEC-direct Stage 2 integration layer.

## Main result

Only one alt-source issuer is promoted into the provisional Stage 2 bridge:

- `CRDE` | Cardinal Ethanol, LLC

All other alt-source names remain either watchlist, duplicate, family-link, or legacy/speculative holdout cases.

## Why only CRDE is included

`CRDE` is the only alt-source issuer with a strong enough current operating profile, direct ethanol-production fit, and no confirmed duplicate-family conflict with the reviewed SEC-direct set.

## Holdout logic

- `REGX` stays out because of the Gevo family-link issue
- `REPYY`, `AIQUY`, `MOTNF`, and similar names remain useful watchlist candidates for later extension work
- legacy or speculative names remain outside the current operating Stage 2 integration set

## Files produced

- `outputs/firm_text_wip/p2_alt_source_stage2_bridge_candidates.csv`
- `outputs/firm_text_wip/p2_alt_source_stage2_holdout_watchlist.csv`
- `outputs/firm_text_wip/p2_stage2_integration_map_v2_with_alt_bridge.csv`
- `outputs/firm_text_wip/p2_stage2_alt_bridge_summary.csv`
- `docs/p2_14_alt_source_stage2_bridge.md`
- `docs/p2_14_readme_update_snippet.md`