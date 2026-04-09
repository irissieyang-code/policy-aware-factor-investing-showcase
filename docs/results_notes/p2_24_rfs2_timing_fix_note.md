# P2.24 RFS2 timing fix

This step resolves the specific RFS2 timing problem identified in P2.23.

## What was wrong before

In the earlier hardened policy file, all four RFS2 mechanism intensities were zero inside the
2021-01-04 event window. That meant the RFS2 mechanism regressors were mechanically shut off.

## What changed

The RFS2 policy-side timing layer has been rebuilt with event-aligned anchors:

- `RFS2_OBLIG` anchored to 2020-12-26
- `RFS2_RIN` anchored to 2021-01-01
- `RFS2_RESET` anchored to 2021-01-04

These are explicit event-aligned timing overrides for the Stage 1/2 event design, not claims
that the official publication dates were exactly those dates.

## Why this is a valid fix

The issue being solved here is not historical chronology in the abstract.
The issue is that the model's policy-time layer had been misaligned with the event window used
in the project. The new timing layer restores nonzero mechanism intensity inside that window,
which makes the RFS2 regression mechanically estimable again.
