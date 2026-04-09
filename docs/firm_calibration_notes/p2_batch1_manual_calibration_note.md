# P2.4 Batch 1 firm-side manual calibration note

This file records the first manual calibration pass for the firm-side text analysis layer.
It is meant to sit on top of the existing P2.3 cosine-similarity exposure schema, not replace it.

## Why this file exists
The P2.3 pipeline already produces mechanism-specific exposure scores from firm business text.
However, the first four issuers show that raw model scores still need issuer-by-issuer interpretation.
The main issue is not complete failure. The main issue is overlap and false inflation.

Three recurring error types appeared in Batch 1:
1. **Mechanism overlap**: one issuer can genuinely load on more than one channel.
2. **Adjacent-transition inflation**: hydrogen or broad decarbonization language can lift demand-pull scores.
3. **Generic-regulation inflation**: permits, registrations, and inspection language can lift compliance scores without direct sustainable-fuel relevance.

## Calibration fields
Each issuer should ultimately receive the following fields:
- policy_relevance: `core`, `adjacent`, `non_core`
- primary_mechanism
- secondary_mechanism
- ecosystem_role
- confidence
- sample_decision: `keep`, `edge`, `control`
- why_model_score_is_reasonable
- possible_false_inflation_source

## Batch 1 calibrated labels

| ticker | policy_relevance | primary_mechanism | secondary_mechanism | ecosystem_role | confidence | sample_decision |
|---|---|---|---|---|---|---|
| AMTX | core | credit_market_exposure | compliance_exposure | core_low_carbon_fuel_credit_linked_producer | high | keep |
| ALTO | core | demand_pull_exposure | subsidy_exposure | core_low_carbon_fuel_tax_credit_player | medium_high | keep |
| APD | adjacent | demand_pull_exposure | compliance_exposure | adjacent_hydrogen_transition_platform | medium | edge |
| BCPC | non_core | compliance_exposure | none_or_weak | non_core_regulatory_control | high | control |

## Interpretation by issuer

### AMTX
AMTX should remain a core issuer in the main sample.
The text directly connects ethanol, RNG, biodiesel, and low or negative carbon-intensity fuel economics.
Its credit-market result is therefore interpretable as a real policy-linked transmission channel.

### ALTO
ALTO should remain a core issuer in the main sample.
The dominant demand-pull result is defensible, but this issuer also loads strongly on subsidy language because the filing explicitly discusses tax-credit and CCS economics.
This is a useful anchor for overlapping policy channels.

### APD
APD should be retained only as an adjacent-transition issuer.
Its hydrogen and clean-energy strategy is economically relevant to transition demand, but it is not a core sustainable-fuel credit-market issuer.

### BCPC
BCPC should be used as a non-core regulatory control.
Its compliance-heavy text is useful for stress-testing the compliance channel against generic regulatory language.

## Recommended next step
Use the same schema for all 45 SEC-direct issuers.
Do not collapse everything into one label too early.
Preserve both primary and secondary mechanisms, especially for mixed cases like ALTO.
