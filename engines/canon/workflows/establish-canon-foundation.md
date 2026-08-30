# Workflow: Establish Canon Foundation

**Workflow ID:** `establish_canon_foundation`

## Entry

- exact assignment and project/state identity are known;
- Owner/K0 intent or another authorized upstream source is available;
- the requested output is Canon Foundation, not Production Foundation.

## Roles

Use existing `roles/executor/ROLE.md`. `roles/control-director/ROLE.md` may route or consume the result. The workflow does not acquire Owner authority.

## Procedure

1. Assemble only the relevant state slice and explicit Owner/authorized inputs.
2. Run `establish-canon-foundation` to create/update a project-neutral 0.x carrier without inventing truth.
3. Use the bounded registration skills as needed: facts, assumptions, unknowns, ambiguity, contradictions.
4. Preserve provenance and classify inference as proposed rather than accepted.
5. Run `validate-canon` against the exact candidate.
6. If the assignment explicitly authorizes a 0.x freeze and validation has no blocker, run `freeze-canon` with maturity `CANON_FOUNDATION_0_X`.
7. Emit durable `CANON_FOUNDATION` and, when frozen, `CANON_FREEZE_RECORD` artifacts.

## Exit

The Foundation states what is protected/accepted/assumed/unknown/ambiguous/contradictory and is usable as a stable Research-entry baseline. It does not claim Research completion or Production Foundation readiness.

## Stop

Stop for conflicting protected Owner intent, missing authority for an acceptance/freeze transition, or a requested mutation that would silently replace an existing frozen Canon scope.