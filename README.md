# Policy Risk Stress-Testing Framework for Sustainable Fuel Equities

**Mechanism-level exposure mapping for climate policy repricing risk**

## What this project does

This project takes three U.S. climate policies — the Inflation Reduction Act (IRA), California's Low Carbon Fuel Standard (LCFS), and the Renewable Fuel Standard 2 (RFS2) — and asks a practical question:

> If these policies tighten, shift, or expand, which firms are most exposed, through which channel, and by roughly how much?

The output is **not a forecast**. It is a **stress-test framework** that decomposes policy risk into mechanism-level channels, maps firm-level exposure to each channel, and produces directional signals with honestly stated limitations — designed to be approximately right rather than precisely wrong.

## Why this matters for institutional ESG risk management

When an investment team faces a new climate policy, the instinctive question is "is this good or bad for our portfolio?" That question is too blunt to act on. This framework offers a more useful decomposition:

1. **Which channel does the policy operate through?** A subsidy, a compliance mandate, a credit-market shift, or a demand-side pull are four different risks that hit four different types of firms.
2. **Where is the risk concentrated?** This project shows that LCFS repricing risk sits in a narrow set of core names, not the broad sector — meaning diligence and engagement resources should be concentrated, not spread thin.
3. **Where is there no risk to worry about?** RFS2 produces no detectable repricing signal under any specification. That is useful information: do not over-allocate risk budget to a channel that the market has already absorbed.

The deliverable is not a 66-company scoring database. It is a **replicable methodology**: given any new policy, how to decompose it into testable mechanism channels, define firm-level exposure, and validate whether the market actually prices each channel — with clear acknowledgement of what the data can and cannot support.

## How it works

The framework has three layers:

**Layer 1 — Policy pulse detection (Stage 1)**
A weighted event study detects whether policy announcements produce abnormal returns among exposed firms. Value-chain weights (core = 1.0, edge = 0.5) improve statistical power over narrow 0/1 treatment definitions.

**Layer 2 — Exposure-scaled panel (Stage 2)**
A two-way fixed-effects panel explains *who* moves and *by how much* by interacting pre-policy firm exposure with daily policy intensity (Bartik-style). The baseline is a Fama–French 5-factor model estimated in the pre-event window — this serves as the "if nothing changes" scenario.

**Layer 3 — Mechanism decomposition (Stage 0)**
Policy exposure is decomposed into four channels:
- **Subsidy** — direct fiscal incentives, tax credits, production subsidies
- **Compliance** — regulatory obligations, carbon-intensity benchmarks, reporting
- **Credit-market** — tradeable credits, RIN economics, carbon credit pricing
- **Demand-pull** — blending mandates, volume obligations, market creation

Firm-side exposure is measured by matching SEC 10-K Item 1 business descriptions to mechanism prototypes via TF-IDF cosine similarity, then manually calibrated issuer-by-issuer (45 SEC-direct + 21 alt-source issuers). Policy-side intensity is derived from official documents (IRA enrolled bill, CARB LCFS amendments, EPA RFS annual rules) time-expanded into daily mechanism series.

## Key results

### What is approximately right

| Policy | Finding | Practitioner implication |
|--------|---------|------------------------|
| **LCFS** | 3 mechanism channels strongly negative in core firms (p < 0.007) | Repricing risk is real and multi-channel — stress-test discount rates for core LCFS-exposed positions |
| **LCFS** | All signals vanish when edge firms are added | Risk is concentrated in a narrow set of names, not diffuse sector exposure — prioritize diligence accordingly |
| **IRA** | Credit-market channel positive in core (p = 0.048); demand-pull negative in broader sample (p < 0.001) | Core vs peripheral firms price IRA in opposite directions — exposure direction depends on where in the value chain |
| **RFS2** | No significant channel in any sample or specification | Current RFS2 framework does not create detectable repricing risk — do not over-allocate risk budget here |

### What the numbers mean (and don't mean)

The mechanism coefficients give **direction and relative magnitude**, not precise point estimates. A β of −503 on demand-pull for LCFS means "more demand-pull-exposed firms are repriced more negatively" — the exact number reflects variable scaling, not investable basis points. The useful information is the direction (negative), the concentration (core names only), and the multi-channel consistency.

