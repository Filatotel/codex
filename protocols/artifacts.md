# Common Artifact Protocol

The legacy software sequence `PLAN → IMPLEMENTATION → QA → REVIEW → MERGE` is not a universal system law. Engines may define such a workflow locally.

## Ownership

A **PRIMARY ARTIFACT** is produced by the role that created the underlying knowledge/work. A **DERIVED ARTIFACT** is computed or summarized from primary artifacts and must retain provenance to them.

There is no universal Artifact Agent. Artifact production is role-native.

## Required common artifact types

- `CAPABILITY_PROFILE` — freshness-bounded evidence of concrete execution surfaces available to one exact destination/runtime instance; it carries no authority by itself.
- `COMPILED_ASSIGNMENT` — normalized authority/movability, context-fact authority, responsibility, evidence, envelope, mandatory-action, and capability semantics authorized by deterministic Control-layer compilation.
- `ASSIGNMENT_ADMISSIBILITY` — pre-assignment control proof comparing mandatory required capabilities/evidence paths with one exact destination capability profile.
- `ASSIGNMENT` — bounded instruction for current work; executable only when its destination-bound execution contract cites an `ADMISSIBLE` proof and contains no unsatisfied required capability.
- `EXECUTOR_RESULT` — what the Executor actually did, resulting state, evidence refs, limitations/deferred findings.
- `VERIFICATION_RESULT` — independent claim-by-claim verification of an exact result/candidate.
- `DIRECTOR_DECISION` — admissible next transition selected from current state plus relevant results.
- `OWNER_DECISION_RECORD` — durable materialization of an Owner/K0 choice.
- `STATE_MUTATION_PROPOSAL` — requested governed state change before authority acceptance.
- `HANDOFF` — bounded continuation transfer between role instances.

## Identity and provenance

Every artifact has a stable `artifact_id`, `artifact_type`, `produced_by_role`, `assignment_id` where applicable (nullable for pre-assignment artifacts), `input_state_ref`, `status`, `provenance/created_from`, and `related_artifacts`.

Derived artifacts must not erase source identity. A summary cannot silently replace a primary result when the downstream decision requires the primary result.

`CAPABILITY_PROFILE` must identify the exact destination/runtime and freshness boundary. `ASSIGNMENT_ADMISSIBILITY` must bind the assignment draft, exact compiled assignment, destination, and exact capability profile used in the subset decision. An `ASSIGNMENT` must preserve those refs in its execution contract.

## Pre-assignment executability separation

`ASSIGNMENT_ADMISSIBILITY != VERIFICATION_RESULT`.

Admissibility establishes only that the destination can execute/prove the mandatory assignment requirements at dispatch time. It does not establish that the work succeeded, that the candidate is correct, or that acceptance is satisfied.

Known missing capability before dispatch yields `ASSIGNMENT_NOT_ADMISSIBLE` and no executable assignment. Loss of a previously proven capability after dispatch is runtime drift and may yield `BLOCKED_RUNTIME_DRIFT` from the active role.

## Execution and verification separation

`EXECUTOR_RESULT != VERIFICATION_RESULT`.

The Executor owns truthful reporting of performed work; the Verifier owns independent assessment of claims. A Verifier report must not rewrite or replace the Executor result. Where verification is required, Control Director receives **both** artifacts.

## Artifact versus evidence

Artifacts can contain evidence references, but artifact existence is not proof. Evidence must be evaluated against the exact claim, state, method, and trust boundary described by the evidence contract. A capability profile is evidence about the runtime surface only; it is neither authorization nor proof of task completion.
# Executability evidence and route trust boundary

`CAPABILITY_EVIDENCE` is structurally valid only when its common artifact identity, runtime, unique non-empty proven capabilities, observation/validity timestamps, observation method, provenance, and created-from lineage are complete. Structural validity is distinct from authoritative resolution: an embedded object cannot resolve itself. `EXECUTION_ROUTE` is the durable assignment-draft-bound proof joining candidate delivery, execution/verification, and durable evidence/control through capability-proven segments and directional handoffs. Cross-surface edges prove export and receive sides independently; same-surface edges prove exact runtime equivalence and internal transfer. Assignment and admissibility artifacts cite its exact identity, the execution segment equals their admitted execution identity, and the structured final-result reference resolves to the durable segment whose destination equals `ASSIGNMENT.result_to`.
