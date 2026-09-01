# Artifact Schemas

These are lightweight standalone JSON Schemas for role-native and shared control artifacts. They intentionally avoid a framework/runtime dependency.

Every schema includes the common envelope: `artifact_type`, `artifact_id`, `produced_by_role`, `assignment_id`, `input_state_ref`, `status`, `provenance`, and `related_artifacts`. Pre-assignment artifacts may use `assignment_id: null`. Role/control-specific fields are added by each artifact type.

Destination executability uses three linked artifacts:

1. `CAPABILITY_PROFILE` — evidence-bearing, freshness-bounded capabilities for one exact destination/runtime;
2. `ASSIGNMENT_ADMISSIBILITY` — complete mandatory-action accounting plus deterministic required-vs-available comparison;
3. `ASSIGNMENT.execution_contract` — only materialized as executable work when the cited admissibility proof is `ADMISSIBLE` and no required capability is unsatisfied.

The schemas constrain shape; `tools/executability.py` validates cross-field and cross-artifact consistency such as capability evidence coverage, mandatory-action closure, exact profile binding, and the subset relation.
# Executability parity matrix

| Artifact | Required deterministic/schema constraints |
|---|---|
| `CAPABILITY_PROFILE` | exact destination/runtime, unique capability sets, strict freshness timestamps, evidence references and optional non-authoritative transport copies |
| `CAPABILITY_EVIDENCE` | exact artifact/runtime/capabilities, producer and state identity, observation/validity timestamps, observation method, provenance, related artifacts, created-from lineage; governed resolution is a reference-validator semantic gate |
| `ASSIGNMENT_ADMISSIBILITY` | exact draft/profile/runtime and `route_ref`, mandatory-action union, evidence-path equality, empty missing set iff admissible |
| `EXECUTION_ROUTE` | exact draft/structured final result identity, exactly one of each mandatory role, directional source/target handoff requirements or same-surface internal transfer, and unique capability requirements; segment-id uniqueness, ordered-edge topology, profile resolution, cross-artifact execution identity, and subset/equivalence checks are explicit reference-only semantic gates |
| `ASSIGNMENT` | complete common/assignment fields, proven execution contract, exact draft/profile/admissibility/route bindings, empty missing set, and `result_to` equality with the route final destination |

`tests/test_executability_parity.py` executes a bounded JSON-Schema keyword subset against committed fixtures because this repository has no JSON-Schema runtime dependency. It compares schema and reference acceptance for their shared structural surface and explicitly labels cross-artifact/topological rules that are intentionally reference-only rather than pretending standalone schemas can express them.
