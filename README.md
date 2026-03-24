# From Causal Evidence to Mechanism-Aware Signals

**A Dual-Track Framework for Policy-Aware Factor Investing in the Sustainable Fuel Sector**

This repository contains the research pipeline and ongoing text-analysis extension for a project studying how major U.S. climate policy shocks are priced in the cross-section of sustainable fuel equities.

---

## Project Structure

The project has a completed empirical core (Stage 1 + Stage 2) and an in-progress text measurement extension (Stage 0).

### Stage 1 — Weighted Event Study (Completed)

Detects short-window abnormal returns around three policy events using firm-level Fama–French 5-factor models. A wide treatment definition assigns value-chain weights (core = 1.0, edge = 0.5) to capture indirect policy exposure. Test statistics include Patell Z, Corrado rank test, and cluster bootstrap p-values.

### Stage 2 — Exposure-Based TWFE Panel (Completed)

Converts event-identified signals into a structural policy-aware factor by interacting pre-policy firm exposure with daily policy intensity in a Bartik-style two-way fixed-effects panel. Reports AR and CAR regressions with clustered standard errors and lead–lag event-time dynamics.

### Stage 0 — Text-Based Policy Mechanism Measurement (In Progress)

Adds a text structuring layer to convert policy legislative language into structured mechanism variables. The goal is to move from narrative policy interpretation to auditable, testable mechanism measurement. This extension includes both a policy-side text pipeline and a firm-side annual-filing text pipeline.

---

## Results

### Stage 1: Short-Window Pricing of Policy Shocks

**Table R1. Weighted event study results.**

| Definition | Policy | Event | Window | n_treat | Mean CAR (%) | Patell Z | Corrado Z | Bootstrap p |
|---|---|---|---|---|---|---|---|---|
| Narrow (0/1) | IRA | 2022-08-16 | [0,1] | 4 | 0.535 | 0.928 | −0.556 | / |
| Narrow (0/1) | LCFS | 2023-01-03 | [0,1] | 6 | 1.137 | −0.073 | 0.473 | / |
| Narrow (0/1) | RFS2 | 2021-01-04 | [0,1] | 21 | 0.787 | 2.075 | 4.837 | / |
| Wide (weighted) | IRA | 2022-08-16 | [0,1] | 56 | 0.821 | 2.338 | −0.314 | 0.927 |
| Wide (weighted) | IRA | 2022-08-16 | [−1,1] | 56 | 0.153 | 0.183 | −1.487 | 0.880 |
| Wide (weighted) | LCFS | 2023-01-03 | [0,1] | 51 | −0.385 | 0.731 | −3.046 | 0.955 |
| Wide (weighted) | RFS2 | 2021-01-04 | [0,1] | 21 | 0.787 | 2.075 | 4.837 | 0.072 |

RFS2 displays the cleanest signal: weighted treated firms earn positive, statistically significant CAR in all non-overlapping windows. LCFS shows a negative response that becomes clearer as the window widens, consistent with a gradual re-pricing of updated credit economics. IRA exhibits small, mixed short-window reactions consistent with the diffuse scope of the Act.

### Stage 2: Exposure-Scaled Abnormal Returns

**Table R2. AR–TWFE policy betas.**

| Policy | Event | β(ExpoQuick) | se | t | p | N |
|---|---|---|---|---|---|---|
| IRA | 2022-08-16 | −0.5440 | 1.1215 | −0.485 | 0.6276 | 620,917 |
| LCFS | 2023-01-03 | −9.4307 | 2.1056 | −4.479 | 0 | 538,128 |
| RFS2 | 2021-01-04 | 15.552 | 6.164 | 2.523 | 0.0116 | 538,178 |

**Table R3. Economic magnitudes (IQR effect).**

| Policy | Event | β(AR–TWFE) | Exposure IQR | Δ AR (75th − 25th) |
|---|---|---|---|---|
| IRA | 2022-08-16 | −0.5440 | 0.000859 | −0.047 pp |
| LCFS | 2023-01-03 | −9.4307 | 0.000855 | −0.806 pp |
| RFS2 | 2021-01-04 | 15.552 | 0.000846 | +1.316 pp |

Moving from the 25th to the 75th exposure percentile lowers abnormal returns by approximately 0.81 pp for LCFS and raises them by approximately 1.32 pp for RFS2. These magnitudes are comparable to standard factor shocks and large enough to matter for portfolio construction.

---

## Stage 0 Extension: Current Status

### Completed: Policy-Side Corpus & Source Infrastructure

