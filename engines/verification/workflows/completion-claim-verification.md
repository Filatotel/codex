# Verification Workflow — Completion Claim

**Entry:** exact assignment, exact `EXECUTOR_RESULT`, explicit claims/acceptance targets, and destination executability proof covering every mandatory verification/evidence action required from the selected verifier instance.

1. Load exact assignment, exact `EXECUTOR_RESULT`, Control Verifier role, and the verifier destination capability/admissibility refs.
2. Extract asserted claims and required acceptance criteria **before assignment** when deriving verifier requirements; map each mandatory claim to its exact evidence path and concrete execution capabilities.
3. Require `REQUIRED_CAPABILITIES ⊆ AVAILABLE_CAPABILITIES` for the verifier destination under `contracts/EXECUTABILITY_CONTRACT.md`. If a mandatory evidence path is known unavailable, return `ASSIGNMENT_NOT_ADMISSIBLE`; do not intentionally launch verification to obtain a predictable `BLOCKED`.
4. Bind candidate/evidence identity using shared exact-state rules. Distinguish remote repository state, local worktree state, runtime/deployed state, browser state, database state, and other trust boundaries.
5. Use `skills/proof-loop-verification` plus shared evidence/authority rules.
6. Inspect direct state/evidence where required; do not accept Executor narrative as proof and do not silently substitute weaker evidence because the destination lacks the stronger surface.
7. If a capability that was proven at assignment time disappears, mark affected claims `NOT_PROVEN`/blocked with `BLOCKED_RUNTIME_DRIFT` evidence.
8. Emit `VERIFICATION_RESULT` with `CONFIRMED`, `QUALIFIED`, or `NOT_PROVEN` per claim and separate additional findings.
9. Hand the result to Control Director **alongside the unchanged Executor Result**.

No repair or scope expansion occurs inside this workflow. Verification blockage remains a truthful runtime outcome only for unavailable/stale evidence that was not already known to make the assignment inadmissible before dispatch.
