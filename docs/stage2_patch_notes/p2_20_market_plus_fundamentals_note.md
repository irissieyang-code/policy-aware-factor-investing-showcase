# P2.20 market-plus-fundamentals strengthening pass

This step continues the control-layer strengthening work after the hybrid-controls pass.

## What changed

The new specification adds two more market-based controls with broad panel coverage:

- `beta60`
- `ivol60`

These sit on top of:
- `logP`
- `vol60`
- `mom20`

and the existing accounting controls:
- `bm`
- `debt_assets`
- `curr_ratio`
- `roa`

## Why this is better

The control stack is now less sensitive to the weakness of any single market proxy.

Even without a true market-cap variable, the model now observes:
- price level
- recent volatility
- recent momentum
- market beta
- idiosyncratic volatility

This is a more defensible market-information block than `logP` alone.

## Remaining limitation

This still does not fully solve the size problem.
The current files do not contain a clean shares-outstanding or market-cap series, so a textbook `log(ME)` control is still unavailable.
