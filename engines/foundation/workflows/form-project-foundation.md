# Workflow: Form Project Foundation

**Workflow ID:** `form_project_foundation`

## Role contract

- executing_role: `roles/executor/ROLE.md`
- consuming_role: `roles/control-director/ROLE.md`
- required_skills:
  - `engines/foundation/skills/develop-project-seed/SKILL.md`
  - `engines/foundation/skills/define-project-outcome/SKILL.md`
  - `engines/foundation/skills/classify-consequential-unknowns/SKILL.md`
- optional_skills:
  - `engines/foundation/skills/design-discovery/SKILL.md` only when exploration materially improves the seed, outcome, or unknown map.

Neither role acquires Owner/K0 authority or Canon authority by executing or consuming this workflow.

## Entry

- Liaison has selected `ROUTE` because governed project formation is intended;
- exact Owner material or exact supplied project material is preserved with provenance;
- exact assignment and relevant state identity are known;
- destination assignment is admissible under the generic Resolver execution chain.

## Required durable outputs

The assignment must declare all three Foundation outputs through its existing `required_durable_outputs` contract and bind one exact `durable_system_of_record_ref`:

- `PROJECT_SEED`;
- `PROJECT_OUTCOME`;
- `CONSEQUENTIAL_UNKNOWN_MAP`.

The Executor reports exact `durable_output_refs` for the assignment-declared output identities after successful materialization. Reference presence alone is not completion evidence. Control must perform independent readback from the declared durable system of record under the existing generic durable-output/readback contract.

`FOUNDATION_READY_FOR_OWNER_GATE` is available only when all three required outputs have been materialized, exact output refs cover the assignment declaration, and the required independent readback has succeeded. A local/session copy cannot substitute for durable readback.

Durability preserves working-state continuity. It does not create Owner/K0 authority and it does not create Canon authority.

## Procedure

1. Consume only the bounded Liaison routing frame, exact Owner material, and relevant admitted project state.
2. Use `develop-project-seed` to produce the smallest coherent working interpretation while preserving Owner statements, model interpretations, proposals, and unresolved material questions.
3. Use `define-project-outcome` to identify what should exist at project completion without assuming software or Production.
4. Load optional `design-discovery` only when bounded exploration materially improves the seed, outcome, or unknown classification.
5. Use `classify-consequential-unknowns` to classify only unresolved items that matter downstream; classification is not resolution or dispatch.
6. Reconcile the three working artifacts for contradictions, provenance loss, accidental authority promotion, and material gaps.
7. If one material ambiguity prevents a coherent working foundation, return the smallest bounded clarification/blocker needed. Zero clarification questions is valid when supplied material is already sufficient.
8. Materialize all three assignment-declared durable outputs and return exact `durable_output_refs`.
9. Require the existing generic independent readback before treating durable completion as proven.
10. Only then return `FOUNDATION_READY_FOR_OWNER_GATE`.
11. STOP. Do not execute the future Owner Foundation Gate, Canon acceptance or mutation, Research dispatch, or Production from this workflow.

## Cognitive boundary

This workflow coordinates cognitive skills; it does not replace native model reasoning with a form. Internal iteration among seed, outcome, unknown classification, and optional discovery is allowed when it improves coherence.

No fixed question count exists. Do not ask for information merely because a schema has an optional field. Working uncertainty may remain explicit.

## Stop

Stop with a bounded blocker when required Owner material/provenance, assignment identity, destination executability, durable materialization, output-ref coverage, or independent readback is unavailable.

Stop successfully at `FOUNDATION_READY_FOR_OWNER_GATE` only after the durable completion boundary above is satisfied.

The status is not an Owner decision, does not execute the Owner Foundation Gate, does not perform Canon acceptance, does not dispatch Research, and does not authorize Production.
