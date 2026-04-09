# P2.10 alt-source routing queue for non-SEC-direct issuers

This note starts the second firm-side workflow for the 21 issuers that were not included in the 45-name SEC-direct queue.

## Why these 21 names are separate

They were routed as `Alt_or_no_SEC` in the issuer-universe map, which means they do not fit the current direct SEC 10-K Item 1 Business extraction pipeline. They therefore require a separate routing pass before issuer-by-issuer manual calibration.

## Priority tiers

- **tier_1_alt_core**: 5
- **tier_2_adjacent**: 5
- **tier_3_speculative**: 3
- **tier_4_deduplicate**: 1
- **tier_5_identity_cleanup**: 7

## Tier 1 alt-core names

- **CCGY** | China Clean Energy Inc. | Check OTC disclosure and legacy SEC filings for business identity, then confirm whether biodiesel operations are still active.
- **CRDE** | Cardinal Ethanol, LLC | Pull latest available 10-K / annual filing and business description for ethanol, corn oil, and CO2 operations.
- **MEIL** | Methes Energies International Ltd. | Review latest available SEC/OTC filings and confirm whether biodiesel activity remains active versus legacy-only.
- **REGX** | Red Trail Energy, LLC | Pull latest available filing and business description for ethanol / carbon capture relevance.
- **XFLS** | Cycle Energy Industries Inc. / Xfuels Inc. | Review latest filings and company materials around biodiesel production at the Bieseker plant and confirm operating status.

## Tier 2 adjacent names

- **AIQUY** | L’Air Liquide S.A. ADR | Pull latest Air Liquide annual report / business overview and review hydrogen, low-carbon, and energy-transition sections.
- **CTXAY** | Ampol Limited ADR | Use Ampol annual report and sustainability disclosures; check for SAF, renewable fuels, and refining transition language.
- **MGYOY** | MOL Hungarian Oil and Gas Plc ADR | Use MOL annual report and transition disclosures to assess low-carbon fuels, refining, and petrochemicals positioning.
- **REPYY** | Repsol, S.A. ADR | Use Repsol annual report and low-carbon fuels disclosures, including SAF and renewable fuels sections.
- **RLNIY** | Reliance Industries Ltd ADR | Use Reliance annual report to assess fuels, refining, and new energy exposure.

## Tier 4 deduplication case

- **PBR.A** should be mapped to the existing issuer family rather than treated as a new stand-alone company: Same Petrobras family already appears in SEC-direct queue as PBR.

## Main cleanup bucket

The identity-cleanup tier contains names where current evidence points to shells, software, consumer electronics, or otherwise non-fuel business identities. These should be resolved before any text extraction is attempted.

## Files produced

- `outputs/firm_text_wip/p2_alt_or_no_sec_issuers_routing_queue.csv`
- `outputs/firm_text_wip/p2_alt_or_no_sec_routing_summary.csv`
- `docs/p2_10_alt_or_no_sec_routing_queue.md`
- `docs/p2_10_readme_update_snippet.md`