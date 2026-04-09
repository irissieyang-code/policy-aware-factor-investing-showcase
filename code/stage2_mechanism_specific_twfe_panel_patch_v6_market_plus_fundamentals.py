"""
Stage 2 Patch V6: Market-Plus-Fundamentals Controls
===================================================
This patch strengthens the control layer beyond the earlier hybrid-controls pass.

Added market-based controls:
- logP
- vol60
- mom20
- beta60
- ivol60

Retained fundamentals:
- bm
- debt_assets
- curr_ratio
- roa
- raw missing flags for each fundamental

Purpose:
Use a richer market-information block when clean market-cap data are unavailable.
"""
