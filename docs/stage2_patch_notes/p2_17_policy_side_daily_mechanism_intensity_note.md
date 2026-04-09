# P2.17 policy-side daily mechanism intensity construction and rerun

This step addresses the first remaining limitation in the Stage 0 → Stage 2 bridge:
the earlier mechanism-specific patch still assigned all mechanisms the same shared daily policy factor `dpi01`.

## What was added

Two new policy-side files were created:

1. `p0_policy_doc_mechanism_priors_v1.csv`
   - a document-level mechanism-prior table for the 14 logical policy documents
   - includes:
     - document date
     - date-source note
     - manual mechanism shares
     - legal weight
     - persistence type
     - rationale

2. `All_Daily_Policy_Data_with_policy_mechanisms_v1.csv`
   - extends the original daily policy index with policy-specific mechanism series:
     - `IRA_subsidy_intensity_t`
     - `IRA_compliance_intensity_t`
     - `IRA_credit_market_intensity_t`
     - `IRA_demand_pull_intensity_t`
     - and the same structure for `LCFS` and `RFS2`

## Construction logic

The policy-side daily mechanism intensities use a transparent hybrid rule:

- Start from the 14 official-source documents in `p0_policy_docs_master.csv`
- Assign each document:
  - a mechanism-share vector
  - a legal-weight scalar
  - a persistence class (`statute`, `regulation`, `guidance`, `notice`, `revision`, `guide`)
- Build daily document influence using a persistence-aware decay rule
- Blend:
  - a policy-level baseline mechanism profile
  - a local document-time profile
- Multiply the resulting mechanism shares by the normalized daily policy index `dpi01`

This creates policy-specific daily series that no longer force all four mechanisms to move with the same single regressor.

## Important caveat

This is still a provisional policy-side measurement layer.

The document dates for several guidance / notice files were inferred from:
- source filenames
- source URLs
- notice numbering conventions
rather than being recovered from a full text-extraction table with exact release timestamps.

That means the new daily mechanism series are much better than the pure `dpi01` fallback,
but they are still a reconstruction layer rather than a final publication-grade policy-time series.

## Rerun result

Using the new policy-specific daily intensities, the mechanism-specific Stage 2 patch was rerun in:

`stage2_mechanism_outputs_v2/`

The main pattern from the rerun is:

- `IRA`: negative effects load most clearly on `subsidy_expo_it`, with weaker negative loading on `compliance_expo_it` and `demand_pull_expo_it`
- `LCFS`: still weak in this reconstruction
- `RFS2`: positive effects load strongly on `subsidy_expo_it` and also on `credit_market_expo_it`

## Why this matters

This is the first version of the Stage 0 → Stage 2 bridge where:
- firm-side mechanism separation is active
- policy-side daily mechanism separation is also active
- the model is no longer relying on one shared daily text regressor for all four channels
