#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone


def _normalize(values: Iterable[str]) -> list[str]:
    return sorted({value.strip() for value in values if isinstance(value, str) and value.strip()})


def _timestamp(value: object, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty ISO-8601 timestamp")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} must be an ISO-8601 timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field} must include a timezone")
        return None
    return parsed.astimezone(timezone.utc)


def evaluate_assignment_admissibility(
    required_capabilities: Iterable[str],
    available_capabilities: Iterable[str],
) -> dict[str, object]:
    """Return the deterministic subset result for one destination capability profile."""
    required = _normalize(required_capabilities)
    available = _normalize(available_capabilities)
    missing = sorted(set(required) - set(available))
    return {
        "status": "ADMISSIBLE" if not missing else "NOT_ADMISSIBLE",
        "required_capabilities": required,
        "available_capabilities": available,
        "unsatisfied_required_capabilities": missing,
    }


def validate_capability_profile(profile: Mapping[str, object]) -> list[str]:
    """Validate internal consistency and evidence coverage for a CAPABILITY_PROFILE."""
    errors: list[str] = []
    required_strings = ["artifact_id", "produced_by_role", "status", "destination_id", "runtime_identity"]
    if profile.get("artifact_type") != "CAPABILITY_PROFILE":
        errors.append("artifact_type must be CAPABILITY_PROFILE")
    if profile.get("status") != "CURRENT":
        errors.append("capability profile status must be CURRENT")
    for field in required_strings:
        if not isinstance(profile.get(field), str) or not str(profile[field]).strip():
            errors.append(f"{field} must be a non-empty string")
    for field in ["provenance", "related_artifacts", "limitations"]:
        value = profile.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append(f"{field} must be a list of strings")
    for field in ["assignment_id", "input_state_ref"]:
        value = profile.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{field} must be null or a non-empty string")

    boundary = profile.get("freshness_boundary")
    if not isinstance(boundary, Mapping):
        errors.append("freshness_boundary must be an object")
        observed_at = valid_until = None
    else:
        observed_at = _timestamp(boundary.get("observed_at"), "freshness_boundary.observed_at", errors)
        valid_until = _timestamp(boundary.get("valid_until"), "freshness_boundary.valid_until", errors)
        if observed_at and valid_until and observed_at > valid_until:
            errors.append("freshness_boundary observed_at must not be after valid_until")
        if observed_at and observed_at > datetime.now(timezone.utc):
            errors.append("capability profile freshness boundary starts in the future")
        if valid_until and valid_until <= datetime.now(timezone.utc):
            errors.append("capability profile freshness boundary is expired")

    available = profile.get("available_capabilities")
    unavailable = profile.get("unavailable_capabilities")
    evidence = profile.get("capability_evidence")

    if not isinstance(available, list) or not all(isinstance(v, str) and v.strip() for v in available):
        return ["available_capabilities must be a list of non-empty strings"]
    if not isinstance(unavailable, list) or not all(isinstance(v, str) and v.strip() for v in unavailable):
        return ["unavailable_capabilities must be a list of non-empty strings"]
    if not isinstance(evidence, list):
        return ["capability_evidence must be a list"]

    normalized_available = _normalize(available)
    normalized_unavailable = _normalize(unavailable)
    overlap = sorted(set(normalized_available) & set(normalized_unavailable))
    if overlap:
        errors.append(f"capabilities cannot be both available and unavailable: {overlap}")

    runtime_identity = profile.get("runtime_identity")
    evidence_artifacts = profile.get("evidence_artifacts")
    if not isinstance(evidence_artifacts, list):
        errors.append("evidence_artifacts must be a list")
        evidence_artifacts = []
    evidence_by_id: dict[str, Mapping[str, object]] = {}
    for index, artifact in enumerate(evidence_artifacts):
        if not isinstance(artifact, Mapping):
            errors.append(f"evidence_artifacts[{index}] must be an object")
            continue
        artifact_id = artifact.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id.strip():
            errors.append(f"evidence_artifacts[{index}].artifact_id must be a non-empty string")
            continue
        if artifact_id in evidence_by_id:
            errors.append(f"duplicate evidence artifact id: {artifact_id}")
        evidence_by_id[artifact_id] = artifact

    evidence_caps: list[str] = []
    for index, item in enumerate(evidence):
        if not isinstance(item, Mapping):
            errors.append(f"capability_evidence[{index}] must be an object")
            continue
        capability = item.get("capability")
        evidence_ref = item.get("evidence_ref")
        if not isinstance(capability, str) or not capability.strip():
            errors.append(f"capability_evidence[{index}].capability must be a non-empty string")
            continue
        if not isinstance(evidence_ref, str) or not evidence_ref.strip():
            errors.append(f"capability_evidence[{index}].evidence_ref must be a non-empty string")
            continue
        artifact = evidence_by_id.get(evidence_ref)
        if artifact is None:
            errors.append(f"capability_evidence[{index}].evidence_ref is unresolved: {evidence_ref!r}")
            continue
        if artifact.get("artifact_type") != "CAPABILITY_EVIDENCE":
            errors.append(f"evidence artifact {evidence_ref!r} has invalid artifact_type")
        if artifact.get("status") != "RESOLVED":
            errors.append(f"evidence artifact {evidence_ref!r} is not RESOLVED")
        if artifact.get("runtime_identity") != runtime_identity:
            errors.append(f"evidence artifact {evidence_ref!r} runtime_identity mismatch")
        capabilities = artifact.get("capabilities")
        if not isinstance(capabilities, list) or capability.strip() not in _normalize(capabilities):
            errors.append(f"evidence artifact {evidence_ref!r} does not prove {capability.strip()!r}")
        evidence_observed = _timestamp(
            artifact.get("observed_at"), f"evidence artifact {evidence_ref!r}.observed_at", errors
        )
        evidence_valid = _timestamp(
            artifact.get("valid_until"), f"evidence artifact {evidence_ref!r}.valid_until", errors
        )
        if evidence_valid and evidence_valid <= datetime.now(timezone.utc):
            errors.append(f"evidence artifact {evidence_ref!r} is expired")
        if evidence_observed and evidence_valid and evidence_observed > evidence_valid:
            errors.append(f"evidence artifact {evidence_ref!r} observed_at is after valid_until")
        if observed_at and evidence_observed and evidence_observed < observed_at:
            errors.append(f"evidence artifact {evidence_ref!r} predates the profile freshness boundary")
        if valid_until and evidence_valid and evidence_valid < valid_until:
            errors.append(f"evidence artifact {evidence_ref!r} expires before the profile")
        evidence_caps.append(capability.strip())

        related_artifacts = profile.get("related_artifacts")
        if isinstance(related_artifacts, list) and evidence_ref not in related_artifacts:
            errors.append(f"evidence artifact {evidence_ref!r} is absent from related_artifacts")

    missing_evidence = sorted(set(normalized_available) - set(evidence_caps))
    if missing_evidence:
        errors.append(f"available capabilities missing evidence: {missing_evidence}")

    undeclared_evidence = sorted(set(evidence_caps) - set(normalized_available))
    if undeclared_evidence:
        errors.append(f"capability evidence references non-available capabilities: {undeclared_evidence}")

    return errors


