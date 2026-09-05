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

The reconciliation disposition contract is exactly:
`ACCEPT_ADD_PROPOSAL`, `REJECT_PROPOSAL`, `RETAIN`, `SUPERSEDE_PROPOSAL`,
`CLOSE_UNKNOWN_PROPOSAL`, `RETAIN_UNKNOWN`, `PRESERVE_AMBIGUITY`,
`REGISTER_CONTRADICTION`, `REQUIRE_OWNER_DECISION`, `DEFER_OUT_OF_SCOPE`.
Producer, schema and template surfaces must use this same vocabulary.

## Procedure

1. Lock exact current Canon and upstream Research identities.
2. Run `reconcile-research-into-canon` and emit envelope-compatible reconciliation/change-proposal artifacts using only the declared disposition contract.
3. Do not apply an accepted Canon mutation without exact governing mutation authority.
4. Apply only authorized Canon changes with provenance and prior-state refs; proposal/retain/defer dispositions do not grant mutation authority.
5. Run mandatory `validate-canon` on any resulting exact candidate.
6. Route to `validate_and_freeze_canon` only when freeze authority and maturity prerequisites are separately present.

## Stop

Stop on protected Owner conflict, equal-authority conflict, unsupported stronger claim, missing mutation authority for an accepted change, or unresolved mandatory upstream evidence. Preserve UNKNOWN/AMBIGUITY/CONTRADICTION rather than manufacturing closure.
