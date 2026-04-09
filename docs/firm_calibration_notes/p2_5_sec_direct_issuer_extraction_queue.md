# P2.5 SEC-direct issuer extraction queue and manual calibration worklog

This note continues the Stage 0 firm-side manual calibration workflow after the preliminary issuer-by-issuer fill.

## Current status

- SEC-direct issuers in queue: 45
- Batch 1 extracted anchors with business text already reviewed: 0
- Preliminary sample decisions: keep=10, edge=27, control=6, drop=2

## Priority tiers

- **tier_1_core**: 10 issuers
- **tier_2_boundary**: 10 issuers
- **tier_3_adjacent**: 17 issuers
- **tier_4_control**: 6 issuers
- **tier_5_drop**: 2 issuers

## Tier 1 core extraction order

1. **AMTX** | Aemetis, Inc. | primary=credit_market_exposure
2. **ALTO** | Alto Ingredients, Inc. | primary=demand_pull_exposure
3. **GPRE** | Green Plains Inc. | primary=credit_market_exposure
4. **GEVO** | Gevo, Inc. | primary=subsidy_exposure
5. **REX** | REX American Resources Corporation | primary=credit_market_exposure
6. **VLO** | Valero Energy Corporation | primary=compliance_exposure
7. **FF** | FutureFuel Corp. | primary=subsidy_exposure
8. **DINO** | HF Sinclair Corporation | primary=demand_pull_exposure
9. **CLMT** | Calumet, Inc. | primary=subsidy_exposure
10. **HEOL** | Highwater Ethanol, LLC | primary=demand_pull_exposure

## Tier 2 boundary tests

1. **PBF** | PBF Energy Inc. | current primary=compliance_exposure
2. **PARR** | Par Pacific Holdings, Inc. | current primary=demand_pull_exposure
3. **MPC** | Marathon Petroleum Corporation | current primary=compliance_exposure
4. **PSX** | Phillips 66 | current primary=compliance_exposure
5. **CVI** | CVR Energy, Inc. | current primary=compliance_exposure
6. **DK** | Delek US Holdings, Inc. | current primary=compliance_exposure
7. **LIN** | Linde plc | current primary=demand_pull_exposure
8. **APD** | Air Products and Chemicals, Inc. | current primary=demand_pull_exposure
9. **BP** | BP p.l.c. | current primary=demand_pull_exposure
10. **CVX** | Chevron Corporation | current primary=demand_pull_exposure

## Calibration rules to apply in the next wave

1. Keep the v2 cosine-similarity scores as the raw model layer, but do not treat the top score as final without business-text review.
2. Distinguish direct sustainable-fuel operating exposure from broader transition language. Hydrogen / decarbonization wording alone is not enough to classify a firm as a core fuel-policy issuer.
3. Separate generic regulatory language from policy-channel-specific compliance language. EPA / FDA / permit text may signal generic regulation rather than LCFS / RIN / SAF compliance.
4. Preserve secondary mechanisms when overlap is real. ALTO-style subsidy plus demand-pull overlap should be recorded, not flattened.
5. Maintain negative controls. Non-core regulatory issuers remain useful for false-positive checks in the firm-side pipeline.

## Files produced at this step

- `outputs/firm_text_wip/p2_sec_direct_issuers_extraction_priority_queue.csv`
- `docs/p2_5_sec_direct_issuer_extraction_queue.md`
- `docs/p2_5_readme_update_snippet.md`