def validate_admissibility_record(record: Mapping[str, object]) -> list[str]:
    """Validate subset result and complete mandatory-action capability accounting."""
    errors: list[str] = []
    required = record.get("required_capabilities")
    available = record.get("available_capabilities")
    missing = record.get("unsatisfied_required_capabilities")
    actions = record.get("mandatory_actions")
    evidence_paths = record.get("mandatory_evidence_paths")
    status = record.get("status")

    if record.get("artifact_type") != "ASSIGNMENT_ADMISSIBILITY":
        errors.append("artifact_type must be ASSIGNMENT_ADMISSIBILITY")
    for field in ["artifact_id", "produced_by_role", "assignment_draft_id", "destination_id", "runtime_identity", "capability_profile_ref", "execution_mode"]:
        if not isinstance(record.get(field), str) or not str(record[field]).strip():
            errors.append(f"{field} must be a non-empty string")
    for field in ["provenance", "related_artifacts"]:
        value = record.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append(f"{field} must be a list of strings")
    for field in ["assignment_id", "input_state_ref"]:
        value = record.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{field} must be null or a non-empty string")

    if not isinstance(required, list) or not all(isinstance(v, str) and v.strip() for v in required):
        return ["required_capabilities must be a list of non-empty strings"]
    if not isinstance(available, list) or not all(isinstance(v, str) and v.strip() for v in available):
        return ["available_capabilities must be a list of non-empty strings"]
    if not isinstance(missing, list) or not all(isinstance(v, str) and v.strip() for v in missing):
        return ["unsatisfied_required_capabilities must be a list of non-empty strings"]
    if not isinstance(actions, list) or not actions:
        return ["mandatory_actions must be a non-empty list"]
    if not isinstance(evidence_paths, list) or not all(isinstance(v, str) and v.strip() for v in evidence_paths):
        return ["mandatory_evidence_paths must be a list of non-empty strings"]

    derived_required: set[str] = set()
    derived_evidence_paths: set[str] = set()
    seen_action_ids: set[str] = set()
    for index, action in enumerate(actions):
        if not isinstance(action, Mapping):
            errors.append(f"mandatory_actions[{index}] must be an object")
            continue
        action_id = action.get("action_id")
        action_required = action.get("required_capabilities")
        evidence_path = action.get("evidence_path")
        if not isinstance(action_id, str) or not action_id.strip():
            errors.append(f"mandatory_actions[{index}].action_id must be a non-empty string")
        elif action_id in seen_action_ids:
            errors.append(f"duplicate mandatory action id: {action_id}")
        else:
            seen_action_ids.add(action_id)
        if not isinstance(action_required, list) or not all(
            isinstance(v, str) and v.strip() for v in action_required
        ):
            errors.append(f"mandatory_actions[{index}].required_capabilities must be a list of strings")
        else:
            derived_required.update(_normalize(action_required))
        if evidence_path is not None:
            if not isinstance(evidence_path, str) or not evidence_path.strip():
                errors.append(f"mandatory_actions[{index}].evidence_path must be null or a non-empty string")
            else:
                derived_evidence_paths.add(evidence_path.strip())

    normalized_required = _normalize(required)
    if sorted(derived_required) != normalized_required:
        errors.append(
            "required_capabilities do not equal union of mandatory action requirements: "
            f"derived {sorted(derived_required)}, declared {normalized_required}"
        )

    normalized_paths = _normalize(evidence_paths)
    if sorted(derived_evidence_paths) != normalized_paths:
        errors.append(
            "mandatory_evidence_paths do not equal action evidence paths: "
            f"derived {sorted(derived_evidence_paths)}, declared {normalized_paths}"
        )

    expected = evaluate_assignment_admissibility(required, available)
    if status != expected["status"]:
        errors.append(f"status drift: expected {expected['status']}, got {status}")
    if _normalize(missing) != expected["unsatisfied_required_capabilities"]:
        errors.append(
            "unsatisfied_required_capabilities drift: "
            f"expected {expected['unsatisfied_required_capabilities']}, got {_normalize(missing)}"
        )
    return errors


