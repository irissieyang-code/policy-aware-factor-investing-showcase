# Research Update Memo
## Text-Structured Extension of a Policy-Aware Factor Framework in Sustainable Fuels

### Project context
The original project studies whether major sustainable-fuel policy shocks are reflected in cross-sectional stock-price responses and whether those responses can be translated into policy-aware signals. The base design already includes a weighted event-study layer and a Stage 2 exposure-based panel design.

This update adds a **Stage 0 text-structuring layer** so that policy content is no longer used only as narrative interpretation. Instead, policy language is converted into structured, auditable mechanism variables that can be linked back to the original empirical design.

### What was added
Three additions were completed.

1. **Official-source policy corpus reconstruction**
   - Built a source manifest and policy-doc master table from official materials.
   - IRA / SAF documents were anchored to the enrolled Inflation Reduction Act bill text and IRS SAF notices.
   - LCFS documents were anchored to CARB regulation, amendment, guidance, and credit-market compliance materials.
   - RFS2 documents were anchored to EPA annual-rule and compliance materials.

2. **Clause-level text measurement prototype**
   - Processed 14 logical policy documents in the reconstructed corpus, with 56 clause-level chunks in the current extraction table.
   - Used a deterministic TF-IDF + seed-dictionary workflow to assign:
     - mechanism channel
     - affected actor
     - expected sign
     - five continuous scores: benefit, burden, specificity, certainty, breadth
   - Weighting incorporated legal triggers and mechanism confidence.

3. **Text-enhanced integration into Stage 2**
   - Replaced or augmented the original policy-intensity term with text-derived mechanism scores.
   - Estimated text-enhanced versions of the original panel specification by policy.

### Main empirical takeaways
The text layer already produces three useful results.

**First, policy documents do not collapse into a single verbal story.**
The mechanism heatmap and radar profile show that IRA, LCFS, and RFS2 have distinct text signatures rather than one pooled “policy” signal.

**Second, the text layer sharpens the LCFS result.**
In the original Stage 2 specification, the LCFS exposure term is marginally significant (t = -1.826, p = 0.0723). In the text-enhanced specifications, the LCFS term strengthens to about t = -2.352 with p = 0.0216. This does not prove causal mechanism separation yet, but it does show that structured policy text can improve measurement relative to a coarse policy-intensity input.

**Third, the text layer does not mechanically manufacture significance where the baseline signal is weak.**
IRA and RFS2 remain weak after text enhancement. That is an important result for credibility: the text layer appears to sharpen an existing signal where policy-content structure is informative, not to create significance everywhere.

### Validation status
A first-round manual review was completed on a 24-clause validation sample.

- Mechanism match rate: **54.17%**
- Sign match rate: **62.50%**

By policy:
- IRA: mechanism 50.0%, sign 87.5%
- LCFS: mechanism 62.5%, sign 37.5%
- RFS2: mechanism 50.0%, sign 62.5%

Interpretation:
- The current prototype is better at directional sign than at fine mechanism labeling.
- LCFS mismatches show that compliance burden and margin-impact language are still being blended too often.
- IRA mismatches show that credit, certainty, and threshold language still overlap in the present coding logic.

### What the diagnostics revealed
The current text-enhanced Stage 2 design still has an important structural limitation.

Within each policy, the text specifications for benefit, burden, specificity, and certainty generate nearly identical t-statistics. This indicates that the present regressors are effectively scalar rescalings of the same base exposure term rather than truly distinct mechanism tests.

That means the current Stage 0 prototype already demonstrates:
- corpus building
- structured extraction
- validation discipline
- regression linkage

But it does **not yet** fully demonstrate mechanism separation in the econometric sense.

### Most important next step
The next technical step is to move from a single firm-side exposure term to **mechanism-specific firm exposures**, for example:
- subsidy / tax-credit exposure
- compliance-burden exposure
- credit-market exposure

Those firm-side mechanism exposures can then be matched with policy-side mechanism intensities:
- SubsidyExposure_j × SubsidyIntensity_t
- ComplianceExposure_j × ComplianceIntensity_t
- CreditMarketExposure_j × CreditMarketIntensity_t

This is the clearest path from “text-enhanced narrative measurement” to “mechanism-aware empirical testing.”

### Why this matters for a research-assistant role
This extension is useful beyond this paper because it demonstrates a workflow directly relevant to policy- and firm-level research support:

- official-source document collection
- corpus construction and documentation
- clause-level text processing
- structured variable construction
- validation and mismatch analysis
- integration of text-derived measures into panel regressions
- short research-memo style interpretation of strengths and limitations

### Official-source basis for the reconstructed corpus
Official materials used to anchor the corpus include:
- Inflation Reduction Act enrolled bill text and IRS Notice 2023-6 / 2024-6 / 2024-37 for SAF-related IRA content
- CARB LCFS regulation text, amendment notices, guidance, and credit-market compliance materials
- EPA Renewable Fuel Standard annual-rule and compliance materials

This memo describes a working prototype, not a finished publication-stage text model. Its value is that it turns policy text from hand-written narrative into an auditable intermediate measurement layer that can be refined further.
