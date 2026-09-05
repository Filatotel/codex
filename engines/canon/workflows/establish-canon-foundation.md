# Workflow: Establish Canon Foundation

**Workflow ID:** `establish_canon_foundation`

## Role contract

- executing_role: `roles/executor/ROLE.md`
- consuming_role: `roles/control-director/ROLE.md`
- required_skills:
  - `engines/canon/skills/establish-canon-foundation/SKILL.md`
  - `engines/canon/skills/validate-canon/SKILL.md`
- optional_skills: registration skills and `freeze-canon` only when the exact assignment requires them.

Neither role acquires Owner/K0 authority by executing or consuming this workflow.

## Entry

- exact assignment and state identity are known;
- explicit Owner/K0 intent or another authorized Foundation input exists;
- requested output is Canon Foundation, not Production Foundation;
- destination assignment is admissible under the generic Resolver execution chain.

## Procedure

1. Assemble only the relevant state slice and explicit authorized inputs.
2. Run `establish-canon-foundation` to create/update a project-neutral 0.x carrier without inventing truth.
3. Use bounded registration skills only when the assignment requires their semantic operation.
4. Preserve provenance and classify inference as proposed rather than accepted.
5. Run mandatory `validate-canon` on the exact candidate.
6. If the assignment explicitly authorizes a 0.x freeze, load and run `freeze-canon`; otherwise do not infer freeze authority.
7. Emit durable envelope-compatible `CANON_FOUNDATION` and any explicitly authorized `CANON_FREEZE_RECORD`.

## Stop

Stop for conflicting protected Owner intent, missing authority for acceptance/freeze, unresolved mandatory dependency, or attempted silent replacement of frozen Canon.