- **Official-source manifest**: 14 policy documents across IRA, LCFS, and RFS2 anchored to enrolled bill text, IRS notices, CARB amendments, and EPA rules, with provenance tracking (`p0_source_manifest.csv`, `p0_policy_docs_master.csv`).
- **Clause-level extraction pipeline**: Implemented in `stage0_text_upgrade_p0_to_p23.ipynb`. Processes policy text into clause-level chunks, classifies mechanism channels (tax credit/subsidy, compliance cost, margin impact, credit market, demand pull, capex incentive, financing certainty), and scores five continuous dimensions (benefit, burden, specificity, certainty, breadth).
- **Validation framework**: First-round human review on 24 clauses — mechanism match rate 54.2%, sign match rate 62.5%. Results in `outputs/stage0_text/validation/`.
- **Structural diagnostic**: Analysis of the text measurement design revealed that policy-level text scores (one constant per mechanism per policy) cannot create cross-sectional variation in mechanism-specific exposure. True mechanism separation requires firm-specific mechanism exposures, which motivates the firm-side text pipeline. See `p0_3_diagnostic_note.txt`.

### In Progress: Firm-Side Text Analysis

- **Issuer universe routing**: 69 tickers → 66 issuers → 45 SEC-direct filers identified mechanically from the data.
- **Batch 1 proof of concept**: SEC 10-K Item 1 "Business" sections extracted from EDGAR for 4 firms (AMTX, APD, BCPC, ALTO).
- **Mechanism-specific firm exposure (v2)**: Policy-prototype × firm-text TF-IDF cosine similarity with domain gate, producing 4-dimensional mechanism exposure (subsidy, compliance, credit market, demand pull) per firm.
- **Not yet completed**: Full 45-issuer extraction, mechanism-specific interaction regressions (SubsidyExposure × SubsidyIntensity, etc.), second-round validation.

---

## Repository Structure

```
code/
├── stage1_weighted_event_study.py          # Stage 1: weighted event study
├── stage2_exposure_twfe_panel.py           # Stage 2: Bartik-style TWFE panel
└── stage0_text_upgrade_p0_to_p23.ipynb     # Stage 0: text analysis pipeline (P0→P2.3)

data/
├── All_Daily_Policy_Data.csv
├──   [not included in public repo] Policy_Influenced_Stock_Price_With_FF_5_Factors.csv
├──   [not included in public repo] Financial_Ratios_Ticker.csv
├──   [not included in public repo] {AMTX,ALTO,APD,BCPC}_business_section.txt   # SEC 10-K Item 1 extracts
└── {subsidy,compliance,credit_market,demand_pull}_exposure_prototype.txt

outputs/
├── stage0_text/                         # Policy-side text infrastructure
│   ├── p0_source_manifest.csv                   # Official source tracking
│   ├── p0_policy_docs_master.csv                # Document registry
│   ├── p0_3_diagnostic_note.txt                 # Structural diagnostic
│   └── validation/                              # Human validation results
│       ├── p0_validation_labeled.csv
│       ├── p0_validation_summary.csv
│       ├── p0_validation_mechanism_mismatches.csv
│       └── p0_validation_sign_mismatches.csv
└── firm_text_wip/                       # Firm-side (in progress, 4/45 issuers)
    ├── p2_issuer_universe_map.csv
    ├── p2_sec_direct_issuers.csv
    ├── p2_batch1_firm_business_sections.csv
    ├── p2_batch1_firm_exposure_schema_v2.csv
    └── p2_batch1_exposure_v2_note.md

docs/
├── p1_research_update_memo.md           # Research update with results & limitations
└── p1_project_summary_onepager.md       # One-page project summary
```

## Data

The empirical analysis uses three datasets from WRDS:
- **Policy Influenced Stock Price with FF 5 Factors** — 172,358 firm-days, 69 firms, 5 NAICS industries, 2014–2024
- **Financial Ratios by Ticker** — firm fundamentals
- **All Daily Policy Data** — daily policy intensity index, 14,844 observations

## Data Note

This public repository is a presentation version prepared for research discussion.

Some input datasets are not included because they are derived from licensed academic databases or reconstructed from public filing text through a separate preprocessing workflow.

The repository retains the core code structure, documentation, and selected outputs necessary to illustrate the research design and implementation.

## Methods

- **Factor models**: Firm-level FF5 OLS in pre-event window [−120, −20]
- **Event study**: Weighted Patell Z, Corrado rank, cluster bootstrap (B=2000)
- **TWFE panel**: Two-way FE (firm + date) with two-way clustered SE via PanelOLS
- **Text extraction**: TF-IDF + seed-dictionary cosine similarity classification
- **Firm-text matching**: Policy mechanism prototypes × SEC 10-K text cosine similarity with domain gate
- **Validation**: Stratified human review with mechanism and sign match rates

## Requirements

```
python >= 3.10
pandas, numpy, scipy, statsmodels
scikit-learn (for Stage 0 text pipeline)
matplotlib
linearmodels (for PanelOLS in Stage 2)
```

## Authors

Jingyi Yang (Vancouver School of Economics, UBC) and co-authors.

## Status

Stage 1 and Stage 2 are complete with published results. Stage 0 text extension is an active prototype — policy-side corpus infrastructure and validation are done; firm-side text analysis has a working proof of concept on 4 issuers with 41 remaining. Limitations and next steps are in [`docs/p1_research_update_memo.md`](docs/p1_research_update_memo.md).
