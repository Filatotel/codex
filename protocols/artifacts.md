# Common Artifact Protocol

The legacy software sequence `PLAN → IMPLEMENTATION → QA → REVIEW → MERGE` is not a universal system law. Engines may define such a workflow locally.

## Ownership

A **PRIMARY ARTIFACT** is produced by the role that created the underlying knowledge/work. A **DERIVED ARTIFACT** is computed or summarized from primary artifacts and must retain provenance to them.

There is no universal Artifact Agent. Artifact production is role-native.

## Required common artifact types

- `ASSIGNMENT` — bounded instruction for current work.
- `EXECUTOR_RESULT` — what the Executor actually did, resulting state, evidence refs, limitations/deferred findings.
- `VERIFICATION_RESULT` — independent claim-by-claim verification of an exact result/candidate.
- `DIRECTOR_DECISION` — admissible next transition selected from current state plus relevant results.
- `OWNER_DECISION_RECORD` — durable materialization of an Owner/K0 choice.
- `STATE_MUTATION_PROPOSAL` — requested governed state change before authority acceptance.
- `HANDOFF` — bounded continuation transfer between role instances.

## Identity and provenance

Every artifact has a stable `artifact_id`, `artifact_type`, `produced_by_role`, `assignment_id` where applicable, `input_state_ref`, `status`, `provenance/created_from`, and `related_artifacts`.

Derived artifacts must not erase source identity. A summary cannot silently replace a primary result when the downstream decision requires the primary result.

## Execution and verification separation

`EXECUTOR_RESULT != VERIFICATION_RESULT`.

The Executor owns truthful reporting of performed work; the Verifier owns independent assessment of claims. A Verifier report must not rewrite or replace the Executor result. Where verification is required, Control Director receives **both** artifacts.

## Artifact versus evidence

Artifacts can contain evidence references, but artifact existence is not proof. Evidence must be evaluated against the exact claim, state, method, and trust boundary described by the evidence contract.
