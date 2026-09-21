from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re

from tools.resource_ledger import AuthorityViolation


_BLOCKING_REASONS = {
    "GRANT_MISSING",
    "AUTHORITY_SOURCE_UNRESOLVED",
    "GRANT_SCOPE_MISMATCH",
    "GRANT_EXPIRED",
    "PARENT_AUTHORITY_VIOLATION",
    "ESTIMATE_MISSING",
    "ESTIMATE_ROUTE_MISMATCH",
    "ROUTE_MISMATCH",
    "HARD_LIMIT_EXCEEDED",
    "RESERVABLE_LIMIT_INSUFFICIENT",
    "UNKNOWN_REQUIRED_RESOURCE",
    "UNCLASSIFIED_METERED_SIDE_EFFECT",
    "OTHER_CONTRACT_BLOCK",
}
_LIMIT_MODES = {"HARD_LIMIT", "RESERVABLE_LIMIT", "OBSERVATION_ONLY"}
_AUTHORITY_TYPES = {
    "OWNER_APPROVED_RESOURCE_AUTHORITY",
    "AUTONOMY_ENVELOPE",
    "PARENT_RESOURCE_GRANT",
    "OTHER_DURABLE_RESOURCE_AUTHORITY",
}
_FINALIZATION_PURPOSES = {
    "RESULT_RECONCILIATION",
    "DURABLE_PARTIAL_OUTPUT",
    "FINAL_ACCOUNTING",
    "CONTROL_HANDOFF",
}
_RESOURCE_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_GRANT_FIELDS = {
    "artifact_type", "artifact_id", "produced_by_role", "assignment_id", "input_state_ref",
    "status", "provenance", "related_artifacts", "issued_by", "authority_source",
    "parent_grant_ref", "scope", "limits", "attempt_limit", "valid_until", "finalization_policy",
}
_ESTIMATE_FIELDS = {
    "artifact_type", "artifact_id", "produced_by_role", "assignment_id", "input_state_ref",
    "status", "provenance", "related_artifacts", "subject_ref", "route_ref",
    "estimator_revision_ref", "basis_refs", "estimates",
}
_ESTIMATE_ITEM_FIELDS = {
    "resource_class", "dimension", "estimate_state", "point_estimate", "quantiles",
    "upper_bound", "confidence", "historical_sample_count", "unknown_resource_state",
}
_QUANTILE_FIELDS = {"probability", "quantity"}
_ESTIMATE_STATUSES = {"ESTIMATED", "PARTIAL", "UNKNOWN"}
_CONFIDENCE = {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}
_OWNER_COMMON_REQUIRED = {
    "artifact_type", "artifact_id", "produced_by_role", "assignment_id", "input_state_ref",
    "status", "provenance", "related_artifacts", "question_ref", "options_presented",
    "selected_option", "owner_constraints", "consequences_acknowledged",
}
_OWNER_RESOURCE_REQUIRED = {
    "authority_role", "decision_kind", "authorized_resource_grant_ref", "authorized_scope",
    "authorized_candidate_ref", "authorized_route_ref", "authorized_resource_classes",
    "authorized_resource_limits", "authorized_attempt_limit", "authorized_valid_until",
    "authorized_finalization_policy", "non_transitive",
}
_OWNER_AFFIRMATIVE = "AUTHORIZE_RESOURCE_AUTHORITY"
_OWNER_DECISION_KIND = "OWNER_APPROVED_RESOURCE_AUTHORITY"


class ResourceAdmissionError(ValueError):
    """Structural failure that prevents a canonical RESOURCE_ADMISSION artifact."""


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or value == "":
        raise ResourceAdmissionError(f"{name} must be a non-empty string")
    return value