## Limitations (stated upfront)

- **Small sample**: 66 firms in the NAICS-screened universe, 11 tickers in main-only, 35 in main+edge. Results indicate direction and relative ordering, not population parameters. This is a methodology demo, not a portfolio-wide scoring tool.
- **Text-based measurement**: Firm exposure scores are derived from business descriptions matched to prototypes. The direction is credible; exact magnitudes are approximate. No ground-truth validation (e.g., actual subsidy income or compliance cost breakdowns) has been performed.
- **Edge dilution is a feature**: The fact that signals disappear when boundary firms are added is not a data problem — it means risk is concentrated, which is useful for portfolio prioritization.
- **Not a trading signal**: This is a risk-monitoring and stress-testing tool, not an alpha signal. No claim is made about out-of-sample predictive power.

## What is transferable

The specific results are about three U.S. sustainable fuel policies. The methodology is not policy-specific:

| Step | What was done here | What it generalises to |
|------|-------------------|----------------------|
| Mechanism decomposition | IRA/LCFS/RFS2 → subsidy, compliance, credit-market, demand-pull | Any policy → identify the channels through which it affects firms |
| Firm-side exposure | SEC 10-K text matching + manual calibration | Any firm universe → map business descriptions to policy-relevant channels |
| Baseline vs scenario | Pre-event FF5 model vs post-event mechanism intensity | Any stress test → define "if nothing changes" and "if policy changes" |
| Direction validation | DID with progressive controls and robustness checks | Any hypothesis → test whether the market actually prices the channel |
| Risk concentration | main-only vs main+edge sample split | Any portfolio → distinguish concentrated risk from diffuse noise |

## Repository structure

### `code/`
Stage 2 mechanism-specific patch scripts with progressive control strengthening (baseline → policy-daily → controls → hybrid → market+fundamentals → de-collinearized).

### `data/`
- **Policy mechanism layer**: official document priors, daily mechanism intensity files (v1 → v2 hardened → v3 RFS2-event-aligned)
- **Firm calibration layer**: SEC-direct issuer calibration (45 issuers), alt-source routing (21 issuers), integration maps with policy-specific shrinkage weights
- **Sample labels**: keep / edge / control / drop per issuer

### `docs/`
Process notes covering each stage: calibration, queue management, mechanism patch, control strengthening, timing fix, and integrated rerun.

### `outputs/`
Result tables, comparison tables, interpretation summaries, coverage diagnostics. Key files:
- `p2_25_stage0_stage2_refined_results_with_rfs2_fix.csv` — final integrated results
- `p2_25_stage0_stage2_refined_interpretation_summary.csv` — best specification per policy × sample
- `p2_24_rfs2_timing_diagnostic_after_fix.csv` — RFS2 timing correction documentation

### `outputs/stage2_mechanism_outputs/`
Raw Stage 2 regression text outputs from the early rerun stage.

## Methodology at a glance

| Component | Approach | Purpose |
|-----------|----------|---------|
| Abnormal returns | Fama–French 5-factor residuals | Baseline: what returns look like if nothing changes |
| Event detection | Weighted CAR + Patell Z + Corrado rank + bootstrap | Does the policy create a detectable market reaction? |
| Exposure panel | TWFE with ExpoQuick = Exposure_pre × Post × dpi | Which firms react more, and by how much? |
| Mechanism decomposition | 4-channel exposure × 4-channel intensity | Through which channel does the risk transmit? |
| Robustness | Single vs joint mechanism, main-only vs main+edge, 6 control specifications | Are the results stable or fragile? |

## Original paper

Yang, Du, He, Liu, Xia (2025). "From Causal Evidence to Actionable Signals: A Dual-Track Framework for Policy-Aware Factor Investing in the Sustainable Fuel Sector." Full paper for the 21st CRRC, Sub-theme 6: CSR and Global Governance.

## How to use this repo

Replace the root `README.md` with this file, then unzip the update package into the repo root. The folder structure in the zip matches the repository layout. Review changes before committing.
