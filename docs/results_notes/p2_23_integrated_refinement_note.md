# P2.23 integrated refinement pass

This pass combines three changes at once:

1. **LCFS edge re-review**
   The edge sample is no longer treated as homogeneous for LCFS.
   Boundary refiners and credit-linked names are kept with higher LCFS edge weights, while hydrogen, additive, and indirect transition names are heavily downweighted or excluded.

2. **Policy-specific weight shrinkage**
   The issuer-level integration layer is converted from coarse primary/secondary weights into policy-specific shrunken weights:
   - primary contribution shrunk from 1.0 to 0.90
   - secondary contribution shrunk from 0.50 to 0.35
   - edge-sample inclusion becomes policy-specific rather than one-size-fits-all

3. **Hardened policy-side daily intensity**
   The daily mechanism series now use document-type-specific pulse and decay rules instead of one generic carry-forward logic.
   Statutes and regulations remain persistent, while notices, revisions, and guidance decay faster.
