# Verification Workflow — Completion Claim

1. Load exact assignment, exact `EXECUTOR_RESULT`, and Control Verifier role.
2. Bind candidate/evidence identity using shared exact-state rules.
3. Extract asserted claims and required acceptance criteria.
4. Use `skills/proof-loop-verification` plus shared evidence/authority rules.
5. Inspect direct state/evidence where required; do not accept Executor narrative as proof.
6. Emit `VERIFICATION_RESULT` with `CONFIRMED`, `QUALIFIED`, or `NOT_PROVEN` per claim and separate additional findings.
7. Hand the result to Control Director **alongside the unchanged Executor Result**.

No repair or scope expansion occurs inside this workflow.
