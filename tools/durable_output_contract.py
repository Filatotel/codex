"""A1 structural contract for assignment-required durable output references.

This module proves reference coverage only. It does not resolve, read, or otherwise
establish durability of any referenced artifact.
"""
from __future__ import annotations

from collections.abc import Mapping


REQUIRED_DURABLE_OUTPUTS_FIELD = "required_durable_outputs"
DURABLE_OUTPUT_REFS_FIELD = "durable_output_refs"
_BINDING_FIELDS = {"output_id", "artifact_ref"}


def _non_blank(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_assignment_durable_outputs(assignment: Mapping[str, object]) -> list[str]:
    """Validate assignment-local identities for required durable outputs."""
    errors: list[str] = []
    value = assignment.get(REQUIRED_DURABLE_OUTPUTS_FIELD, [])
    if not isinstance(value, list):
        return ["assignment.required_durable_outputs must be a list"]

    seen: set[str] = set()
    for index, output_id in enumerate(value):
        if not _non_blank(output_id):
            errors.append(
                f"assignment.required_durable_outputs[{index}] must be a non-blank string"
            )
            continue
        assert isinstance(output_id, str)
        if output_id in seen:
            errors.append(f"duplicate required durable output id: {output_id}")
        else:
            seen.add(output_id)
    return errors


def validate_executor_durable_output_refs(
    result: Mapping[str, object],
    assignment: Mapping[str, object],
) -> list[str]:
    """Validate opaque durable-ref bindings against one exact assignment.

    COMPLETE requires one binding for every declared required durable output.
    Other terminal Executor statuses may truthfully carry only the subset that
    exists. Artifact-reference presence is intentionally not readback proof.
    """
    errors = validate_assignment_durable_outputs(assignment)
    if errors:
        return errors

    declared_value = assignment.get(REQUIRED_DURABLE_OUTPUTS_FIELD, [])
    declared = set(declared_value) if isinstance(declared_value, list) else set()

    bindings = result.get(DURABLE_OUTPUT_REFS_FIELD, [])
    if not isinstance(bindings, list):
        return errors + ["executor_result.durable_output_refs must be a list"]

    bound: set[str] = set()
    for index, binding in enumerate(bindings):
        prefix = f"executor_result.durable_output_refs[{index}]"
        if not isinstance(binding, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        if set(binding) != _BINDING_FIELDS:
            errors.append(f"{prefix} must contain exactly output_id and artifact_ref")
            continue

        output_id = binding.get("output_id")
        artifact_ref = binding.get("artifact_ref")
        if not _non_blank(output_id):
            errors.append(f"{prefix}.output_id must be a non-blank string")
            continue
        if not _non_blank(artifact_ref):
            errors.append(f"{prefix}.artifact_ref must be a non-blank string")

        assert isinstance(output_id, str)
        if output_id not in declared:
            errors.append(f"{prefix}.output_id is not declared by the assignment: {output_id}")
        if output_id in bound:
            errors.append(f"duplicate durable output binding id: {output_id}")
        else:
            bound.add(output_id)

    if result.get("status") == "COMPLETE":
        missing = sorted(declared - bound)
        if missing:
            errors.append(f"COMPLETE executor result is missing durable output refs: {missing}")
    return errors