def validate_admissibility_against_profile(
    record: Mapping[str, object],
    profile: Mapping[str, object],
) -> list[str]:
    """Bind an admissibility record to the exact capability profile it cites."""
    errors = validate_capability_profile(profile) + validate_admissibility_record(record)

    profile_id = profile.get("artifact_id")
    record_profile_ref = record.get("capability_profile_ref")
    if not isinstance(profile_id, str) or not profile_id.strip():
        errors.append("capability profile artifact_id must be a non-empty string")
    elif record_profile_ref != profile_id:
        errors.append(
            f"capability_profile_ref mismatch: record cites {record_profile_ref!r}, profile is {profile_id!r}"
        )

    profile_destination = profile.get("destination_id")
    record_destination = record.get("destination_id")
    if profile_destination != record_destination:
        errors.append(
            f"destination mismatch: record {record_destination!r}, profile {profile_destination!r}"
        )

    if profile.get("runtime_identity") != record.get("runtime_identity"):
        errors.append(
            "runtime identity mismatch: "
            f"record {record.get('runtime_identity')!r}, profile {profile.get('runtime_identity')!r}"
        )

    profile_available = profile.get("available_capabilities")
    record_available = record.get("available_capabilities")
    if isinstance(profile_available, list) and isinstance(record_available, list):
        if _normalize(profile_available) != _normalize(record_available):
            errors.append(
                "available_capabilities do not match cited capability profile: "
                f"record {_normalize(record_available)}, profile {_normalize(profile_available)}"
            )

    return errors


