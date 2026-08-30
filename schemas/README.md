# Artifact Schemas

These are lightweight standalone JSON Schemas for the first role-native control artifacts. They intentionally avoid a framework/runtime dependency.

Every schema includes the common envelope: `artifact_type`, `artifact_id`, `produced_by_role`, `assignment_id`, `input_state_ref`, `status`, `provenance`, and `related_artifacts`. Role-specific fields are added by each artifact type.
