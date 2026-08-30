---
name: freeze-canon
description: Freeze an explicitly authorized Canon scope at Foundation 0.x, Canon 1.0 or Canon 2.0 after maturity-appropriate validation gates pass.
---

Adapted from source `canon-freeze`, with maturity-specific Project Resolver semantics.

## Procedure

1. Lock exact candidate, target scope, validation result and requested maturity.
2. Reject stale/mismatched validation or any blocking finding.
3. Require explicit authority for the state transition.
4. For `CANON_FOUNDATION_0_X`, allow explicit assumptions/unknowns/contradictions that are recorded as unresolved and do not misrepresent research completion.
5. For `CANON_1_0`, require current Research reconciliation and explicit disposition of blockers inside production-authorizing scope.
6. For `CANON_2_0`, require current final production-era reconciliation.
7. Freeze only the declared scope; partial freeze is valid.
8. Emit `CANON_FREEZE_RECORD` with exact state ref, scope, authority, unresolved-but-permitted items and downstream authorization.

## Verdict

`FROZEN`, `READY_BUT_NOT_AUTHORIZED`, or `BLOCKED`.

Freeze means stability, not maximal detail.