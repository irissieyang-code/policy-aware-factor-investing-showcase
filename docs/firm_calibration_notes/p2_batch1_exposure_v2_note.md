# P2.3 Batch 1 firm-side mechanism exposure schema v2

This version upgrades the first-pass keyword-density approach to a policy-prototype TF-IDF cosine similarity approach.
Each mechanism exposure is computed as cosine(firm business text, official policy mechanism prototype) × domain gate.

Mechanism prototypes were built from official policy text sentences matched from the extracted IRA/LCFS corpus.
Domain gate uses only mechanical counts of biofuel / hydrogen / refining domain terms.

## Results
- AMTX: dominant=credit_market_exposure; subsidy=0.0976, compliance=0.1396, credit_market=0.1440, demand_pull=0.1244.
- APD: dominant=demand_pull_exposure; subsidy=0.0359, compliance=0.0206, credit_market=0.0143, demand_pull=0.0474.
- BCPC: dominant=compliance_exposure; subsidy=0.0083, compliance=0.0114, credit_market=0.0069, demand_pull=0.0080.
- ALTO: dominant=demand_pull_exposure; subsidy=0.0905, compliance=0.0941, credit_market=0.0901, demand_pull=0.1080.
