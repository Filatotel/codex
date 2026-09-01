#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections.abc import Callable, Iterable, Mapping
from datetime import datetime, timezone

CapabilityEvidenceResolver = Callable[[str], Mapping[str, object] | None]


def _normalize(values: Iterable[str]) -> list[str]:
    return sorted({value.strip() for value in values if isinstance(value, str) and value.strip()})


def _timestamp(value: object, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty ISO-8601 timestamp")
        return None
    if re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        value,
    ) is None:
        errors.append(f"{field} must be an RFC3339 date-time")
        return None
    offset = re.search(r"([+-])(\d{2}):(\d{2})$", value)
    if offset and (int(offset.group(2)) > 23 or int(offset.group(3)) > 59):
        errors.append(f"{field} has an invalid timezone offset")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        normalized = parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        errors.append(f"{field} must be an ISO-8601 timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field} must include a timezone")
        return None
    return normalized


def _string_list(
    value: object,
    field: str,
    errors: list[str],
    *,
    unique: bool = False,
    min_items: int = 0,
    non_empty: bool = True,
) -> list[str] | None:
    if not isinstance(value, list):
        errors.append(f"{field} must be a list")
        return None
    if len(value) < min_items:
        errors.append(f"{field} must contain at least {min_items} item(s)")
    if not all(isinstance(item, str) and (item.strip() if non_empty else True) for item in value):
        errors.append(f"{field} must be a list of {'non-empty ' if non_empty else ''}strings")
        return None
    normalized = [item.strip() if non_empty else item for item in value]
    if unique and len(set(normalized)) != len(normalized):
        errors.append(f"{field} must not contain duplicates")
    return normalized


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


def validate_capability_evidence_artifact(artifact: Mapping[str, object]) -> list[str]:
    """Validate the schema-backed structural surface of CAPABILITY_EVIDENCE."""
    errors: list[str] = []
    if artifact.get("artifact_type") != "CAPABILITY_EVIDENCE": errors.append("artifact_type must be CAPABILITY_EVIDENCE")
    if artifact.get("status") != "RESOLVED": errors.append("status must be RESOLVED")
    for field in ["artifact_id", "produced_by_role", "runtime_identity", "observation_method", "created_from"]:
        if not isinstance(artifact.get(field), str) or not str(artifact[field]).strip(): errors.append(f"{field} must be a non-empty string")
    for field in ["assignment_id", "input_state_ref"]:
        value = artifact.get(field)
        if field not in artifact: errors.append(f"{field} is required")
        elif value is not None and (not isinstance(value, str) or not value.strip()): errors.append(f"{field} must be null or a non-empty string")
    for field in ["provenance", "related_artifacts"]:
        _string_list(artifact.get(field), field, errors, min_items=1)
    _string_list(artifact.get("capabilities"), "capabilities", errors, unique=True, min_items=1)
    _timestamp(artifact.get("observed_at"), "observed_at", errors)
    _timestamp(artifact.get("valid_until"), "valid_until", errors)
    return errors