def _nullable_text(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _text(value, name)


def _refs(value: Sequence[object] | object, name: str) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ResourceAdmissionError(f"{name} must be an array")
    out = [_text(item, f"{name}[{index}]") for index, item in enumerate(value)]
    if len(out) != len(set(out)):
        raise ResourceAdmissionError(f"{name} must contain unique refs")
    return sorted(out)


def _string_array(
    value: object,
    name: str,
    *,
    non_empty: bool = False,
    unique: bool = False,
) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ResourceAdmissionError(f"{name} must be an array of strings")
    if non_empty and not value:
        raise ResourceAdmissionError(f"{name} must be non-empty")
    if unique and len(value) != len(set(value)):
        raise ResourceAdmissionError(f"{name} must contain unique values")
    return list(value)


def _resource_identifier(value: object, name: str) -> str:
    text = _text(value, name)
    if not _RESOURCE_ID_RE.fullmatch(text):
        raise ResourceAdmissionError(f"{name} must be a canonical resource identifier")
    return text


def _decimal(value: object, name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ResourceAdmissionError(f"{name} must be an exact finite non-negative number")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ResourceAdmissionError(f"{name} must be an exact finite non-negative number") from None
    if not result.is_finite() or result < 0:
        raise ResourceAdmissionError(f"{name} must be an exact finite non-negative number")
    return result


def _positive_integer_or_none(value: object, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ResourceAdmissionError(f"{name} must be null or a non-negative integer")
    return value


def _attempt_limit(value: object, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ResourceAdmissionError(f"{name} must be null or an integer >= 1")
    return value


def _instant(value: object, name: str, *, nullable: bool, strings_only: bool = False) -> datetime | None:
    if value is None:
        if nullable:
            return None
        raise ResourceAdmissionError(f"{name} must be timezone-aware")
    if isinstance(value, datetime) and not strings_only:
        parsed = value
    elif isinstance(value, str) and value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ResourceAdmissionError(f"{name} must be timezone-aware") from None
    else:
        raise ResourceAdmissionError(f"{name} must be timezone-aware")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ResourceAdmissionError(f"{name} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _canonical_limit_items(value: object, name: str) -> list[dict[str, object]]:
    if not isinstance(value, list) or not value:
        raise ResourceAdmissionError(f"{name} must be a non-empty array")
    normalized: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(value):
        if not isinstance(raw, Mapping) or set(raw) != {
            "resource_class", "dimension", "limit_mode", "ordinary_limit", "finalization_reserve"
        }:
            raise ResourceAdmissionError(f"{name}[{index}] malformed")
        resource_class = _resource_identifier(raw.get("resource_class"), f"{name}[{index}].resource_class")
        dimension = _resource_identifier(raw.get("dimension"), f"{name}[{index}].dimension")
        key = (resource_class, dimension)
        if key in seen:
            raise ResourceAdmissionError(f"{name} contains duplicate limit key")
        seen.add(key)
        mode = raw.get("limit_mode")
        if mode not in _LIMIT_MODES:
            raise ResourceAdmissionError(f"{name}[{index}].limit_mode invalid")
        if mode == "OBSERVATION_ONLY":
            if raw.get("ordinary_limit") is not None or raw.get("finalization_reserve") is not None:
                raise ResourceAdmissionError(f"{name} OBSERVATION_ONLY capacity must be null")
            ordinary = final_reserve = None
        else:
            ordinary = _decimal(raw.get("ordinary_limit"), f"{name}[{index}].ordinary_limit")
            final_reserve = _decimal(raw.get("finalization_reserve"), f"{name}[{index}].finalization_reserve")
        normalized.append({
            "resource_class": resource_class,
            "dimension": dimension,
            "limit_mode": mode,
            "ordinary_limit": ordinary,
            "finalization_reserve": final_reserve,
        })
    return sorted(normalized, key=lambda item: (str(item["resource_class"]), str(item["dimension"])))


def _canonical_finalization(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != {"protected", "allowed_purposes"}:
        raise ResourceAdmissionError(f"{name} malformed")
    if value.get("protected") is not True:
        raise ResourceAdmissionError(f"{name}.protected must be true")
    purposes = _string_array(value.get("allowed_purposes"), f"{name}.allowed_purposes", non_empty=True, unique=True)
    if any(purpose not in _FINALIZATION_PURPOSES for purpose in purposes):
        raise ResourceAdmissionError(f"{name}.allowed_purposes contains invalid purpose")
    return {"protected": True, "allowed_purposes": sorted(purposes)}


def _canonical_grant(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != _GRANT_FIELDS:
        raise ResourceAdmissionError("RESOURCE_GRANT has invalid fields")
    if value.get("artifact_type") != "RESOURCE_GRANT":
        raise ResourceAdmissionError("RESOURCE_GRANT artifact_type mismatch")
    scope = value.get("scope")
    authority = value.get("authority_source")
    if not isinstance(scope, Mapping) or set(scope) != {"scope_ref", "candidate_ref", "route_ref", "resource_classes"}:
        raise ResourceAdmissionError("RESOURCE_GRANT scope malformed")
    if not isinstance(authority, Mapping) or set(authority) != {"authority_type", "authority_ref"}:
        raise ResourceAdmissionError("RESOURCE_GRANT authority_source malformed")
    if value.get("produced_by_role") != "control-director" or value.get("issued_by") != "control-director" or value.get("status") != "AUTHORIZED":
        raise ResourceAdmissionError("RESOURCE_GRANT authority producer/status malformed")

    resource_classes = _refs(scope.get("resource_classes"), "scope.resource_classes")
    if not resource_classes:
        raise ResourceAdmissionError("scope.resource_classes must be non-empty")
    for index, resource_class in enumerate(resource_classes):
        _resource_identifier(resource_class, f"scope.resource_classes[{index}]")
    normalized_limits = _canonical_limit_items(value.get("limits"), "RESOURCE_GRANT limits")
    declared_classes = set(resource_classes)
    if any(limit["resource_class"] not in declared_classes for limit in normalized_limits):
        raise ResourceAdmissionError("RESOURCE_GRANT limit resource class is outside grant scope")

    authority_type = authority.get("authority_type")
    if authority_type not in _AUTHORITY_TYPES:
        raise ResourceAdmissionError("RESOURCE_GRANT authority type malformed")
    authority_ref = _text(authority.get("authority_ref"), "authority_source.authority_ref")
    parent_ref = _nullable_text(value.get("parent_grant_ref"), "parent_grant_ref")
    if authority_type == "PARENT_RESOURCE_GRANT" and parent_ref is None:
        raise ResourceAdmissionError("PARENT_RESOURCE_GRANT requires parent_grant_ref")
    if parent_ref is not None and authority_type != "PARENT_RESOURCE_GRANT":
        raise ResourceAdmissionError("child RESOURCE_GRANT must use PARENT_RESOURCE_GRANT authority")
    if parent_ref is not None and authority_ref != parent_ref:
        raise ResourceAdmissionError("PARENT_RESOURCE_GRANT authority_ref must equal parent_grant_ref")

    provenance = _refs(value.get("provenance"), "provenance")
    if not provenance:
        raise ResourceAdmissionError("RESOURCE_GRANT provenance must be non-empty")
    related = _refs(value.get("related_artifacts"), "related_artifacts")
    valid_raw = value.get("valid_until")
    if valid_raw is not None and not isinstance(valid_raw, str):
        raise ResourceAdmissionError("valid_until must be a date-time string or null")
    valid_until = _instant(valid_raw, "valid_until", nullable=True, strings_only=True)
    finalization = _canonical_finalization(value.get("finalization_policy"), "RESOURCE_GRANT finalization_policy")

    return {
        "artifact_type": "RESOURCE_GRANT",
        "artifact_id": _text(value.get("artifact_id"), "artifact_id"),
        "produced_by_role": value.get("produced_by_role"),
        "assignment_id": _nullable_text(value.get("assignment_id"), "assignment_id"),
        "input_state_ref": _nullable_text(value.get("input_state_ref"), "input_state_ref"),
        "status": value.get("status"),
        "provenance": provenance,
        "related_artifacts": related,
        "issued_by": value.get("issued_by"),
        "authority_source": {"authority_type": authority_type, "authority_ref": authority_ref},
        "parent_grant_ref": parent_ref,
        "scope": {
            "scope_ref": _text(scope.get("scope_ref"), "scope.scope_ref"),
            "candidate_ref": _nullable_text(scope.get("candidate_ref"), "scope.candidate_ref"),
            "route_ref": _nullable_text(scope.get("route_ref"), "scope.route_ref"),
            "resource_classes": resource_classes,
        },
        "limits": normalized_limits,
        "attempt_limit": _attempt_limit(value.get("attempt_limit"), "RESOURCE_GRANT attempt_limit"),
        "valid_until": valid_until,
        "finalization_policy": finalization,
    }


def _optional_owner_properties_valid(value: Mapping[str, object]) -> None:
    for field in ("project_id", "authorized_question_id", "authorization_id"):
        if field in value and (not isinstance(value[field], str) or not value[field]):
            raise ResourceAdmissionError(f"OWNER_DECISION_RECORD {field} malformed")
    if "authorized_namespace" in value:
        namespace = value["authorized_namespace"]
        if not isinstance(namespace, str) or not re.fullmatch(r"human-research/.+", namespace):
            raise ResourceAdmissionError("OWNER_DECISION_RECORD authorized_namespace malformed")
    if "default_research_mode_unchanged" in value and not isinstance(value["default_research_mode_unchanged"], bool):
        raise ResourceAdmissionError("OWNER_DECISION_RECORD default_research_mode_unchanged malformed")
    if "qualifications" in value:
        _string_array(value["qualifications"], "OWNER_DECISION_RECORD qualifications")


def _canonical_owner_resource_decision(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ResourceAdmissionError("OWNER_DECISION_RECORD must be an object")
    missing = (_OWNER_COMMON_REQUIRED | _OWNER_RESOURCE_REQUIRED) - set(value)
    if missing:
        raise ResourceAdmissionError("OWNER_DECISION_RECORD missing required resource-authority fields")
    _optional_owner_properties_valid(value)
    if value.get("artifact_type") != "OWNER_DECISION_RECORD":
        raise ResourceAdmissionError("OWNER_DECISION_RECORD artifact_type mismatch")
    if value.get("produced_by_role") != "owner-interface":
        raise ResourceAdmissionError("OWNER_DECISION_RECORD producer mismatch")
    if value.get("status") != "RECORDED":
        raise ResourceAdmissionError("OWNER_DECISION_RECORD status mismatch")
    if value.get("authority_role") != "OWNER_K0":
        raise ResourceAdmissionError("OWNER_DECISION_RECORD authority_role mismatch")
    if value.get("decision_kind") != _OWNER_DECISION_KIND:
        raise ResourceAdmissionError("OWNER_DECISION_RECORD decision_kind mismatch")
    if value.get("non_transitive") is not True:
        raise ResourceAdmissionError("OWNER_DECISION_RECORD non_transitive must be true")

    artifact_id = _text(value.get("artifact_id"), "OWNER_DECISION_RECORD artifact_id")
    assignment_id = _text(value.get("assignment_id"), "OWNER_DECISION_RECORD assignment_id")
    input_state_ref = _text(value.get("input_state_ref"), "OWNER_DECISION_RECORD input_state_ref")
    question_ref = value.get("question_ref")
    selected_option = value.get("selected_option")
    if not isinstance(question_ref, str) or not question_ref:
        raise ResourceAdmissionError("OWNER_DECISION_RECORD question_ref malformed")
    if not isinstance(selected_option, str) or not selected_option:
        raise ResourceAdmissionError("OWNER_DECISION_RECORD selected_option malformed")
    provenance = _string_array(value.get("provenance"), "OWNER_DECISION_RECORD provenance", non_empty=True)
    related = _string_array(value.get("related_artifacts"), "OWNER_DECISION_RECORD related_artifacts", non_empty=True)
    options = _string_array(value.get("options_presented"), "OWNER_DECISION_RECORD options_presented", non_empty=True)
    if _OWNER_AFFIRMATIVE not in options:
        raise ResourceAdmissionError("OWNER_DECISION_RECORD lacks affirmative resource option")
    constraints = _string_array(value.get("owner_constraints"), "OWNER_DECISION_RECORD owner_constraints")
    consequences = _string_array(value.get("consequences_acknowledged"), "OWNER_DECISION_RECORD consequences_acknowledged")

    authorized_grant = _text(value.get("authorized_resource_grant_ref"), "authorized_resource_grant_ref")
    authorized_scope = _text(value.get("authorized_scope"), "authorized_scope")
    candidate = value.get("authorized_candidate_ref")
    route = value.get("authorized_route_ref")
    if candidate is not None and not isinstance(candidate, str):
        raise ResourceAdmissionError("authorized_candidate_ref must be string or null")
    if route is not None and not isinstance(route, str):
        raise ResourceAdmissionError("authorized_route_ref must be string or null")
    classes = _string_array(
        value.get("authorized_resource_classes"),
        "authorized_resource_classes",
        non_empty=True,
        unique=True,
    )
    for index, resource_class in enumerate(classes):
        _resource_identifier(resource_class, f"authorized_resource_classes[{index}]")
    limits = _canonical_limit_items(value.get("authorized_resource_limits"), "authorized_resource_limits")
    attempt_limit = _attempt_limit(value.get("authorized_attempt_limit"), "authorized_attempt_limit")
    valid_raw = value.get("authorized_valid_until")
    if valid_raw is not None and not isinstance(valid_raw, str):
        raise ResourceAdmissionError("authorized_valid_until must be a date-time string or null")
    valid_until = _instant(valid_raw, "authorized_valid_until", nullable=True, strings_only=True)
    finalization = _canonical_finalization(value.get("authorized_finalization_policy"), "authorized_finalization_policy")
    qualifications = _string_array(value.get("qualifications", []), "OWNER_DECISION_RECORD qualifications")

    return {
        "artifact_id": artifact_id,
        "assignment_id": assignment_id,
        "input_state_ref": input_state_ref,
        "provenance": provenance,
        "related_artifacts": related,
        "question_ref": question_ref,
        "options_presented": options,
        "selected_option": selected_option,
        "owner_constraints": constraints,
        "consequences_acknowledged": consequences,
        "authority_role": value.get("authority_role"),
        "decision_kind": value.get("decision_kind"),
        "authorized_resource_grant_ref": authorized_grant,
        "authorized_scope": authorized_scope,
        "authorized_candidate_ref": candidate,
        "authorized_route_ref": route,
        "authorized_resource_classes": sorted(classes),
        "authorized_resource_limits": limits,
        "authorized_attempt_limit": attempt_limit,
        "authorized_valid_until": valid_until,
        "authorized_finalization_policy": finalization,
        "non_transitive": True,
        "qualifications": qualifications,
    }


def _owner_root_authority_valid(
    grant: Mapping[str, object],
    authority_resolver: Callable[[str], Mapping[str, object] | None],
) -> bool:
    authority = grant.get("authority_source")
    if not isinstance(authority, Mapping) or authority.get("authority_type") != _OWNER_DECISION_KIND:
        return False
    if grant.get("parent_grant_ref") is not None:
        return False
    authority_ref = authority.get("authority_ref")
    grant_id = grant.get("artifact_id")
    if not isinstance(authority_ref, str) or authority_ref == "" or authority_ref == grant_id:
        return False
    try:
        source = authority_resolver(authority_ref)
    except Exception:
        return False
    try:
        owner = _canonical_owner_resource_decision(source)
    except ResourceAdmissionError:
        return False
    if owner["artifact_id"] != authority_ref:
        return False
    if owner["selected_option"] != _OWNER_AFFIRMATIVE:
        return False
    if _OWNER_AFFIRMATIVE not in owner["options_presented"]:
        return False
    if owner["owner_constraints"] or owner["qualifications"]:
        return False
    if owner["authorized_resource_grant_ref"] != grant_id or grant_id not in owner["related_artifacts"]:
        return False

    assignment_id = grant.get("assignment_id")
    input_state_ref = grant.get("input_state_ref")
    if not isinstance(assignment_id, str) or not assignment_id or not isinstance(input_state_ref, str) or not input_state_ref:
        return False
    if owner["assignment_id"] != assignment_id or owner["input_state_ref"] != input_state_ref:
        return False
    scope = grant.get("scope")
    if not isinstance(scope, Mapping):
        return False
    if owner["authorized_scope"] != scope.get("scope_ref"):
        return False
    if owner["authorized_candidate_ref"] != scope.get("candidate_ref"):
        return False
    if owner["authorized_route_ref"] != scope.get("route_ref"):
        return False
    if set(owner["authorized_resource_classes"]) != set(scope.get("resource_classes", [])):
        return False
    if owner["authorized_resource_limits"] != grant.get("limits"):
        return False
    if owner["authorized_attempt_limit"] != grant.get("attempt_limit"):
        return False
    if owner["authorized_valid_until"] != grant.get("valid_until"):
        return False
    if owner["authorized_finalization_policy"] != grant.get("finalization_policy"):
        return False
    return True


def _canonical_estimate(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != _ESTIMATE_FIELDS:
        raise ResourceAdmissionError("RESOURCE_ESTIMATE has invalid fields")
    if value.get("artifact_type") != "RESOURCE_ESTIMATE":
        raise ResourceAdmissionError("RESOURCE_ESTIMATE artifact_type mismatch")
    artifact_id = _text(value.get("artifact_id"), "estimate.artifact_id")
    produced_by_role = _text(value.get("produced_by_role"), "estimate.produced_by_role")
    assignment_id = _nullable_text(value.get("assignment_id"), "estimate.assignment_id")
    input_state_ref = _nullable_text(value.get("input_state_ref"), "estimate.input_state_ref")
    status = value.get("status")
    if status not in _ESTIMATE_STATUSES:
        raise ResourceAdmissionError("RESOURCE_ESTIMATE status invalid")
    provenance = _refs(value.get("provenance"), "estimate.provenance")
    if not provenance:
        raise ResourceAdmissionError("RESOURCE_ESTIMATE provenance must be non-empty")
    related = _refs(value.get("related_artifacts"), "estimate.related_artifacts")
    subject_ref = _text(value.get("subject_ref"), "estimate.subject_ref")
    route_ref = _text(value.get("route_ref"), "estimate.route_ref")
    estimator_revision_ref = _text(value.get("estimator_revision_ref"), "estimate.estimator_revision_ref")
    basis_refs = _refs(value.get("basis_refs"), "estimate.basis_refs")
    raw_items = value.get("estimates")
    if not isinstance(raw_items, list) or not raw_items:
        raise ResourceAdmissionError("RESOURCE_ESTIMATE estimates must be a non-empty array")

    normalized_items: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    states: list[str] = []
    for index, raw in enumerate(raw_items):
        if not isinstance(raw, Mapping) or set(raw) != _ESTIMATE_ITEM_FIELDS:
            raise ResourceAdmissionError(f"RESOURCE_ESTIMATE estimates[{index}] has invalid fields")
        resource_class = _resource_identifier(raw.get("resource_class"), f"estimates[{index}].resource_class")
        dimension = _resource_identifier(raw.get("dimension"), f"estimates[{index}].dimension")
        key = (resource_class, dimension)
        if key in seen:
            raise ResourceAdmissionError("RESOURCE_ESTIMATE contains duplicate resource key")
        seen.add(key)
        estimate_state = raw.get("estimate_state")
        if estimate_state not in {"ESTIMATED", "UNKNOWN"}:
            raise ResourceAdmissionError(f"estimates[{index}].estimate_state invalid")
        confidence = raw.get("confidence")
        if confidence not in _CONFIDENCE:
            raise ResourceAdmissionError(f"estimates[{index}].confidence invalid")
        historical_sample_count = _positive_integer_or_none(
            raw.get("historical_sample_count"), f"estimates[{index}].historical_sample_count"
        )
        quantiles = raw.get("quantiles")
        if not isinstance(quantiles, list):
            raise ResourceAdmissionError(f"estimates[{index}].quantiles must be an array")
        normalized_quantiles: list[dict[str, Decimal]] = []
        for q_index, quantile in enumerate(quantiles):
            if not isinstance(quantile, Mapping) or set(quantile) != _QUANTILE_FIELDS:
                raise ResourceAdmissionError(f"estimates[{index}].quantiles[{q_index}] malformed")
            probability = _decimal(quantile.get("probability"), f"estimates[{index}].quantiles[{q_index}].probability")
            if probability <= 0 or probability > 1:
                raise ResourceAdmissionError(f"estimates[{index}].quantiles[{q_index}].probability invalid")
            quantity = _decimal(quantile.get("quantity"), f"estimates[{index}].quantiles[{q_index}].quantity")
            normalized_quantiles.append({"probability": probability, "quantity": quantity})

        if estimate_state == "ESTIMATED":
            point_estimate = _decimal(raw.get("point_estimate"), f"estimates[{index}].point_estimate")
            upper_raw = raw.get("upper_bound")
            upper_bound = None if upper_raw is None else _decimal(upper_raw, f"estimates[{index}].upper_bound")
            if raw.get("unknown_resource_state") != "KNOWN":
                raise ResourceAdmissionError(f"estimates[{index}] ESTIMATED item must have KNOWN resource state")
        else:
            if raw.get("point_estimate") is not None:
                raise ResourceAdmissionError(f"estimates[{index}] UNKNOWN point_estimate must be null")
            if quantiles:
                raise ResourceAdmissionError(f"estimates[{index}] UNKNOWN quantiles must be empty")
            if raw.get("upper_bound") is not None:
                raise ResourceAdmissionError(f"estimates[{index}] UNKNOWN upper_bound must be null")
            if confidence != "UNKNOWN":
                raise ResourceAdmissionError(f"estimates[{index}] UNKNOWN confidence must be UNKNOWN")
            if historical_sample_count is not None:
                raise ResourceAdmissionError(f"estimates[{index}] UNKNOWN historical_sample_count must be null")
            if raw.get("unknown_resource_state") != "ESTIMATE_UNKNOWN":
                raise ResourceAdmissionError(f"estimates[{index}] UNKNOWN resource state must be ESTIMATE_UNKNOWN")
            point_estimate = None
            upper_bound = None

        states.append(str(estimate_state))
        normalized_items.append({
            "resource_class": resource_class,
            "dimension": dimension,
            "estimate_state": estimate_state,
            "point_estimate": point_estimate,
            "quantiles": normalized_quantiles,
            "upper_bound": upper_bound,
            "confidence": confidence,
            "historical_sample_count": historical_sample_count,
            "unknown_resource_state": raw.get("unknown_resource_state"),
        })

    all_estimated = all(state == "ESTIMATED" for state in states)
    all_unknown = all(state == "UNKNOWN" for state in states)
    expected_status = "ESTIMATED" if all_estimated else "UNKNOWN" if all_unknown else "PARTIAL"
    if status != expected_status:
        raise ResourceAdmissionError("RESOURCE_ESTIMATE top-level status contradicts estimate item states")

    return {
        "artifact_type": "RESOURCE_ESTIMATE",
        "artifact_id": artifact_id,
        "produced_by_role": produced_by_role,
        "assignment_id": assignment_id,
        "input_state_ref": input_state_ref,
        "status": status,
        "provenance": provenance,
        "related_artifacts": related,
        "subject_ref": subject_ref,
        "route_ref": route_ref,
        "estimator_revision_ref": estimator_revision_ref,
        "basis_refs": basis_refs,
        "estimates": normalized_items,
    }


def _is_positive_missing(exc: Exception) -> bool:
    if isinstance(exc, KeyError):
        return True
    return isinstance(exc, AuthorityViolation) and str(exc).startswith("grant not registered:")


def _read_grant(reader: object, grant_id: str) -> tuple[str, Mapping[str, object] | None]:
    try:
        value = reader.get_grant(grant_id)  # type: ignore[attr-defined]
    except Exception as exc:
        return ("missing", None) if _is_positive_missing(exc) else ("failure", None)
    if value is None:
        return "missing", None
    if not isinstance(value, Mapping):
        return "failure", None
    return "ok", value


def _read_state(reader: object, grant_id: str, resource_class: str, dimension: str) -> tuple[str, Mapping[str, object] | None]:
    try:
        value = reader.get_resource_state(grant_id, resource_class, dimension)  # type: ignore[attr-defined]
    except Exception:
        return "failure", None
    if not isinstance(value, Mapping):
        return "failure", None
    return "ok", value


def _limit_map(grant: Mapping[str, object]) -> dict[tuple[str, str], Mapping[str, object]]:
    raw = grant.get("limits")
    if not isinstance(raw, list):
        raise ResourceAdmissionError("registered RESOURCE_GRANT limits malformed")
    result: dict[tuple[str, str], Mapping[str, object]] = {}
    for item in raw:
        if not isinstance(item, Mapping):
            raise ResourceAdmissionError("registered RESOURCE_GRANT limit malformed")
        key = (
            _resource_identifier(item.get("resource_class"), "limit.resource_class"),
            _resource_identifier(item.get("dimension"), "limit.dimension"),
        )
        if key in result:
            raise ResourceAdmissionError("registered RESOURCE_GRANT duplicate limit key")
        result[key] = item
    return result


def _base_artifact(
    *, artifact_id: str, assignment_id: object, input_state_ref: object,
    compiled_assignment_ref: str, assignment_admissibility_ref: str, route_ref: str,
    resource_estimate_ref: str | None, resource_grant_ref: str | None,
    availability_evidence_refs: list[str], provenance: list[str], related_artifacts: list[str],
) -> dict[str, object]:
    return {
        "artifact_type": "RESOURCE_ADMISSION",
        "artifact_id": artifact_id,
        "produced_by_role": "control-director",
        "assignment_id": assignment_id,
        "input_state_ref": input_state_ref,
        "status": "NOT_ADMISSIBLE",
        "provenance": provenance,
        "related_artifacts": related_artifacts,
        "compiled_assignment_ref": compiled_assignment_ref,
        "assignment_admissibility_ref": assignment_admissibility_ref,
        "route_ref": route_ref,
        "resource_estimate_ref": resource_estimate_ref,
        "resource_grant_ref": resource_grant_ref,
        "availability_evidence_refs": availability_evidence_refs,
        "evaluations": [],
        "blocking_reasons": [],
        "unknown_resource_state": "KNOWN",
    }


def evaluate_resource_admission(
    *,
    artifact_id: str,
    assignment_id: str,
    input_state_ref: str | None,
    compiled_assignment: Mapping[str, object],
    assignment_admissibility: Mapping[str, object],
    route_ref: str,
    state_identity: str,
    resource_estimate_ref: str,
    resource_estimate: Mapping[str, object] | None,
    resource_grant_ref: str,
    resource_grant: Mapping[str, object] | None,
    resource_state_reader: object,
    authority_resolver: Callable[[str], Mapping[str, object] | None],
    availability_evidence_refs: Sequence[str] = (),
    unclassified_metered_side_effect_refs: Sequence[str] = (),
    now: datetime | str | None = None,
) -> dict[str, object]:
    """Read-only RG-04 resource authorization and current-availability proof."""
    artifact_id = _text(artifact_id, "artifact_id")
    assignment_id = _text(assignment_id, "assignment_id")
    input_state_ref = _nullable_text(input_state_ref, "input_state_ref")
    route_ref = _text(route_ref, "route_ref")
    state_identity = _text(state_identity, "state_identity")
    requested_estimate_ref = _text(resource_estimate_ref, "resource_estimate_ref")
    requested_grant_ref = _text(resource_grant_ref, "resource_grant_ref")
    evidence_refs = _refs(availability_evidence_refs, "availability_evidence_refs")
    side_effect_refs = _refs(unclassified_metered_side_effect_refs, "unclassified_metered_side_effect_refs")
    now_dt = _instant(now if now is not None else datetime.now(timezone.utc), "now", nullable=False)
    if now_dt is None:  # pragma: no cover
        raise ResourceAdmissionError("now must resolve")
    if not hasattr(resource_state_reader, "get_grant") or not hasattr(resource_state_reader, "get_resource_state"):
        raise ResourceAdmissionError("resource_state_reader does not implement the public read interface")
    if not callable(authority_resolver):
        raise ResourceAdmissionError("authority_resolver must be callable")

    compiled_ref = _text(compiled_assignment.get("artifact_id"), "compiled_assignment.artifact_id")
    admissibility_ref = _text(assignment_admissibility.get("artifact_id"), "assignment_admissibility.artifact_id")
    if assignment_admissibility.get("artifact_type") != "ASSIGNMENT_ADMISSIBILITY" or assignment_admissibility.get("status") != "ADMISSIBLE":
        raise ResourceAdmissionError("Resource Admission requires ADMISSIBLE ASSIGNMENT_ADMISSIBILITY")

    estimate_resolved = isinstance(resource_estimate, Mapping)
    grant_resolved = isinstance(resource_grant, Mapping)
    resolved_estimate_ref = requested_estimate_ref if estimate_resolved else None
    resolved_grant_ref = requested_grant_ref if grant_resolved else None
    provenance = sorted({admissibility_ref, *([requested_estimate_ref] if estimate_resolved else []), *([requested_grant_ref] if grant_resolved else [])})
    related = sorted({compiled_ref, admissibility_ref, route_ref, *evidence_refs,
                      *([requested_estimate_ref] if estimate_resolved else []), *([requested_grant_ref] if grant_resolved else [])})
    artifact = _base_artifact(
        artifact_id=artifact_id, assignment_id=assignment_id, input_state_ref=input_state_ref,
        compiled_assignment_ref=compiled_ref, assignment_admissibility_ref=admissibility_ref,
        route_ref=route_ref, resource_estimate_ref=resolved_estimate_ref, resource_grant_ref=resolved_grant_ref,
        availability_evidence_refs=evidence_refs, provenance=provenance, related_artifacts=related,
    )
    blocking: set[str] = set()
    availability_unknown = False
    estimate_unknown = False

    if side_effect_refs:
        blocking.add("UNCLASSIFIED_METERED_SIDE_EFFECT")

    canonical_estimate: dict[str, object] | None = None
    if not estimate_resolved:
        blocking.add("ESTIMATE_MISSING")
        estimate_unknown = True
    else:
        try:
            canonical_estimate = _canonical_estimate(resource_estimate)
        except ResourceAdmissionError:
            blocking.add("OTHER_CONTRACT_BLOCK")
        if canonical_estimate is not None:
            if canonical_estimate.get("artifact_id") != requested_estimate_ref:
                blocking.add("OTHER_CONTRACT_BLOCK")
            if canonical_estimate.get("route_ref") != route_ref:
                blocking.add("ESTIMATE_ROUTE_MISMATCH")
            if canonical_estimate.get("assignment_id") != assignment_id:
                blocking.add("OTHER_CONTRACT_BLOCK")
            if canonical_estimate.get("input_state_ref") != input_state_ref:
                blocking.add("OTHER_CONTRACT_BLOCK")
            if canonical_estimate.get("subject_ref") != compiled_ref:
                blocking.add("OTHER_CONTRACT_BLOCK")

    reader_leaf_status, registered_leaf = _read_grant(resource_state_reader, requested_grant_ref)
    if reader_leaf_status == "missing":
        blocking.add("GRANT_MISSING")
    elif reader_leaf_status == "failure":
        blocking.add("OTHER_CONTRACT_BLOCK")
        availability_unknown = True

    supplied_canonical: dict[str, object] | None = None
    registered_canonical: dict[str, object] | None = None
    if grant_resolved:
        try:
            supplied_canonical = _canonical_grant(resource_grant)
        except ResourceAdmissionError:
            blocking.add("OTHER_CONTRACT_BLOCK")
        if resource_grant.get("artifact_id") != requested_grant_ref:
            blocking.add("AUTHORITY_SOURCE_UNRESOLVED")
    elif reader_leaf_status == "ok":
        blocking.add("AUTHORITY_SOURCE_UNRESOLVED")

    if reader_leaf_status == "ok" and registered_leaf is not None:
        try:
            registered_canonical = _canonical_grant(registered_leaf)
        except ResourceAdmissionError:
            blocking.add("OTHER_CONTRACT_BLOCK")
        if supplied_canonical is not None and registered_canonical is not None and supplied_canonical != registered_canonical:
            blocking.add("AUTHORITY_SOURCE_UNRESOLVED")

    chain: list[Mapping[str, object]] = []
    authority_chain_proven = False
    if registered_canonical is not None:
        current: Mapping[str, object] | None = registered_canonical
        expected_id = requested_grant_ref
        seen: set[str] = set()
        while current is not None:
            gid = current.get("artifact_id")
            if gid != expected_id or not isinstance(gid, str) or not gid:
                blocking.add("OTHER_CONTRACT_BLOCK")
                break
            if gid in seen:
                blocking.add("OTHER_CONTRACT_BLOCK")
                break
            seen.add(gid)
            chain.append(current)
            expiry = current.get("valid_until")
            if expiry is not None and not isinstance(expiry, datetime):
                blocking.add("OTHER_CONTRACT_BLOCK")
                break
            if isinstance(expiry, datetime) and now_dt >= expiry:
                blocking.add("GRANT_EXPIRED")

            authority = current.get("authority_source")
            parent_ref = current.get("parent_grant_ref")
            if not isinstance(authority, Mapping):
                blocking.add("AUTHORITY_SOURCE_UNRESOLVED")
                break
            authority_type = authority.get("authority_type")
            authority_ref = authority.get("authority_ref")
            if parent_ref is None:
                if authority_type == "OWNER_APPROVED_RESOURCE_AUTHORITY":
                    authority_chain_proven = _owner_root_authority_valid(current, authority_resolver)
                else:
                    # AUTONOMY_ENVELOPE and OTHER_DURABLE_RESOURCE_AUTHORITY are frozen RG-01
                    # families, but frozen current main exposes no authoritative RG-04 validator.
                    authority_chain_proven = False
                if not authority_chain_proven:
                    blocking.add("AUTHORITY_SOURCE_UNRESOLVED")
                break

            if not isinstance(parent_ref, str) or not parent_ref or authority_type != "PARENT_RESOURCE_GRANT" or authority_ref != parent_ref:
                blocking.add("AUTHORITY_SOURCE_UNRESOLVED")
                break
            parent_status, parent = _read_grant(resource_state_reader, parent_ref)
            if parent_status == "missing":
                blocking.add("PARENT_AUTHORITY_VIOLATION")
                break
            if parent_status == "failure" or parent is None:
                blocking.add("OTHER_CONTRACT_BLOCK")
                availability_unknown = True
                break
            try:
                parent_canonical = _canonical_grant(parent)
            except ResourceAdmissionError:
                blocking.add("OTHER_CONTRACT_BLOCK")
                break
            expected_id = parent_ref
            current = parent_canonical

    if registered_canonical is not None:
        if registered_canonical.get("assignment_id") != assignment_id:
            blocking.add("GRANT_SCOPE_MISMATCH")
        grant_input = registered_canonical.get("input_state_ref")
        if grant_input is not None and grant_input != input_state_ref:
            blocking.add("GRANT_SCOPE_MISMATCH")
        scope = registered_canonical.get("scope")
        if isinstance(scope, Mapping):
            if scope.get("route_ref") is not None and scope.get("route_ref") != route_ref:
                blocking.add("ROUTE_MISMATCH")
            if scope.get("candidate_ref") is not None and scope.get("candidate_ref") != state_identity:
                blocking.add("GRANT_SCOPE_MISMATCH")
        else:
            blocking.add("GRANT_SCOPE_MISMATCH")

    estimate_items: list[Mapping[str, object]] = []
    if canonical_estimate is not None:
        raw_items = canonical_estimate.get("estimates")
        if isinstance(raw_items, list):
            estimate_items = [item for item in raw_items if isinstance(item, Mapping)]

    chain_limit_maps: list[dict[tuple[str, str], Mapping[str, object]]] = []
    for grant in chain if authority_chain_proven else []:
        try:
            chain_limit_maps.append(_limit_map(grant))
        except ResourceAdmissionError:
            blocking.add("OTHER_CONTRACT_BLOCK")
            chain_limit_maps.append({})

    evaluations: list[dict[str, object]] = []
    for item in estimate_items:
        resource_class = str(item.get("resource_class"))
        dimension = str(item.get("dimension"))
        key = (resource_class, dimension)
        if not chain_limit_maps:
            continue
        if key not in chain_limit_maps[0]:
            blocking.add("GRANT_SCOPE_MISMATCH")
            continue
        leaf_limit = chain_limit_maps[0][key]
        mode = leaf_limit.get("limit_mode")
        if mode not in _LIMIT_MODES:
            blocking.add("OTHER_CONTRACT_BLOCK")
            continue
        if mode == "OBSERVATION_ONLY":
            unknown_state = item.get("unknown_resource_state")
            if unknown_state not in {"KNOWN", "ESTIMATE_UNKNOWN", "METERING_UNAVAILABLE", "ACTUAL_UNKNOWN"}:
                unknown_state = "ESTIMATE_UNKNOWN"
            requirement = item.get("upper_bound") if item.get("estimate_state") == "ESTIMATED" else None
            evaluations.append({
                "resource_class": resource_class, "dimension": dimension, "limit_mode": mode,
                "estimated_requirement": requirement, "available_amount": None,
                "verdict": "ADMISSIBLE", "reason": "OBSERVATION_ONLY_NON_BLOCKING",
                "unknown_resource_state": unknown_state,
            })
            continue

        missing_parent_authority = any(
            key not in limit_map or limit_map[key].get("limit_mode") == "OBSERVATION_ONLY"
            for limit_map in chain_limit_maps[1:]
        )
        requirement = item.get("upper_bound") if item.get("estimate_state") == "ESTIMATED" else None
        requirement_known = item.get("estimate_state") == "ESTIMATED" and requirement is not None
        if not requirement_known:
            estimate_unknown = True

        if missing_parent_authority:
            blocking.add("PARENT_AUTHORITY_VIOLATION")
            evaluations.append({
                "resource_class": resource_class, "dimension": dimension, "limit_mode": mode,
                "estimated_requirement": requirement if requirement_known else None, "available_amount": None,
                "verdict": "NOT_ADMISSIBLE", "reason": "PARENT_AUTHORITY_VIOLATION", "unknown_resource_state": "KNOWN",
            })
            continue

        availabilities: list[Decimal] = []
        state_failed = False
        for index, grant in enumerate(chain):
            gid = str(grant.get("artifact_id"))
            state_status, state = _read_state(resource_state_reader, gid, resource_class, dimension)
            if state_status != "ok" or state is None:
                state_failed = True
                break
            ordinary = state.get("ordinary")
            try:
                expected_mode = chain_limit_maps[index][key].get("limit_mode")
                if (state.get("grant_id") != gid or state.get("resource_class") != resource_class
                        or state.get("dimension") != dimension or state.get("limit_mode") != expected_mode):
                    raise ResourceAdmissionError("resource state identity does not match registered authority")
                if state.get("spend_authority") is not True or not isinstance(ordinary, Mapping):
                    raise ResourceAdmissionError("state carries no spend authority")
                availabilities.append(_decimal(ordinary.get("available"), "ordinary.available"))
            except ResourceAdmissionError:
                state_failed = True
                break
        if state_failed or not availabilities:
            blocking.add("OTHER_CONTRACT_BLOCK")
            availability_unknown = True
            evaluations.append({
                "resource_class": resource_class, "dimension": dimension, "limit_mode": mode,
                "estimated_requirement": requirement if requirement_known else None, "available_amount": None,
                "verdict": "NOT_ADMISSIBLE", "reason": "OTHER_CONTRACT_BLOCK", "unknown_resource_state": "AVAILABILITY_UNKNOWN",
            })
            continue
        effective_available = min(availabilities)

        if not requirement_known or requirement is None:
            blocking.add("UNKNOWN_REQUIRED_RESOURCE")
            evaluations.append({
                "resource_class": resource_class, "dimension": dimension, "limit_mode": mode,
                "estimated_requirement": None, "available_amount": effective_available,
                "verdict": "NOT_ADMISSIBLE", "reason": "UNKNOWN_REQUIRED_RESOURCE", "unknown_resource_state": "ESTIMATE_UNKNOWN",
            })
            continue
        if requirement <= effective_available:
            verdict, reason = "ADMISSIBLE", "AUTHORIZED_AND_AVAILABLE"
        elif mode == "HARD_LIMIT":
            verdict, reason = "NOT_ADMISSIBLE", "HARD_LIMIT_EXCEEDED"
            blocking.add(reason)
        else:
            verdict, reason = "NOT_ADMISSIBLE", "RESERVABLE_LIMIT_INSUFFICIENT"
            blocking.add(reason)
        evaluations.append({
            "resource_class": resource_class, "dimension": dimension, "limit_mode": mode,
            "estimated_requirement": requirement, "available_amount": effective_available,
            "verdict": verdict, "reason": reason, "unknown_resource_state": "KNOWN",
        })

    artifact["evaluations"] = sorted(evaluations, key=lambda item: (str(item["resource_class"]), str(item["dimension"])))
    artifact["blocking_reasons"] = sorted(reason for reason in blocking if reason in _BLOCKING_REASONS)
    if artifact["blocking_reasons"]:
        artifact["status"] = "NOT_ADMISSIBLE"
        artifact["unknown_resource_state"] = "AVAILABILITY_UNKNOWN" if availability_unknown else "ESTIMATE_UNKNOWN" if estimate_unknown else "KNOWN"
    else:
        artifact["status"] = "ADMISSIBLE"
        artifact["unknown_resource_state"] = "KNOWN"
    return artifact
