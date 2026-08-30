---
name: validate-canon
description: Validate exact Canon structure, stable identity, authority/provenance, contradiction and maturity readiness without granting acceptance or independent verification authority.
---

Adapted from source `canon-validator`, `canon-acceptance-tests`, and `contradiction-audit`.

## Checks

1. Exact artifact identity/version/scope is known.
2. Schema/required fields are structurally valid where a schema applies.
3. Stable IDs are unique; dependencies resolve or are explicitly external.
4. Fact/assumption/unknown/ambiguity/contradiction types are not blurred.
5. Accepted/frozen claims carry explicit authority/provenance.
6. Equal accepted conflicts are blocking unless explicitly scoped/intentional.
7. Intended ambiguity has explicit preservation law.
8. Maturity gate is coherent:
   - 0.x may retain explicit unknowns/assumptions;
   - 1.0 requires current Research reconciliation and disposition of production-scope blockers;
   - 2.0 requires current final reconciliation.
9. Freeze metadata matches actual frozen scope.

## Verdict

`PASS`, `PASS_WITH_FINDINGS`, or `BLOCKED`.

A PASS is internal Canon validation only. It does not itself grant Owner acceptance, freeze authority, or independent Verification Engine proof.