"""
Stage 2 Patch V7: De-collinearized Controls
===========================================
This patch keeps the richer market-information block, but removes one
highly collinear volatility control to improve numerical stability.

Control design
--------------
Retained market controls:
- logP
- mom20
- beta60
- ivol60

Dropped from the previous pass:
- vol60

Reason
------
`vol60` and `ivol60` were almost collinear in the current panel.
This version keeps `ivol60` as the cleaner residual-risk control and removes
the redundant broad-volatility term.
"""
