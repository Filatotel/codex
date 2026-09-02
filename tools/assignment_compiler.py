#!/usr/bin/env python3
"""Deterministic authority-aware assignment compilation.

This module consumes structured control intent.  It deliberately does not parse
natural-language prompts and does not perform destination executability checks.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy

AUTHORITY_CLASSES = (
    "FROZEN_CANDIDATE", "MOVING_PR", "MOVING_BRANCH",
    "POST_MERGE_STATE", "LIVE_REMOTE_STATE",
)
CONTEXT_AUTHORITIES = (
    "PLATFORM_PROVIDED", "RESOLVER_BOUND", "EXECUTOR_RESOLVED", "REMOTE_LIVE",
)
RESPONSIBILITIES = ("EXECUTOR", "CONTROL", "PLATFORM")
INVARIANT_CLASSES = ("immutable", "runtime_resolved", "platform_provided", "remote_live")
COMPILATION_STATUSES = ("COMPILED", "REJECTED")
ENVELOPE_STATUSES = ("SUPPORTED", "UNSUPPORTED")

INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET = "INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET"
PLATFORM_FACT_REAUTHENTICATION = "PLATFORM_FACT_REAUTHENTICATION"
RESPONSIBILITY_MISMATCH = "RESPONSIBILITY_MISMATCH"
UNSUPPORTED_EXECUTION_ENVELOPE = "UNSUPPORTED_EXECUTION_ENVELOPE"
INVALID_CONTEXT_AUTHORITY = "INVALID_CONTEXT_AUTHORITY"
COMPILED_CAPABILITY_MISMATCH = "COMPILED_CAPABILITY_MISMATCH"


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({item.strip() for item in value if isinstance(item, str) and item.strip()})


def _error(code: str, detail: str) -> dict[str, str]:
    return {"code": code, "detail": detail}


def compile_assignment(
    draft: Mapping[str, object],
    supported_obligation_classes: Iterable[str],
) -> dict[str, object]:
    """Compile structured intent into authorized semantics or a rejected artifact."""
    authority_class = draft.get("authority_class")
    facts = deepcopy(draft.get("context_facts", [])) if isinstance(draft.get("context_facts"), list) else []
    invariants = deepcopy(draft.get("invariants", [])) if isinstance(draft.get("invariants"), list) else []
    actions = deepcopy(draft.get("mandatory_actions", [])) if isinstance(draft.get("mandatory_actions"), list) else []
    evidence = deepcopy(draft.get("evidence_requirements", [])) if isinstance(draft.get("evidence_requirements"), list) else []
    stops = deepcopy(draft.get("stop_conditions", [])) if isinstance(draft.get("stop_conditions"), list) else []
    errors: list[dict[str, str]] = []

    if authority_class not in AUTHORITY_CLASSES:
        errors.append(_error(INVALID_CONTEXT_AUTHORITY, "authority_class is not recognized"))

    fact_by_id: dict[str, Mapping[str, object]] = {}
    for index, fact in enumerate(facts):
        if not isinstance(fact, Mapping):
            errors.append(_error(INVALID_CONTEXT_AUTHORITY, f"context_facts[{index}] is not an object"))
            continue
        fact_id = fact.get("fact_id")
        source = fact.get("authority_source")
        required_for = fact.get("required_for")
        if (not isinstance(fact_id, str) or not fact_id or source not in CONTEXT_AUTHORITIES
                or not isinstance(fact.get("fact_kind"), str) or not fact.get("fact_kind")
                or "value_or_ref" not in fact or not isinstance(fact.get("mutable"), bool)
                or not _strings(required_for)):
            errors.append(_error(INVALID_CONTEXT_AUTHORITY, f"context_facts[{index}] has invalid identity or authority_source"))
        elif fact_id in fact_by_id:
            errors.append(_error(INVALID_CONTEXT_AUTHORITY, f"duplicate context fact id: {fact_id}"))
        else:
            fact_by_id[fact_id] = fact

    immutable: list[object] = []
    runtime: list[object] = []
    for index, invariant in enumerate(invariants):
        if not isinstance(invariant, Mapping):
            errors.append(_error(INVALID_CONTEXT_AUTHORITY, f"invariants[{index}] is not an object"))
            continue
        classification = invariant.get("classification")
        if (classification not in INVARIANT_CLASSES
                or invariant.get("responsibility") not in RESPONSIBILITIES
                or not isinstance(invariant.get("invariant_id"), str)
                or not isinstance(invariant.get("identity_kind"), str)
                or "value_or_ref" not in invariant):
            errors.append(_error(INVALID_CONTEXT_AUTHORITY, f"invariants[{index}] has invalid classification"))
            continue
        if (authority_class in {"MOVING_PR", "MOVING_BRANCH"}
                and invariant.get("identity_kind") == "CANDIDATE_HEAD"
                and classification == "immutable"
                and not invariant.get("independent_freeze_authority_ref")):
            errors.append(_error(
                INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET,
                f"{authority_class} cannot freeze an observed candidate HEAD without independent freeze authority",
            ))
        (immutable if classification in {"immutable", "platform_provided"} else runtime).append(invariant)

    for index, condition in enumerate(stops):
        if not isinstance(condition, Mapping):
            errors.append(_error(RESPONSIBILITY_MISMATCH, f"stop_conditions[{index}] is not an object"))
            continue
        classification = condition.get("classification")
        owner = condition.get("responsibility")
        fact = fact_by_id.get(str(condition.get("context_fact_ref", "")))
        if classification not in INVARIANT_CLASSES or owner not in RESPONSIBILITIES:
            errors.append(_error(RESPONSIBILITY_MISMATCH, f"stop_conditions[{index}] has invalid classification or responsibility"))
        elif owner == "EXECUTOR" and classification not in {"runtime_resolved", "remote_live"}:
            errors.append(_error(RESPONSIBILITY_MISMATCH, f"Executor cannot own {classification} stop condition"))
        elif owner == "EXECUTOR" and fact and fact.get("authority_source") in {"PLATFORM_PROVIDED", "RESOLVER_BOUND"}:
            errors.append(_error(RESPONSIBILITY_MISMATCH, f"Executor cannot re-prove stop fact {fact.get('fact_id')}"))

    supported = set(_strings(list(supported_obligation_classes)))
    derived_capabilities: set[str] = set()
    executor: list[object] = []
    control: list[object] = []
    platform: list[object] = []
    for kind, obligations in (("action", actions), ("evidence", evidence)):
        for index, obligation in enumerate(obligations):
            if not isinstance(obligation, Mapping):
                errors.append(_error(RESPONSIBILITY_MISMATCH, f"{kind}[{index}] is not an object"))
                continue
            owner = obligation.get("responsibility")
            fact = fact_by_id.get(str(obligation.get("context_fact_ref", "")))
            if (owner not in RESPONSIBILITIES
                    or not isinstance(obligation.get("action_id"), str)
                    or not isinstance(obligation.get("operation"), str)
                    or not isinstance(obligation.get("required_capabilities"), list)):
                errors.append(_error(RESPONSIBILITY_MISMATCH, f"{kind}[{index}] has invalid responsibility"))
                continue
            if owner == "EXECUTOR" and fact and fact.get("authority_source") in {"PLATFORM_PROVIDED", "RESOLVER_BOUND"}:
                errors.append(_error(RESPONSIBILITY_MISMATCH, f"Executor cannot own proof of {fact.get('authority_source')} fact {fact.get('fact_id')}"))
            if (obligation.get("operation") == "REAUTHENTICATE_CONTEXT_FACT" and fact
                    and fact.get("authority_source") == "PLATFORM_PROVIDED"):
                errors.append(_error(PLATFORM_FACT_REAUTHENTICATION, f"platform-provided fact {fact.get('fact_id')} must not be remotely reconstructed"))
            obligation_class = obligation.get("obligation_class")
            if not isinstance(obligation_class, str) or obligation_class not in supported:
                errors.append(_error(UNSUPPORTED_EXECUTION_ENVELOPE, f"unsupported obligation class: {obligation_class!r}"))
            target = {"EXECUTOR": executor, "CONTROL": control, "PLATFORM": platform}[owner]
            target.append(obligation)
            if owner == "EXECUTOR":
                derived_capabilities.update(_strings(obligation.get("required_capabilities")))

    declared = _strings(draft.get("authorized_required_capabilities"))
    if declared and declared != sorted(derived_capabilities):
        errors.append(_error(COMPILED_CAPABILITY_MISMATCH, "declared capabilities do not equal authorized Executor obligation union"))

    result = {
        "artifact_type": "COMPILED_ASSIGNMENT",
        "artifact_id": draft.get("compiled_artifact_id"),
        "produced_by_role": "control-director",
        "assignment_id": None,
        "input_state_ref": draft.get("input_state_ref"),
        "status": "REJECTED" if errors else "COMPILED",
        "provenance": _strings(draft.get("provenance")),
        "related_artifacts": _strings(draft.get("related_artifacts")),
        "assignment_draft_ref": draft.get("assignment_draft_ref"),
        "authority_class": authority_class,
        "immutable_invariants": immutable,
        "runtime_resolved_invariants": runtime,
        "context_facts": facts,
        "executor_responsibilities": executor,
        "control_responsibilities": control,
        "platform_responsibilities": platform,
        "acceptance_requirements": deepcopy(draft.get("acceptance_requirements", [])),
        "evidence_requirements": evidence,
        "stop_conditions": stops,
        "supported_execution_envelope_status": "UNSUPPORTED" if any(e["code"] == UNSUPPORTED_EXECUTION_ENVELOPE for e in errors) else "SUPPORTED",
        "authorized_mandatory_actions": [] if errors else [item for item in executor if item in actions],
        "authorized_required_capabilities": sorted(derived_capabilities) if not errors else [],
        "compilation_status": "REJECTED" if errors else "COMPILED",
        "compilation_errors": errors,
    }
    return result


def validate_compiled_assignment(compiled: Mapping[str, object]) -> list[str]:
    """Validate the cross-field semantic closure of a compiled artifact."""
    errors: list[str] = []
    if compiled.get("artifact_type") != "COMPILED_ASSIGNMENT": errors.append("artifact_type must be COMPILED_ASSIGNMENT")
    status = compiled.get("compilation_status")
    if status not in COMPILATION_STATUSES or compiled.get("status") != status: errors.append("compilation status is invalid or inconsistent")
    if compiled.get("authority_class") not in AUTHORITY_CLASSES: errors.append("authority_class is invalid")
    envelope = compiled.get("supported_execution_envelope_status")
    if envelope not in ENVELOPE_STATUSES: errors.append("supported execution envelope status is invalid")
    compilation_errors = compiled.get("compilation_errors")
    if not isinstance(compilation_errors, list): errors.append("compilation_errors must be a list")
    elif status == "COMPILED" and compilation_errors: errors.append("COMPILED artifact cannot contain compilation errors")
    elif status == "REJECTED" and not compilation_errors: errors.append("REJECTED artifact must contain compilation errors")
    capabilities: set[str] = set()
    actions = compiled.get("authorized_mandatory_actions")
    if not isinstance(actions, list): errors.append("authorized_mandatory_actions must be a list")
    else:
        for action in actions:
            if isinstance(action, Mapping): capabilities.update(_strings(action.get("required_capabilities")))
            else: errors.append("authorized_mandatory_actions must contain objects")
    declared = _strings(compiled.get("authorized_required_capabilities"))
    if status == "COMPILED" and declared != sorted(capabilities): errors.append(COMPILED_CAPABILITY_MISMATCH)
    if status == "REJECTED" and declared: errors.append("REJECTED artifact cannot authorize capabilities")
    return errors