def validate_assignment_execution_contract(
    assignment: Mapping[str, object],
    record: Mapping[str, object],
    profile: Mapping[str, object],
) -> list[str]:
    """Validate the complete executable-assignment proof chain."""
    errors = validate_admissibility_against_profile(record, profile)
    contract = assignment.get("execution_contract")
    if not isinstance(contract, Mapping):
        return errors + ["assignment.execution_contract must be an object"]

    if record.get("status") != "ADMISSIBLE":
        errors.append("executable assignment cites a non-ADMISSIBLE record")

    draft_id = record.get("assignment_draft_id")
    draft_ref = contract.get("assignment_draft_ref")
    if not isinstance(draft_ref, str) or not draft_ref.strip():
        errors.append("assignment execution contract requires a non-empty assignment_draft_ref")
    elif draft_ref != draft_id:
        errors.append(f"assignment_draft_ref mismatch: assignment {draft_ref!r}, proof {draft_id!r}")

    record_id = record.get("artifact_id")
    if contract.get("admissibility_ref") != record_id:
        errors.append(
            f"admissibility_ref mismatch: assignment {contract.get('admissibility_ref')!r}, record {record_id!r}"
        )

    profile_id = profile.get("artifact_id")
    if contract.get("capability_profile_ref") != profile_id:
        errors.append(
            "assignment capability_profile_ref mismatch: "
            f"assignment {contract.get('capability_profile_ref')!r}, profile {profile_id!r}"
        )

    destination = record.get("destination_id")
    if contract.get("destination_id") != destination:
        errors.append(
            f"assignment destination mismatch: assignment {contract.get('destination_id')!r}, proof {destination!r}"
        )

    runtime_identity = record.get("runtime_identity")
    if contract.get("runtime_identity") != runtime_identity:
        errors.append(
            "assignment runtime_identity mismatch: "
            f"assignment {contract.get('runtime_identity')!r}, proof {runtime_identity!r}"
        )

    if contract.get("proof_status") != "PROVEN":
        errors.append("assignment execution proof_status must be PROVEN")

    record_required = record.get("required_capabilities")
    assignment_required = contract.get("required_capabilities")
    if isinstance(record_required, list) and isinstance(assignment_required, list):
        if _normalize(record_required) != _normalize(assignment_required):
            errors.append(
                "assignment required_capabilities do not match admissibility record: "
                f"assignment {_normalize(assignment_required)}, proof {_normalize(record_required)}"
            )
    else:
        errors.append("assignment/proof required_capabilities must be lists")

    record_missing = record.get("unsatisfied_required_capabilities")
    assignment_missing = contract.get("unsatisfied_required_capabilities")
    if isinstance(record_missing, list) and isinstance(assignment_missing, list):
        if _normalize(record_missing) != _normalize(assignment_missing):
            errors.append(
                "assignment unsatisfied_required_capabilities do not match admissibility record"
            )
        if _normalize(assignment_missing):
            errors.append("executable assignment contains unsatisfied required capabilities")
    else:
        errors.append("assignment/proof unsatisfied_required_capabilities must be lists")

    record_paths = record.get("mandatory_evidence_paths")
    assignment_paths = contract.get("mandatory_evidence_paths")
    if isinstance(record_paths, list) and isinstance(assignment_paths, list):
        if _normalize(record_paths) != _normalize(assignment_paths):
            errors.append(
                "assignment mandatory_evidence_paths do not match admissibility record: "
                f"assignment {_normalize(assignment_paths)}, proof {_normalize(record_paths)}"
            )
    else:
        errors.append("assignment/proof mandatory_evidence_paths must be lists")

    if contract.get("execution_mode") != record.get("execution_mode"):
        errors.append(
            "assignment execution_mode does not match admissibility record: "
            f"assignment {contract.get('execution_mode')!r}, proof {record.get('execution_mode')!r}"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Project Resolver destination executability")
    parser.add_argument("--required", nargs="*", default=[])
    parser.add_argument("--available", nargs="*", default=[])
    parser.add_argument("--record", help="Validate an ASSIGNMENT_ADMISSIBILITY JSON file")
    parser.add_argument("--profile", help="Validate against an exact CAPABILITY_PROFILE JSON file")
    parser.add_argument("--assignment", help="Validate the complete ASSIGNMENT proof chain")
    args = parser.parse_args()

    if args.profile and not args.record:
        parser.error("--profile requires --record")
    if args.assignment and (not args.record or not args.profile):
        parser.error("--assignment requires --record and --profile")

    if args.record:
        with open(args.record, "r", encoding="utf-8") as handle:
            record = json.load(handle)
        if args.profile:
            with open(args.profile, "r", encoding="utf-8") as handle:
                profile = json.load(handle)
            if args.assignment:
                with open(args.assignment, "r", encoding="utf-8") as handle:
                    assignment = json.load(handle)
                errors = validate_assignment_execution_contract(assignment, record, profile)
            else:
                errors = validate_admissibility_against_profile(record, profile)
        else:
            errors = validate_admissibility_record(record)
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1

    result = evaluate_assignment_admissibility(args.required, args.available)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ADMISSIBLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
