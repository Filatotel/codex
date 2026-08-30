# Workflow: Reconcile Research Into Canon

**Workflow ID:** `reconcile_research_into_canon`

## Entry

- exact current `CANON_FOUNDATION` or `CANON_STATE` ref;
- Research has produced explicit evidence/findings with provenance;
- reconciliation scope and Canon authority boundary are known.

## Invariant

`RESEARCH → EVIDENCE/FINDINGS → CANON RECONCILIATION → ACCEPTED CANON`.

A Research finding is never accepted Canon merely because it is well supported.

## Procedure

1. Lock exact current Canon and Research release identities.
2. Run `reconcile-research-into-canon` to compare findings against facts, assumptions, unknowns, ambiguities, contradictions, protected values and prior decisions.
3. Emit a `CANON_RECONCILIATION_RESULT` with explicit dispositions and one or more `CANON_CHANGE_PROPOSAL` records where mutation is warranted.
4. Do not mutate accepted Canon unless the active assignment carries the governing Canon authority or an explicit authority decision is supplied.
5. Apply only authorized dispositions with provenance and prior-state refs.
6. Run `validate-canon` on the resulting exact candidate.
7. When the scope is ready and freeze authority exists, route to `validate_and_freeze_canon` for Canon 1.0.

## Stop

Stop on equal-authority conflict, protected Owner-intent conflict, unsupported stronger claim, or missing decision authority. Preserve `UNKNOWN`, `CONTRADICTION`, or `BLOCKED` rather than manufacturing closure.