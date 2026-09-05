# Workflow: Reconcile Research Into Canon

**Workflow ID:** `reconcile_research_into_canon`

## Role contract

- executing_role: `roles/executor/ROLE.md`
- consuming_role: `roles/control-director/ROLE.md`
- required_skills:
  - `engines/canon/skills/reconcile-research-into-canon/SKILL.md`
  - `engines/canon/skills/validate-canon/SKILL.md`
- optional_skills: bounded registration skills and `freeze-canon` only when authorized.

## Entry

- exact current `CANON_FOUNDATION` or `CANON_STATE` ref;
- exact Research release/findings with provenance;
- reconciliation scope and authority boundary;
- destination assignment is admissible.

## Invariant

`RESEARCH → EVIDENCE/FINDINGS → CANON RECONCILIATION → ACCEPTED CANON`.

A Research finding is never accepted Canon merely because Research supports it.

## Procedure

1. Lock exact current Canon and upstream Research identities.
2. Run `reconcile-research-into-canon` and emit envelope-compatible reconciliation/change-proposal artifacts.
3. Do not apply an accepted Canon mutation without exact governing mutation authority.
4. Apply only authorized dispositions with provenance and prior-state refs.
5. Run mandatory `validate-canon` on any resulting exact candidate.
6. Route to `validate_and_freeze_canon` only when freeze authority and maturity prerequisites are separately present.

## Stop

Stop on protected Owner conflict, equal-authority conflict, unsupported stronger claim, missing mutation authority, or unresolved mandatory upstream evidence. Preserve UNKNOWN/AMBIGUITY/CONTRADICTION rather than manufacturing closure.