def validate_capability_profile(
    profile: Mapping[str, object],
    evidence_resolver: CapabilityEvidenceResolver | None = None,
) -> list[str]:
    """Validate internal consistency, freshness, runtime binding, and evidence coverage."""
    errors: list[str] = []
    if profile.get("artifact_type") != "CAPABILITY_PROFILE":
        errors.append("artifact_type must be CAPABILITY_PROFILE")
    if profile.get("status") != "CURRENT":
        errors.append("capability profile status must be CURRENT")
    for field in ["artifact_id", "produced_by_role", "status", "destination_id", "runtime_identity"]:
        if not isinstance(profile.get(field), str) or not str(profile[field]).strip():
            errors.append(f"{field} must be a non-empty string")
    for field in ["provenance", "related_artifacts", "limitations"]:
        _string_list(profile.get(field), field, errors, non_empty=False)
    for field in ["assignment_id", "input_state_ref"]:
        if field not in profile:
            errors.append(f"{field} is required")
            continue
        value = profile.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{field} must be null or a non-empty string")

    boundary = profile.get("freshness_boundary")
    if not isinstance(boundary, Mapping):
        errors.append("freshness_boundary must be an object")
        observed_at = valid_until = None
    else:
        extra_boundary_fields = sorted(set(boundary) - {"observed_at", "valid_until"})
        if extra_boundary_fields:
            errors.append(f"freshness_boundary has unexpected fields: {extra_boundary_fields}")
        observed_at = _timestamp(boundary.get("observed_at"), "freshness_boundary.observed_at", errors)
        valid_until = _timestamp(boundary.get("valid_until"), "freshness_boundary.valid_until", errors)
        if observed_at and valid_until and observed_at > valid_until:
            errors.append("freshness_boundary observed_at must not be after valid_until")
        now = datetime.now(timezone.utc)
        if observed_at and observed_at > now:
            errors.append("capability profile freshness boundary starts in the future")
        if valid_until and valid_until <= now:
            errors.append("capability profile freshness boundary is expired")

    available = _string_list(
        profile.get("available_capabilities"),
        "available_capabilities",
        errors,
        unique=True,
    )
    unavailable = _string_list(
        profile.get("unavailable_capabilities"),
        "unavailable_capabilities",
        errors,
        unique=True,
    )
    evidence = profile.get("capability_evidence")
    if not isinstance(evidence, list):
        errors.append("capability_evidence must be a list")
        evidence = []

    normalized_available = _normalize(available or [])
    normalized_unavailable = _normalize(unavailable or [])
    overlap = sorted(set(normalized_available) & set(normalized_unavailable))
    if overlap:
        errors.append(f"capabilities cannot be both available and unavailable: {overlap}")

    runtime_identity = profile.get("runtime_identity")
    related_artifacts = profile.get("related_artifacts")
    evidence_artifacts = profile.get("evidence_artifacts")
    if not isinstance(evidence_artifacts, list):
        errors.append("evidence_artifacts must be a list")
        evidence_artifacts = []

    embedded_by_id: dict[str, Mapping[str, object]] = {}
    now = datetime.now(timezone.utc)
    for index, artifact in enumerate(evidence_artifacts):
        prefix = f"evidence_artifacts[{index}]"
        if not isinstance(artifact, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        errors.extend(f"{prefix}.{error}" for error in validate_capability_evidence_artifact(artifact))
        artifact_id = artifact.get("artifact_id")
        if artifact.get("artifact_type") != "CAPABILITY_EVIDENCE":
            errors.append(f"{prefix}.artifact_type must be CAPABILITY_EVIDENCE")
        if not isinstance(artifact_id, str) or not artifact_id.strip():
            errors.append(f"{prefix}.artifact_id must be a non-empty string")
            artifact_id = None
        elif artifact_id in embedded_by_id:
            errors.append(f"duplicate evidence artifact id: {artifact_id}")
        if artifact.get("status") != "RESOLVED":
            errors.append(f"{prefix}.status must be RESOLVED")
        if not isinstance(artifact.get("runtime_identity"), str) or not str(artifact["runtime_identity"]).strip():
            errors.append(f"{prefix}.runtime_identity must be a non-empty string")
        elif artifact.get("runtime_identity") != runtime_identity:
            errors.append(f"{prefix}.runtime_identity mismatch")
        _string_list(
            artifact.get("capabilities"),
            f"{prefix}.capabilities",
            errors,
            unique=True,
            min_items=1,
        )
        for field in ["produced_by_role", "observation_method", "created_from"]:
            if not isinstance(artifact.get(field), str) or not str(artifact[field]).strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")
        for field in ["provenance", "related_artifacts"]:
            _string_list(artifact.get(field), f"{prefix}.{field}", errors, min_items=1)
        for field in ["assignment_id", "input_state_ref"]:
            value = artifact.get(field)
            if field not in artifact:
                errors.append(f"{prefix}.{field} is required")
            elif value is not None and (not isinstance(value, str) or not value.strip()):
                errors.append(f"{prefix}.{field} must be null or a non-empty string")
        evidence_observed = _timestamp(artifact.get("observed_at"), f"{prefix}.observed_at", errors)
        evidence_valid = _timestamp(artifact.get("valid_until"), f"{prefix}.valid_until", errors)
        if evidence_observed and evidence_observed > now:
            errors.append(f"{prefix}.observed_at starts in the future")
        if evidence_valid and evidence_valid <= now:
            errors.append(f"{prefix}.valid_until is expired")
        if evidence_observed and evidence_valid and evidence_observed > evidence_valid:
            errors.append(f"{prefix}.observed_at is after valid_until")
        if observed_at and evidence_observed and evidence_observed > observed_at:
            errors.append(f"{prefix} begins after the profile freshness boundary")
        if valid_until and evidence_valid and evidence_valid < valid_until:
            errors.append(f"{prefix} expires before the profile")
        if artifact_id:
            embedded_by_id[artifact_id] = artifact

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
        if evidence_resolver is None:
            errors.append(f"capability_evidence[{index}].evidence_ref requires governed resolution: {evidence_ref!r}")
            continue
        try:
            artifact = evidence_resolver(evidence_ref)
        except Exception as exc:
            errors.append(f"capability evidence resolver failed closed for {evidence_ref!r}: {type(exc).__name__}")
            continue
        if not isinstance(artifact, Mapping):
            errors.append(f"capability_evidence[{index}].evidence_ref is unresolved: {evidence_ref!r}")
            continue
        if artifact.get("artifact_id") != evidence_ref:
            errors.append(f"resolved evidence artifact identity mismatch for {evidence_ref!r}")
            continue
        embedded = embedded_by_id.get(evidence_ref)
        if embedded is not None and dict(embedded) != dict(artifact):
            errors.append(f"embedded evidence disagrees with authoritative evidence {evidence_ref!r}")
        errors.extend(f"resolved evidence {evidence_ref!r}.{error}" for error in validate_capability_evidence_artifact(artifact))
        # Validate the authoritative object with the same structural surface.
        for field in ["produced_by_role", "observation_method", "created_from"]:
            if not isinstance(artifact.get(field), str) or not str(artifact[field]).strip():
                errors.append(f"resolved evidence {evidence_ref!r}.{field} must be a non-empty string")
        for field in ["provenance", "related_artifacts"]:
            value = artifact.get(field)
            if not isinstance(value, list) or not value or not all(isinstance(v, str) and v.strip() for v in value):
                errors.append(f"resolved evidence {evidence_ref!r}.{field} must be a non-empty string list")
        for field in ["assignment_id", "input_state_ref"]:
            value = artifact.get(field)
            if field not in artifact:
                errors.append(f"resolved evidence {evidence_ref!r}.{field} is required")
            elif value is not None and (not isinstance(value, str) or not value.strip()):
                errors.append(f"resolved evidence {evidence_ref!r}.{field} must be null or a non-empty string")
        if artifact.get("artifact_type") != "CAPABILITY_EVIDENCE" or artifact.get("status") != "RESOLVED":
            errors.append(f"resolved evidence {evidence_ref!r} is not a RESOLVED CAPABILITY_EVIDENCE")
        if artifact.get("runtime_identity") != runtime_identity:
            errors.append(f"resolved evidence {evidence_ref!r}.runtime_identity mismatch")
        resolved_observed = _timestamp(artifact.get("observed_at"), f"resolved evidence {evidence_ref!r}.observed_at", errors)
        resolved_valid = _timestamp(artifact.get("valid_until"), f"resolved evidence {evidence_ref!r}.valid_until", errors)
        if resolved_observed and resolved_observed > now: errors.append(f"resolved evidence {evidence_ref!r}.observed_at starts in the future")
        if resolved_valid and resolved_valid <= now: errors.append(f"resolved evidence {evidence_ref!r}.valid_until is expired")
        if resolved_observed and resolved_valid and resolved_observed > resolved_valid: errors.append(f"resolved evidence {evidence_ref!r}.observed_at is after valid_until")
        if observed_at and resolved_observed and resolved_observed > observed_at: errors.append(f"resolved evidence {evidence_ref!r} begins after the profile freshness boundary")
        if valid_until and resolved_valid and resolved_valid < valid_until: errors.append(f"resolved evidence {evidence_ref!r} expires before the profile")
        capabilities = _string_list(artifact.get("capabilities"), f"resolved evidence {evidence_ref!r}.capabilities", errors, unique=True, min_items=1)
        if capabilities is None or capability.strip() not in _normalize(capabilities):
            errors.append(f"evidence artifact {evidence_ref!r} does not prove {capability.strip()!r}")
        evidence_caps.append(capability.strip())
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
    for field in [
        "artifact_id",
        "produced_by_role",
        "assignment_draft_id",
        "destination_id",
        "runtime_identity",
        "capability_profile_ref",
        "route_ref",
        "execution_mode",
    ]:
        if not isinstance(record.get(field), str) or not str(record[field]).strip():
            errors.append(f"{field} must be a non-empty string")
    for field in ["provenance", "related_artifacts"]:
        _string_list(record.get(field), field, errors, non_empty=False)
    for field in ["assignment_id", "input_state_ref"]:
        if field not in record:
            errors.append(f"{field} is required")
            continue
        value = record.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{field} must be null or a non-empty string")
    for field in ["fallback_mode", "reason"]:
        if field in record and record.get(field) is not None and not isinstance(record.get(field), str):
            errors.append(f"{field} must be null or a string")

    required_list = _string_list(required, "required_capabilities", errors, unique=True)
    available_list = _string_list(available, "available_capabilities", errors, unique=True)
    missing_list = _string_list(missing, "unsatisfied_required_capabilities", errors, unique=True)
    if not isinstance(actions, list) or not actions:
        errors.append("mandatory_actions must be a non-empty list")
        actions = []
    evidence_paths_list = _string_list(
        evidence_paths,
        "mandatory_evidence_paths",
        errors,
    )

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
        action_required_list = _string_list(
            action_required,
            f"mandatory_actions[{index}].required_capabilities",
            errors,
            unique=True,
        )
        if action_required_list is not None:
            derived_required.update(_normalize(action_required_list))
        if evidence_path is not None:
            if not isinstance(evidence_path, str) or not evidence_path.strip():
                errors.append(f"mandatory_actions[{index}].evidence_path must be null or a non-empty string")
            else:
                derived_evidence_paths.add(evidence_path.strip())

    normalized_required = _normalize(required_list or [])
    if sorted(derived_required) != normalized_required:
        errors.append(
            "required_capabilities do not equal union of mandatory action requirements: "
            f"derived {sorted(derived_required)}, declared {normalized_required}"
        )

    normalized_paths = _normalize(evidence_paths_list or [])
    if sorted(derived_evidence_paths) != normalized_paths:
        errors.append(
            "mandatory_evidence_paths do not equal action evidence paths: "
            f"derived {sorted(derived_evidence_paths)}, declared {normalized_paths}"
        )

    if required_list is not None and available_list is not None and missing_list is not None:
        expected = evaluate_assignment_admissibility(required_list, available_list)
        if status != expected["status"]:
            errors.append(f"status drift: expected {expected['status']}, got {status}")
        if _normalize(missing_list) != expected["unsatisfied_required_capabilities"]:
            errors.append(
                "unsatisfied_required_capabilities drift: "
                f"expected {expected['unsatisfied_required_capabilities']}, got {_normalize(missing_list)}"
            )
    return errors


def validate_admissibility_against_profile(
    record: Mapping[str, object],
    profile: Mapping[str, object],
    evidence_resolver: CapabilityEvidenceResolver | None = None,
) -> list[str]:
    """Bind an admissibility record to the exact capability profile it cites."""
    errors = validate_capability_profile(profile, evidence_resolver) + validate_admissibility_record(record)

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


def validate_execution_route(
    route: Mapping[str, object],
    profiles: Mapping[str, Mapping[str, object]],
    evidence_resolver: CapabilityEvidenceResolver | None,
) -> list[str]:
    """Prove every delivery/execution/durable-control segment and handoff."""
    errors: list[str] = []
    if route.get("artifact_type") != "EXECUTION_ROUTE" or route.get("status") != "ADMISSIBLE":
        errors.append("execution route must be an ADMISSIBLE EXECUTION_ROUTE")
    for field in ["artifact_id", "produced_by_role", "assignment_draft_id"]:
        if not isinstance(route.get(field), str) or not str(route[field]).strip():
            errors.append(f"execution_route.{field} must be a non-empty string")
    for field in ["assignment_id", "input_state_ref"]:
        value = route.get(field)
        if field not in route: errors.append(f"execution_route.{field} is required")
        elif value is not None and (not isinstance(value, str) or not value.strip()): errors.append(f"execution_route.{field} must be null or a non-empty string")
    for field in ["provenance", "related_artifacts"]:
        _string_list(route.get(field), f"execution_route.{field}", errors)
    segments = route.get("segments")
    if not isinstance(segments, list) or not segments:
        return errors + ["execution_route.segments must be a non-empty list"]
    roles: set[str] = set()
    ids: set[str] = set()
    segment_caps: dict[str, set[str]] = {}
    segment_by_id: dict[str, Mapping[str, object]] = {}
    for index, segment in enumerate(segments):
        prefix = f"execution_route.segments[{index}]"
        if not isinstance(segment, Mapping):
            errors.append(f"{prefix} must be an object"); continue
        sid, role = segment.get("segment_id"), segment.get("route_role")
        for field in ["segment_id", "route_role", "destination_id", "runtime_identity", "capability_profile_ref", "execution_mode"]:
            if not isinstance(segment.get(field), str) or not str(segment[field]).strip(): errors.append(f"{prefix}.{field} must be a non-empty string")
        if role not in {"CANDIDATE_DELIVERY", "EXECUTION_VERIFICATION", "DURABLE_EVIDENCE_CONTROL"}: errors.append(f"{prefix}.route_role is invalid")
        elif role in roles: errors.append(f"duplicate execution route role: {role}")
        else: roles.add(str(role))
        if isinstance(sid, str):
            if sid in ids: errors.append(f"duplicate route segment id: {sid}")
            ids.add(sid)
        required = _string_list(segment.get("required_capabilities"), f"{prefix}.required_capabilities", errors, unique=True) or []
        profile_ref = segment.get("capability_profile_ref")
        profile = profiles.get(str(profile_ref))
        if profile is None:
            errors.append(f"{prefix}.capability_profile_ref is unresolved: {profile_ref!r}"); continue
        errors.extend(validate_capability_profile(profile, evidence_resolver))
        if profile.get("destination_id") != segment.get("destination_id"): errors.append(f"{prefix}.destination_id mismatch")
        if profile.get("runtime_identity") != segment.get("runtime_identity"): errors.append(f"{prefix}.runtime_identity mismatch")
        available = set(_normalize(profile.get("available_capabilities", [])))
        missing = sorted(set(_normalize(required)) - available)
        if missing: errors.append(f"{prefix} has unproven capabilities: {missing}")
        if isinstance(sid, str):
            segment_caps[sid] = available
            segment_by_id[sid] = segment
    expected_roles = {"CANDIDATE_DELIVERY", "EXECUTION_VERIFICATION", "DURABLE_EVIDENCE_CONTROL"}
    if roles != expected_roles: errors.append(f"execution route roles incomplete: {sorted(expected_roles - roles)}")
    edges = route.get("handoffs")
    if not isinstance(edges, list) or len(edges) < 2: errors.append("execution_route.handoffs must prove both mandatory handoffs"); edges = []
    seen_pairs: set[tuple[object, object]] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, Mapping): errors.append(f"execution_route.handoffs[{index}] must be an object"); continue
        source, target = edge.get("from_segment"), edge.get("to_segment")
        source_required = _string_list(edge.get("source_required_capabilities"), f"execution_route.handoffs[{index}].source_required_capabilities", errors, unique=True) or []
        target_required = _string_list(edge.get("target_required_capabilities"), f"execution_route.handoffs[{index}].target_required_capabilities", errors, unique=True) or []
        internal_required = _string_list(edge.get("internal_required_capabilities"), f"execution_route.handoffs[{index}].internal_required_capabilities", errors, unique=True) or []
        if source not in ids or target not in ids: errors.append(f"execution_route.handoffs[{index}] cites an unknown segment")
        seen_pairs.add((source, target))
        source_available = segment_caps.get(str(source), set())
        target_available = segment_caps.get(str(target), set())
        if edge.get("same_surface") is True:
            source_seg = segment_by_id.get(str(source), {})
            target_seg = segment_by_id.get(str(target), {})
            if (source_seg.get("destination_id"), source_seg.get("runtime_identity")) != (target_seg.get("destination_id"), target_seg.get("runtime_identity")):
                errors.append(f"execution_route.handoffs[{index}] claims false same-surface equivalence")
            if not internal_required:
                errors.append(f"execution_route.handoffs[{index}] same-surface handoff requires internal capabilities")
            missing = sorted(set(internal_required) - source_available)
            if missing: errors.append(f"execution_route.handoffs[{index}] has unproven internal capabilities: {missing}")
        else:
            if not source_required or not target_required:
                errors.append(f"execution_route.handoffs[{index}] cross-surface handoff requires source export and target receive capabilities")
            source_missing = sorted(set(source_required) - source_available)
            target_missing = sorted(set(target_required) - target_available)
            if source_missing: errors.append(f"execution_route.handoffs[{index}] has unproven source capabilities: {source_missing}")
            if target_missing: errors.append(f"execution_route.handoffs[{index}] has unproven target capabilities: {target_missing}")
    ordered = [next((s.get("segment_id") for s in segments if isinstance(s, Mapping) and s.get("route_role") == r), None) for r in ["CANDIDATE_DELIVERY", "EXECUTION_VERIFICATION", "DURABLE_EVIDENCE_CONTROL"]]
    if (ordered[0], ordered[1]) not in seen_pairs or (ordered[1], ordered[2]) not in seen_pairs: errors.append("execution route is missing a mandatory ordered handoff")
    final_result = route.get("final_result")
    if not isinstance(final_result, Mapping):
        errors.append("execution_route.final_result must be an object")
    else:
        segment_ref = final_result.get("segment_ref")
        destination_id = final_result.get("destination_id")
        if not isinstance(segment_ref, str) or segment_ref not in segment_by_id:
            errors.append("execution_route.final_result.segment_ref is unresolved")
        else:
            endpoint = segment_by_id[segment_ref]
            if endpoint.get("route_role") != "DURABLE_EVIDENCE_CONTROL": errors.append("execution_route.final_result must reference the durable segment")
            if destination_id != endpoint.get("destination_id"): errors.append("execution_route.final_result.destination_id does not match durable segment")
        if not isinstance(destination_id, str) or not destination_id.strip(): errors.append("execution_route.final_result.destination_id must be a non-empty string")
    return errors


