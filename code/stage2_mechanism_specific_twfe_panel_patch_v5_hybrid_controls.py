"""
Stage 2 Patch V5: Hybrid Controls + Mechanism-Specific TWFE
===========================================================
This patch strengthens the Stage 2 control layer by using a hybrid control stack.

Control stack
-------------
Market-based controls with broad panel coverage:
- logP
- vol60
- mom20

Fundamentals merged by ticker and public_date:
- bm
- debt_assets
- curr_ratio
- roa

Missingness handling:
- raw missing flags for each fundamental
- date-by-industry median imputation
- date median fallback
- overall median fallback

Fixed effects
-------------
Firm and date fixed effects are implemented with explicit dummy variables.
Standard errors are clustered by firm.

Goal
----
Improve control quality and estimability without pretending that the data
already contain a clean full-coverage market-cap variable.
"""
