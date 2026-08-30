# Workflow: Validate and Freeze Canon

**Workflow ID:** `validate_and_freeze_canon`

## Procedure

1. Lock exact candidate identity/version and target freeze scope.
2. Run `validate-canon` for deterministic structure plus semantic/authority readiness.
3. Treat internal validation as necessary but not as Owner acceptance or independent Verification Engine proof.
4. If validation is blocking, emit findings and stop without mutation.
5. If freeze authority is absent, return `READY_BUT_NOT_AUTHORIZED`.
6. Run `freeze-canon` with explicit maturity:
   - `CANON_FOUNDATION_0_X`: explicit unknowns/assumptions may remain and are frozen as unresolved state;
   - `CANON_1_0`: Research reconciliation must be current and production-authorizing blockers resolved/disposed;
   - `CANON_2_0`: final production-era reconciliation must be current.
7. Emit `CANON_FREEZE_RECORD` with exact state ref, scope, authority ref, unresolved-but-permitted items and downstream entry authorization.

## Exit

A freeze is scoped stability, not maximal specification and not permission for silent later mutation.