def validate_assignment_artifact(assignment: Mapping[str, object]) -> list[str]:
    """Validate the schema-required ASSIGNMENT surface used by the complete-chain CLI."""
    errors: list[str] = []
    if assignment.get("artifact_type") != "ASSIGNMENT":
        errors.append("assignment artifact_type must be ASSIGNMENT")
    for field in [
        "artifact_id",
        "produced_by_role",
        "assignment_id",
        "status",
        "objective",
        "result_to",
    ]:
        if not isinstance(assignment.get(field), str) or not str(assignment[field]).strip():
            errors.append(f"assignment.{field} must be a non-empty string")
    if "input_state_ref" not in assignment:
        errors.append("assignment.input_state_ref is required")
    else:
        input_state_ref = assignment.get("input_state_ref")
        if input_state_ref is not None and (
            not isinstance(input_state_ref, str) or not input_state_ref.strip()
        ):
            errors.append("assignment.input_state_ref must be null or a non-empty string")
    for field in ["provenance", "related_artifacts", "acceptance", "stop_conditions"]:
        _string_list(assignment.get(field), f"assignment.{field}", errors, non_empty=False)
    _string_list(
        assignment.get("authority"),
        "assignment.authority",
        errors,
        min_items=1,
        non_empty=False,
    )
    required_outputs = assignment.get("required_outputs")
    if required_outputs is not None:
        _string_list(required_outputs, "assignment.required_outputs", errors, non_empty=False)

    scope = assignment.get("scope")
    if not isinstance(scope, Mapping):
        errors.append("assignment.scope must be an object")
    else:
        _string_list(scope.get("allowed"), "assignment.scope.allowed", errors, non_empty=False)
        _string_list(scope.get("forbidden"), "assignment.scope.forbidden", errors, non_empty=False)

    contract = assignment.get("execution_contract")
    if not isinstance(contract, Mapping):
        errors.append("assignment.execution_contract must be an object")
        return errors

    for field in [
        "assignment_draft_ref",
        "destination_id",
        "runtime_identity",
        "capability_profile_ref",
        "admissibility_ref",
        "route_ref",
        "execution_mode",
    ]:
        if not isinstance(contract.get(field), str) or not str(contract[field]).strip():
            errors.append(f"assignment.execution_contract.{field} must be a non-empty string")
    if contract.get("proof_status") != "PROVEN":
        errors.append("assignment execution proof_status must be PROVEN")
    _string_list(
        contract.get("required_capabilities"),
        "assignment.execution_contract.required_capabilities",
        errors,
        unique=True,
    )
    unsatisfied = _string_list(
        contract.get("unsatisfied_required_capabilities"),
        "assignment.execution_contract.unsatisfied_required_capabilities",
        errors,
        unique=True,
    )
    if unsatisfied:
        errors.append("assignment.execution_contract.unsatisfied_required_capabilities must be empty")
    _string_list(
        contract.get("mandatory_evidence_paths"),
        "assignment.execution_contract.mandatory_evidence_paths",
        errors,
    )
    fallback = contract.get("fallback_mode")
    if fallback is not None and not isinstance(fallback, str):
        errors.append("assignment.execution_contract.fallback_mode must be null or a string")
    return errors


