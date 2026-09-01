# Artifact Schemas

These are lightweight standalone JSON Schemas for role-native and shared control artifacts. They intentionally avoid a framework/runtime dependency.

Every schema includes the common envelope: `artifact_type`, `artifact_id`, `produced_by_role`, `assignment_id`, `input_state_ref`, `status`, `provenance`, and `related_artifacts`. Pre-assignment artifacts may use `assignment_id: null`. Role/control-specific fields are added by each artifact type.

Destination executability uses three linked artifacts:

1. `CAPABILITY_PROFILE` — evidence-bearing, freshness-bounded capabilities for one exact destination/runtime;
2. `ASSIGNMENT_ADMISSIBILITY` — complete mandatory-action accounting plus deterministic required-vs-available comparison;
3. `ASSIGNMENT.execution_contract` — only materialized as executable work when the cited admissibility proof is `ADMISSIBLE` and no required capability is unsatisfied.

The schemas constrain shape; `tools/executability.py` validates cross-field and cross-artifact consistency such as capability evidence coverage, mandatory-action closure, exact profile binding, and the subset relation.
