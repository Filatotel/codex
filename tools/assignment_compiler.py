#!/usr/bin/env python3
"""Deterministic authority-aware assignment compilation from structured control data."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy

AUTHORITY_CLASSES = ("FROZEN_CANDIDATE", "MOVING_PR", "MOVING_BRANCH", "POST_MERGE_STATE", "LIVE_REMOTE_STATE")
CONTEXT_AUTHORITIES = ("PLATFORM_PROVIDED", "RESOLVER_BOUND", "EXECUTOR_RESOLVED", "REMOTE_LIVE")
RESPONSIBILITIES = ("EXECUTOR", "CONTROL", "PLATFORM")
INVARIANT_CLASSES = ("immutable", "runtime_resolved", "platform_provided", "remote_live")
CLAIM_KINDS = ("IMMUTABLE_INVARIANT", "RUNTIME_FACT", "CONTEXT_FACT", "TASK_OUTCOME", "INDEPENDENT_VERIFICATION")
COMPILATION_STATUSES = ("COMPILED", "REJECTED")
ENVELOPE_STATUSES = ("SUPPORTED", "UNSUPPORTED")

INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET = "INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET"
OBLIGATION_NOT_AUTHORIZED = "OBLIGATION_NOT_AUTHORIZED"
PLATFORM_FACT_REAUTHENTICATION = "PLATFORM_FACT_REAUTHENTICATION"
RESPONSIBILITY_MISMATCH = "RESPONSIBILITY_MISMATCH"
UNSUPPORTED_EXECUTION_ENVELOPE = "UNSUPPORTED_EXECUTION_ENVELOPE"
INVALID_CONTEXT_AUTHORITY = "INVALID_CONTEXT_AUTHORITY"
COMPILED_CAPABILITY_MISMATCH = "COMPILED_CAPABILITY_MISMATCH"

AuthorityResolver = Callable[[str], Mapping[str, object] | None]
EnvelopeResolver = Callable[[str], Mapping[str, object] | None]


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({item.strip() for item in value if isinstance(item, str) and item.strip()})


def _error(code: str, detail: str) -> dict[str, str]:
    return {"code": code, "detail": detail}


def _resolve(resolver: Callable[[str], Mapping[str, object] | None] | None, ref: object) -> Mapping[str, object] | None:
    if resolver is None or not isinstance(ref, str) or not ref:
        return None
    try:
        value = resolver(ref)
    except Exception:
        return None
    return value if isinstance(value, Mapping) and value.get("artifact_id") == ref else None


def _executor_capabilities(actions: object, evidence: object) -> list[str]:
    """Single closure law for all authorized Executor actions and evidence."""
    capabilities: set[str] = set()
    for obligations in (actions, evidence):
        if isinstance(obligations, list):
            for obligation in obligations:
                if isinstance(obligation, Mapping) and obligation.get("responsibility") == "EXECUTOR":
                    capabilities.update(_strings(obligation.get("required_capabilities")))
    return sorted(capabilities)


def _valid_freeze_authority(
    invariant: Mapping[str, object], authority_class: object, resolver: AuthorityResolver | None,
) -> bool:
    record = _resolve(resolver, invariant.get("independent_freeze_authority_ref"))
    return bool(record
        and record.get("artifact_type") == "FREEZE_AUTHORITY"
        and record.get("status") == "AUTHORIZED"
        and record.get("produced_by_role") in {"owner-interface", "control-director"}
        and bool(_strings(record.get("provenance")))
        and record.get("authority_role") in {"OWNER_K0", "CONTROL_DIRECTOR"}
        and record.get("target_ref") == invariant.get("target_ref")
        and record.get("authority_class") == authority_class
        and record.get("authorizes_exact_candidate_freeze") is True
        and record.get("candidate_identity") == invariant.get("value_or_ref"))


def _supported_envelope(resolver: EnvelopeResolver | None, ref: object) -> tuple[Mapping[str, object] | None, set[str]]:
    envelope = _resolve(resolver, ref)
    valid = bool(envelope
        and envelope.get("artifact_type") == "EXECUTION_ENVELOPE"
        and envelope.get("status") == "CURRENT"
        and envelope.get("produced_by_role") == "control-director"
        and bool(_strings(envelope.get("provenance"))))
    return (envelope, set(_strings(envelope.get("supported_obligation_classes")))) if valid and envelope else (None, set())


def _claim_authorizes(
    obligation: Mapping[str, object], claim: Mapping[str, object] | None,
    facts: Mapping[str, Mapping[str, object]], acceptance_refs: set[str],
) -> tuple[bool, str | None]:
    if claim is None:
        return False, "claim_ref is unresolved"
    if claim.get("responsibility") != obligation.get("responsibility"):
        return False, "claim and obligation responsibilities differ"
    target_ref = claim.get("target_ref")
    kind = claim.get("claim_kind")
    if kind == "TASK_OUTCOME" and (claim.get("authority_source") != "RESOLVER_BOUND" or target_ref not in acceptance_refs):
        return False, "task-outcome claim is not bound to an acceptance requirement"
    if kind in {"RUNTIME_FACT", "CONTEXT_FACT"} and target_ref not in facts:
        return False, "fact claim target is unresolved"
    if kind == "INDEPENDENT_VERIFICATION" and not (claim.get("authority_source") == "RESOLVER_BOUND" and claim.get("independent_verification_required") is True):
        return False, "independent verification lacks Resolver authority"
    fact_ref = obligation.get("context_fact_ref")
    if fact_ref is not None and target_ref != fact_ref:
        return False, "claim target does not match obligation context fact"
    fact = facts.get(str(target_ref))
    if fact and fact.get("authority_source") == "PLATFORM_PROVIDED" and obligation.get("responsibility") == "EXECUTOR":
        independent = (claim.get("claim_kind") == "INDEPENDENT_VERIFICATION"
                       and claim.get("authority_source") == "RESOLVER_BOUND"
                       and claim.get("independent_verification_required") is True)
        if not independent:
            return False, PLATFORM_FACT_REAUTHENTICATION
    return True, None


def compile_assignment(
    draft: Mapping[str, object],
    execution_envelope_ref: str,
    envelope_resolver: EnvelopeResolver | None,
    authority_resolver: AuthorityResolver | None = None,
) -> dict[str, object]:
    """Compile structured claims and obligations, failing closed before executability."""
    authority_class = draft.get("authority_class")
    facts = deepcopy(draft.get("context_facts", [])) if isinstance(draft.get("context_facts"), list) else []
    claims = deepcopy(draft.get("authorized_claims", [])) if isinstance(draft.get("authorized_claims"), list) else []
    invariants = deepcopy(draft.get("invariants", [])) if isinstance(draft.get("invariants"), list) else []
    actions = deepcopy(draft.get("mandatory_actions", [])) if isinstance(draft.get("mandatory_actions"), list) else []
    evidence = deepcopy(draft.get("evidence_requirements", [])) if isinstance(draft.get("evidence_requirements"), list) else []
    stops = deepcopy(draft.get("stop_conditions", [])) if isinstance(draft.get("stop_conditions"), list) else []
    errors: list[dict[str, str]] = []
    acceptance_refs = {f"acceptance:{item.get('requirement_id')}" for item in draft.get("acceptance_requirements", []) if isinstance(item, Mapping) and isinstance(item.get("requirement_id"), str)} if isinstance(draft.get("acceptance_requirements"), list) else set()

    if authority_class not in AUTHORITY_CLASSES:
        errors.append(_error(INVALID_CONTEXT_AUTHORITY, "authority_class is not recognized"))

    fact_by_id: dict[str, Mapping[str, object]] = {}
    for index, fact in enumerate(facts):
        if not isinstance(fact, Mapping):
            errors.append(_error(INVALID_CONTEXT_AUTHORITY, f"context_facts[{index}] is not an object")); continue
        fact_id, source = fact.get("fact_id"), fact.get("authority_source")
        if (not isinstance(fact_id, str) or not fact_id or source not in CONTEXT_AUTHORITIES
                or not isinstance(fact.get("fact_kind"), str) or not fact.get("fact_kind")
                or "value_or_ref" not in fact or not isinstance(fact.get("mutable"), bool)
                or not _strings(fact.get("required_for")) or fact_id in fact_by_id):
            errors.append(_error(INVALID_CONTEXT_AUTHORITY, f"context_facts[{index}] is invalid or duplicated"))
        else:
            fact_by_id[fact_id] = fact

    claim_by_id: dict[str, Mapping[str, object]] = {}
    for index, claim in enumerate(claims):
        if (not isinstance(claim, Mapping) or not isinstance(claim.get("claim_id"), str)
                or claim.get("claim_kind") not in CLAIM_KINDS
                or claim.get("authority_source") not in CONTEXT_AUTHORITIES
                or claim.get("responsibility") not in RESPONSIBILITIES
                or claim.get("classification") not in INVARIANT_CLASSES
                or not isinstance(claim.get("independent_verification_required"), bool)
                or claim.get("claim_id") in claim_by_id):
            errors.append(_error(OBLIGATION_NOT_AUTHORIZED, f"authorized_claims[{index}] is invalid or duplicated"))
        else:
            claim_by_id[str(claim["claim_id"])] = claim

    immutable: list[object] = []
    runtime: list[object] = []
    for index, invariant in enumerate(invariants):
        if (not isinstance(invariant, Mapping) or invariant.get("classification") not in INVARIANT_CLASSES
                or invariant.get("responsibility") not in RESPONSIBILITIES
                or not isinstance(invariant.get("invariant_id"), str)
                or not isinstance(invariant.get("identity_kind"), str)
                or not isinstance(invariant.get("target_ref"), str) or "value_or_ref" not in invariant):
            errors.append(_error(INVALID_CONTEXT_AUTHORITY, f"invariants[{index}] is invalid")); continue
        moving_freeze = (authority_class in {"MOVING_PR", "MOVING_BRANCH"}
                         and invariant.get("identity_kind") == "CANDIDATE_HEAD"
                         and invariant.get("classification") == "immutable")
        if moving_freeze and not _valid_freeze_authority(invariant, authority_class, authority_resolver):
            errors.append(_error(INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET,
                                 f"{authority_class} exact identity requires resolved authority for this target and candidate"))
        (immutable if invariant.get("classification") in {"immutable", "platform_provided"} else runtime).append(invariant)

    for index, condition in enumerate(stops):
        if not isinstance(condition, Mapping) or condition.get("classification") not in INVARIANT_CLASSES or condition.get("responsibility") not in RESPONSIBILITIES:
            errors.append(_error(RESPONSIBILITY_MISMATCH, f"stop_conditions[{index}] is invalid")); continue
        fact = fact_by_id.get(str(condition.get("context_fact_ref", "")))
        if condition.get("responsibility") == "EXECUTOR" and (condition.get("classification") not in {"runtime_resolved", "remote_live"} or (fact and fact.get("authority_source") in {"PLATFORM_PROVIDED", "RESOLVER_BOUND"})):
            errors.append(_error(RESPONSIBILITY_MISMATCH, f"Executor cannot own stop condition {condition.get('condition_id')}"))

    envelope, supported_classes = _supported_envelope(envelope_resolver, execution_envelope_ref)
    if not supported_classes:
        errors.append(_error(UNSUPPORTED_EXECUTION_ENVELOPE, "execution envelope reference is unresolved or invalid"))

    executor: list[object] = []
    control: list[object] = []
    platform: list[object] = []
    authorized_actions: list[object] = []
    authorized_evidence: list[object] = []
    for kind, obligations in (("action", actions), ("evidence", evidence)):
        for index, obligation in enumerate(obligations):
            if not isinstance(obligation, Mapping) or obligation.get("responsibility") not in RESPONSIBILITIES:
                errors.append(_error(RESPONSIBILITY_MISMATCH, f"{kind}[{index}] is invalid")); continue
            claim = claim_by_id.get(str(obligation.get("claim_ref", "")))
            authorized, reason = _claim_authorizes(obligation, claim, fact_by_id, acceptance_refs)
            if not authorized:
                code = PLATFORM_FACT_REAUTHENTICATION if reason == PLATFORM_FACT_REAUTHENTICATION else OBLIGATION_NOT_AUTHORIZED
                errors.append(_error(code, f"{kind}[{index}] is not authorized: {reason}"))
            if obligation.get("obligation_class") not in supported_classes:
                errors.append(_error(UNSUPPORTED_EXECUTION_ENVELOPE, f"unsupported obligation class: {obligation.get('obligation_class')!r}"))
            {"EXECUTOR": executor, "CONTROL": control, "PLATFORM": platform}[str(obligation.get("responsibility"))].append(obligation)
            if authorized and obligation.get("obligation_class") in supported_classes:
                (authorized_actions if kind == "action" else authorized_evidence).append(obligation)

    derived = _executor_capabilities(authorized_actions, authorized_evidence)
    declared = _strings(draft.get("authorized_required_capabilities"))
    if declared and declared != derived:
        errors.append(_error(COMPILED_CAPABILITY_MISMATCH, "declared capabilities do not equal authorized Executor obligation union"))

    status = "REJECTED" if errors else "COMPILED"
    return {
        "artifact_type":"COMPILED_ASSIGNMENT", "artifact_id":draft.get("compiled_artifact_id"),
        "produced_by_role":"control-director", "assignment_id":None, "input_state_ref":draft.get("input_state_ref"),
        "status":status, "provenance":_strings(draft.get("provenance")), "related_artifacts":_strings(draft.get("related_artifacts")),
        "assignment_draft_ref":draft.get("assignment_draft_ref"), "authority_class":authority_class,
        "authorized_claims":claims, "immutable_invariants":immutable, "runtime_resolved_invariants":runtime,
        "context_facts":facts, "executor_responsibilities":executor, "control_responsibilities":control,
        "platform_responsibilities":platform, "acceptance_requirements":deepcopy(draft.get("acceptance_requirements", [])),
        "evidence_requirements":evidence, "stop_conditions":stops,
        "supported_execution_envelope_ref":execution_envelope_ref,
        "supported_execution_envelope_status":"UNSUPPORTED" if any(e["code"] == UNSUPPORTED_EXECUTION_ENVELOPE for e in errors) else "SUPPORTED",
        "authorized_mandatory_actions":[] if errors else authorized_actions,
        "authorized_evidence_requirements":[] if errors else authorized_evidence,
        "authorized_required_capabilities":[] if errors else derived,
        "compilation_status":status, "compilation_errors":errors,
    }


def validate_compiled_assignment(
    compiled: Mapping[str, object], envelope_resolver: EnvelopeResolver | None = None,
    authority_resolver: AuthorityResolver | None = None,
) -> list[str]:
    """Validate claim, envelope, and capability closure of a compiled artifact."""
    errors: list[str] = []
    status = compiled.get("compilation_status")
    if compiled.get("artifact_type") != "COMPILED_ASSIGNMENT": errors.append("artifact_type must be COMPILED_ASSIGNMENT")
    if status not in COMPILATION_STATUSES or compiled.get("status") != status: errors.append("compilation status is invalid or inconsistent")
    if compiled.get("authority_class") not in AUTHORITY_CLASSES: errors.append("authority_class is invalid")
    compilation_errors = compiled.get("compilation_errors")
    if not isinstance(compilation_errors, list) or (status == "COMPILED" and compilation_errors) or (status == "REJECTED" and not compilation_errors): errors.append("compilation_errors do not match status")
    facts = compiled.get("context_facts")
    fact_by_id = {str(f.get("fact_id")):f for f in facts if isinstance(f, Mapping) and isinstance(f.get("fact_id"), str)} if isinstance(facts, list) else {}
    claims = compiled.get("authorized_claims")
    claim_by_id = {str(c.get("claim_id")):c for c in claims if isinstance(c, Mapping) and isinstance(c.get("claim_id"), str)} if isinstance(claims, list) else {}
    acceptance = compiled.get("acceptance_requirements")
    acceptance_refs = {f"acceptance:{item.get('requirement_id')}" for item in acceptance if isinstance(item, Mapping) and isinstance(item.get("requirement_id"), str)} if isinstance(acceptance, list) else set()
    actions, evidence = compiled.get("authorized_mandatory_actions"), compiled.get("authorized_evidence_requirements")
    for obligations in (actions, evidence):
        if not isinstance(obligations, list): errors.append("authorized obligations must be lists"); continue
        for obligation in obligations:
            if not isinstance(obligation, Mapping): errors.append(OBLIGATION_NOT_AUTHORIZED); continue
            authorized, _ = _claim_authorizes(obligation, claim_by_id.get(str(obligation.get("claim_ref", ""))), fact_by_id, acceptance_refs)
            if not authorized: errors.append(OBLIGATION_NOT_AUTHORIZED)
    if status == "COMPILED" and isinstance(actions, list) and isinstance(evidence, list):
        expected_executor = [item for group in (actions, evidence) for item in group if isinstance(item, Mapping) and item.get("responsibility") == "EXECUTOR"]
        if compiled.get("executor_responsibilities") != expected_executor:
            errors.append(OBLIGATION_NOT_AUTHORIZED)
    for invariant in compiled.get("immutable_invariants", []) if isinstance(compiled.get("immutable_invariants"), list) else []:
        if (isinstance(invariant, Mapping) and compiled.get("authority_class") in {"MOVING_PR", "MOVING_BRANCH"}
                and invariant.get("identity_kind") == "CANDIDATE_HEAD"
                and not _valid_freeze_authority(invariant, compiled.get("authority_class"), authority_resolver)):
            errors.append(INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET)
    derived = _executor_capabilities(actions, evidence)
    declared = _strings(compiled.get("authorized_required_capabilities"))
    if status == "COMPILED" and declared != derived: errors.append(COMPILED_CAPABILITY_MISMATCH)
    if status == "REJECTED" and declared: errors.append("REJECTED artifact cannot authorize capabilities")
    envelope, supported = _supported_envelope(envelope_resolver, compiled.get("supported_execution_envelope_ref"))
    obligation_classes = {o.get("obligation_class") for group in (actions, evidence) if isinstance(group, list) for o in group if isinstance(o, Mapping)}
    if not supported or not obligation_classes.issubset(supported): errors.append(UNSUPPORTED_EXECUTION_ENVELOPE)
    if status == "COMPILED" and compiled.get("supported_execution_envelope_status") != "SUPPORTED": errors.append("compiled envelope status is not SUPPORTED")
    return errors