def validate_assignment_execution_contract(
    assignment: Mapping[str, object],
    record: Mapping[str, object],
    profile: Mapping[str, object],
    evidence_resolver: CapabilityEvidenceResolver | None = None,
    route: Mapping[str, object] | None = None,
    route_profiles: Mapping[str, Mapping[str, object]] | None = None,
) -> list[str]:
    """Validate the complete executable-assignment proof chain."""
    errors = (
        validate_admissibility_against_profile(record, profile, evidence_resolver)
        + validate_assignment_artifact(assignment)
    )
    contract = assignment.get("execution_contract")
    if not isinstance(contract, Mapping):
        return errors

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
            errors.append("assignment unsatisfied_required_capabilities do not match admissibility record")
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

    if route is None:
        errors.append("complete executable assignment requires an authoritative execution route")
    else:
        errors.extend(validate_execution_route(route, route_profiles or {str(profile.get("artifact_id")): profile}, evidence_resolver))
        if contract.get("route_ref") != route.get("artifact_id"):
            errors.append("assignment route_ref does not match execution route identity")
        if record.get("route_ref") != route.get("artifact_id"):
            errors.append("admissibility route_ref does not match execution route identity")
        if route.get("assignment_draft_id") != record.get("assignment_draft_id"):
            errors.append("execution route assignment_draft_id mismatch")
        final_result = route.get("final_result")
        if not isinstance(final_result, Mapping) or assignment.get("result_to") != final_result.get("destination_id"):
            errors.append("assignment result_to does not match bound final durable route destination")
        route_segments = route.get("segments")
        execution_segment = next((segment for segment in route_segments if isinstance(segment, Mapping) and segment.get("route_role") == "EXECUTION_VERIFICATION"), None) if isinstance(route_segments, list) else None
        if not isinstance(execution_segment, Mapping):
            errors.append("execution route has no bound execution segment")
        else:
            for field in ["destination_id", "runtime_identity", "capability_profile_ref"]:
                if execution_segment.get(field) != contract.get(field):
                    errors.append(f"execution route execution segment {field} mismatch")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Project Resolver destination executability")
    parser.add_argument("--required", nargs="*", default=[])
    parser.add_argument("--available", nargs="*", default=[])
    parser.add_argument("--record", help="Validate an ASSIGNMENT_ADMISSIBILITY JSON file")
    parser.add_argument("--profile", help="Validate against an exact CAPABILITY_PROFILE JSON file")
    parser.add_argument("--assignment", help="Validate the complete ASSIGNMENT proof chain")
    parser.add_argument("--evidence-bundle", help="Governed offline CAPABILITY_EVIDENCE JSON array")
    parser.add_argument("--route", help="Validate the cited EXECUTION_ROUTE JSON file")
    parser.add_argument("--route-profiles", help="Offline JSON array of route CAPABILITY_PROFILE artifacts")
    args = parser.parse_args()

    if args.profile and not args.record:
        parser.error("--profile requires --record")
    if args.assignment and (not args.record or not args.profile):
        parser.error("--assignment requires --record and --profile")
    if args.assignment and (not args.evidence_bundle or not args.route):
        parser.error("--assignment requires --evidence-bundle and --route")

    if args.record:
        with open(args.record, "r", encoding="utf-8") as handle:
            record = json.load(handle)
        if args.profile:
            with open(args.profile, "r", encoding="utf-8") as handle:
                profile = json.load(handle)
            if args.assignment:
                with open(args.assignment, "r", encoding="utf-8") as handle:
                    assignment = json.load(handle)
                with open(args.evidence_bundle, "r", encoding="utf-8") as handle:
                    bundle = json.load(handle)
                evidence_by_id = {item.get("artifact_id"): item for item in bundle if isinstance(item, Mapping)} if isinstance(bundle, list) else {}
                with open(args.route, "r", encoding="utf-8") as handle:
                    route = json.load(handle)
                profiles = {str(profile.get("artifact_id")): profile}
                if args.route_profiles:
                    with open(args.route_profiles, "r", encoding="utf-8") as handle:
                        for item in json.load(handle):
                            if isinstance(item, Mapping): profiles[str(item.get("artifact_id"))] = item
                errors = validate_assignment_execution_contract(assignment, record, profile, evidence_by_id.get, route, profiles)
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
