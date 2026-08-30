# Workflow: Final Canon Reconciliation

**Workflow ID:** `final_canon_reconciliation`

## Entry

Production is complete enough for final Canon reconciliation and all accepted production-time Canon changes/decisions are available as durable artifacts.

## Procedure

1. Lock Canon 1.x state and exact production-era change records.
2. Reconcile accepted A/B/C/D outcomes, unresolved proposals, explicit final decisions, preserved ambiguities and remaining contradictions.
3. Reject implementation-only facts that never received Canon authority.
4. Produce a `CANON_RECONCILIATION_RESULT` and Canon 2.0 candidate.
5. Run `validate-canon`.
6. With explicit final Canon authority, run `freeze-canon` as `CANON_2_0` and emit the freeze record.

## Boundary

This workflow closes Canon truth state. It does not grant generic product/release verification authority.

## Stop

Stop if a late change requires an unresolved core/Owner decision or if the candidate would hide a known contradiction/unknown rather than dispose it explicitly.