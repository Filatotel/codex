#!/usr/bin/env python3
"""Bundle-local post-spawn composition of the Control Director procedure.

The module interprets only explicit, structured transition authority carried by
an existing DIRECTOR_DECISION.  It never authors an assignment; an ``ASSIGN``
result is a baton back to the existing pre-spawn ``resolve_spawn`` path.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.executability import validate_capability_profile

BATONS = {"ASSIGN", "WAIT", "ESCALATE", "COMPLETE"}


def _out(state: str, reason: str, **details: object) -> dict[str, object]:
    return {"status": state, "control_state": state, "reason": reason, **details}


def _strings(value: object, field: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        return [f"{field} must be a{' non-empty' if nonempty else ''} list"]
    if not all(isinstance(item, str) and item.strip() for item in value):
        return [f"{field} must contain only non-empty strings"]
    return []


def _common(artifact: Mapping[str, object], artifact_type: str, role: str) -> list[str]:
    errors: list[str] = []
    if artifact.get("artifact_type") != artifact_type:
        errors.append(f"artifact_type must be {artifact_type}")
    if artifact.get("produced_by_role") != role:
        errors.append(f"produced_by_role must be {role}")
    for field in ("artifact_id", "assignment_id"):
        if not isinstance(artifact.get(field), str) or not str(artifact[field]).strip():
            errors.append(f"{field} must be a non-empty string")
    state_ref = artifact.get("input_state_ref")
    if state_ref is not None and (not isinstance(state_ref, str) or not state_ref.strip()):
        errors.append("input_state_ref must be null or a non-empty string")
    errors += _strings(artifact.get("provenance"), "provenance")
    errors += _strings(artifact.get("related_artifacts"), "related_artifacts")
    return errors


def _executor_errors(result: Mapping[str, object]) -> list[str]:
    errors = _common(result, "EXECUTOR_RESULT", "executor")
    if result.get("status") not in {"COMPLETE", "PARTIAL", "BLOCKED", "FAILED"}:
        errors.append("status is invalid")
    for field in ("resulting_state_refs", "evidence_refs", "deferred_findings", "limitations"):
        errors += _strings(result.get(field), field)
    claims = result.get("claims")
    if not isinstance(claims, list):
        errors.append("claims must be a list")
    else:
        seen: set[str] = set()
        for index, claim in enumerate(claims):
            if not isinstance(claim, Mapping):
                errors.append(f"claims[{index}] must be an object"); continue
            claim_id = claim.get("claim_id")
            if not isinstance(claim_id, str) or not claim_id.strip():
                errors.append(f"claims[{index}].claim_id must be non-empty")
            elif claim_id in seen:
                errors.append(f"duplicate claim_id: {claim_id}")
            else:
                seen.add(claim_id)
            if not isinstance(claim.get("claim"), str):
                errors.append(f"claims[{index}].claim must be a string")
            if claim.get("acceptance_status") not in {"SATISFIED", "NOT_SATISFIED"}:
                errors.append(f"claims[{index}].acceptance_status is required")
            errors += _strings(claim.get("acceptance_requirement_ids"), f"claims[{index}].acceptance_requirement_ids", nonempty=True)
    return errors


def _verification_errors(result: Mapping[str, object]) -> list[str]:
    errors = _common(result, "VERIFICATION_RESULT", "control-verifier")
    if result.get("status") not in {"CONFIRMED", "QUALIFIED", "NOT_PROVEN", "BLOCKED"}:
        errors.append("status is invalid")
    if not isinstance(result.get("executor_result_ref"), str) or not str(result["executor_result_ref"]).strip():
        errors.append("executor_result_ref must be a non-empty string")
    verdicts = result.get("claim_verdicts")
    if not isinstance(verdicts, list):
        errors.append("claim_verdicts must be a list")
    else:
        seen: set[str] = set()
        for index, verdict in enumerate(verdicts):
            if not isinstance(verdict, Mapping):
                errors.append(f"claim_verdicts[{index}] must be an object"); continue
            claim_id = verdict.get("claim_id")
            if not isinstance(claim_id, str) or not claim_id.strip():
                errors.append(f"claim_verdicts[{index}].claim_id must be non-empty")
            elif claim_id in seen:
                errors.append(f"duplicate verification claim_id: {claim_id}")
            else:
                seen.add(claim_id)
            if verdict.get("verdict") not in {"CONFIRMED", "QUALIFIED", "NOT_PROVEN"}:
                errors.append(f"claim_verdicts[{index}].verdict is invalid")
            if "evidence_refs" in verdict:
                errors += _strings(verdict.get("evidence_refs"), f"claim_verdicts[{index}].evidence_refs")
            if "note" in verdict and not isinstance(verdict.get("note"), str):
                errors.append(f"claim_verdicts[{index}].note must be a string")
    errors += _strings(result.get("additional_findings"), "additional_findings")
    errors += _strings(result.get("evidence_gaps"), "evidence_gaps")
    return errors


def _artifacts(value: object) -> tuple[dict[str, Mapping[str, object]], list[str]]:
    if not isinstance(value, list):
        return {}, ["artifacts must be a list"]
    found: dict[str, Mapping[str, object]] = {}
    errors: list[str] = []
    for index, artifact in enumerate(value):
        if not isinstance(artifact, Mapping):
            errors.append(f"artifacts[{index}] must be an object"); continue
        artifact_id = artifact.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id.strip():
            errors.append(f"artifacts[{index}].artifact_id must be non-empty")
        elif artifact_id in found:
            errors.append(f"duplicate artifact_id: {artifact_id}")
        else:
            found[artifact_id] = artifact
    return found, errors


def _proof_problem(proof: Mapping[str, object], artifacts: Mapping[str, Mapping[str, object]]) -> tuple[str, str] | None:
    lifecycle = proof.get("transition_proof")
    if not isinstance(lifecycle, Mapping):
        return "ESCALATE", "MALFORMED_PROOF_LIFECYCLE"
    dependencies = lifecycle.get("dependency_bindings")
    if not isinstance(dependencies, list) or not dependencies:
        return "ESCALATE", "MALFORMED_PROOF_LIFECYCLE"
    for binding in dependencies:
        if not isinstance(binding, Mapping):
            return "ESCALATE", "MALFORMED_PROOF_LIFECYCLE"
        ref, identity = binding.get("dependency_ref"), binding.get("proven_identity")
        if not isinstance(ref, str) or not isinstance(identity, str) or not ref or not identity:
            return "ESCALATE", "MALFORMED_PROOF_LIFECYCLE"
        current = artifacts.get(ref)
        if not isinstance(current, Mapping):
            return "ESCALATE", "UNAUTHORIZED_PROOF_REFERENCE"
        if current.get("state_identity") != identity:
            return "WAIT", "RELEVANT_PROOF_STALE"
    return None


def resolve_transition(control_bundle: Mapping[str, object]) -> dict[str, object]:
    """Reconcile one structured local post-spawn bundle to exactly one baton."""
    if not isinstance(control_bundle, Mapping):
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT")
    artifacts, errors = _artifacts(control_bundle.get("artifacts"))
    if errors:
        reason = "CONTRADICTORY_CONTROL_ARTIFACTS" if any("duplicate artifact_id" in error for error in errors) else "MALFORMED_CONTROL_ARTIFACT"
        return _out("ESCALATE", reason, errors=errors)

    refs = control_bundle.get("refs")
    if not isinstance(refs, Mapping):
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=["refs must be an object"])
    for required in ("current_state_ref", "prior_director_decision_ref", "assignment_ref", "executor_result_ref"):
        if not isinstance(refs.get(required), str) or not refs[required]:
            if required == "executor_result_ref":
                return _out("WAIT", "EXECUTOR_RESULT_PENDING")
            return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=[f"refs.{required} is required"])
    current, director, assignment, executor = (artifacts.get(refs[key]) for key in
        ("current_state_ref", "prior_director_decision_ref", "assignment_ref", "executor_result_ref"))
    if not all(isinstance(item, Mapping) for item in (current, director, assignment)):
        return _out("ESCALATE", "REFERENCE_IDENTITY_MISMATCH")
    if not isinstance(executor, Mapping):
        return _out("WAIT", "EXECUTOR_RESULT_PENDING")
    if director.get("artifact_type") != "DIRECTOR_DECISION" or director.get("produced_by_role") != "control-director":
        return _out("ESCALATE", "MALFORMED_DIRECTOR_DECISION")
    authority = director.get("transition_authority")
    if not isinstance(authority, Mapping):
        return _out("ESCALATE", "MISSING_ACCEPTANCE_SEMANTICS")
    assignment_id = assignment.get("assignment_id")
    if assignment.get("artifact_type") != "ASSIGNMENT" or not isinstance(assignment_id, str):
        return _out("ESCALATE", "MALFORMED_ASSIGNMENT")
    if director.get("assignment_id") != assignment_id or director.get("input_state_ref") != assignment.get("input_state_ref"):
        return _out("ESCALATE", "CONTROL_POINT_IDENTITY_MISMATCH")
    executor_errors = _executor_errors(executor)
    if executor_errors:
        return _out("ESCALATE", "MALFORMED_EXECUTOR_RESULT", errors=executor_errors)
    if executor.get("assignment_id") != assignment_id or executor.get("input_state_ref") != assignment.get("input_state_ref"):
        return _out("ESCALATE", "EXECUTOR_RESULT_IDENTITY_MISMATCH")
    if current.get("artifact_id") not in executor.get("resulting_state_refs", []):
        return _out("ESCALATE", "CURRENT_STATE_IDENTITY_MISMATCH")

    requirements = authority.get("acceptance_requirements")
    if not isinstance(requirements, list) or not requirements:
        return _out("ESCALATE", "MISSING_ACCEPTANCE_SEMANTICS")
    required: dict[str, str] = {}
    for item in requirements:
        if not isinstance(item, Mapping) or item.get("required") is not True or not isinstance(item.get("requirement_id"), str) or not isinstance(item.get("claim_id"), str):
            return _out("ESCALATE", "MALFORMED_ACCEPTANCE_AUTHORITY")
        if item["requirement_id"] in required:
            return _out("ESCALATE", "CONTRADICTORY_CONTROL_ARTIFACTS")
        required[item["requirement_id"]] = item["claim_id"]

    proof_refs = authority.get("required_proof_refs")
    if not isinstance(proof_refs, list) or not all(isinstance(ref, str) and ref for ref in proof_refs):
        return _out("ESCALATE", "MALFORMED_PROOF_AUTHORITY")
    for proof_ref in proof_refs:
        proof = artifacts.get(proof_ref)
        if not isinstance(proof, Mapping) or proof_ref not in assignment.get("related_artifacts", []):
            return _out("ESCALATE", "UNAUTHORIZED_PROOF_REFERENCE")
        problem = _proof_problem(proof, artifacts)
        if problem:
            return _out(*problem, stale_proof_ref=proof_ref)

    # Capability drift is checked selectively only for a protected transition
    # that explicitly relies on the old assignment admission.
    if authority.get("requires_current_executability") is True:
        profile_ref = refs.get("current_capability_profile_ref")
        profile = artifacts.get(profile_ref) if isinstance(profile_ref, str) else None
        contract = assignment.get("execution_contract")
        if not isinstance(profile, Mapping) or not isinstance(contract, Mapping):
            return _out("WAIT", "CURRENT_EXECUTABILITY_REVALIDATION_REQUIRED")
        profile_errors = validate_capability_profile(profile, artifacts.get)
        if profile_errors:
            return _out("WAIT", "CURRENT_EXECUTABILITY_REVALIDATION_REQUIRED", errors=profile_errors)
        missing = sorted(set(contract.get("required_capabilities", [])) - set(profile.get("available_capabilities", [])))
        if missing or profile.get("runtime_identity") != contract.get("runtime_identity"):
            return _out("WAIT", "BLOCKED_RUNTIME_DRIFT", missing_capabilities=missing)

    verification_required = authority.get("verification_required")
    if not isinstance(verification_required, bool):
        return _out("ESCALATE", "MISSING_VERIFICATION_REQUIREMENT")
    verification = None
    verification_ref = refs.get("verification_result_ref")
    if verification_required:
        if not isinstance(verification_ref, str) or not verification_ref or verification_ref not in artifacts:
            return _out("WAIT", "VERIFICATION_RESULT_PENDING")
        verification = artifacts[verification_ref]
        verification_errors = _verification_errors(verification)
        if verification_errors:
            return _out("ESCALATE", "MALFORMED_VERIFICATION_RESULT", errors=verification_errors)
        if (verification.get("assignment_id") != assignment_id or verification.get("executor_result_ref") != executor.get("artifact_id")
                or verification.get("input_state_ref") != executor.get("input_state_ref")):
            return _out("ESCALATE", "VERIFICATION_RESULT_IDENTITY_MISMATCH")

    claims = {claim["claim_id"]: claim for claim in executor["claims"]}
    if any(claim_id not in claims or requirement_id not in claims[claim_id]["acceptance_requirement_ids"]
           for requirement_id, claim_id in required.items()):
        return _out("ESCALATE", "ACCEPTANCE_CLAIM_IDENTITY_MISMATCH")
    satisfied = all(claims[claim_id]["acceptance_status"] == "SATISFIED" for claim_id in required.values())
    if verification_required:
        verdicts = {item["claim_id"]: item["verdict"] for item in verification["claim_verdicts"]}
        if any(claim_id not in verdicts for claim_id in required.values()):
            return _out("ESCALATE", "VERIFICATION_TARGET_IDENTITY_MISMATCH")
        if any(verdicts[claim_id] != "CONFIRMED" for claim_id in required.values()) or verification.get("status") != "CONFIRMED":
            return _out("ESCALATE", "MATERIAL_ACCEPTANCE_CONTRADICTION")
    engine_id = current.get("engine_id")
    required_claims = [claims[claim_id] for claim_id in required.values()]
    if engine_id == "research":
        if authority.get("research_admission") != "MACHINE_ONLY_ADMITTED" or any(
            claim.get("engine_semantics") != "research"
            or claim.get("machine_only") is not True
            or claim.get("research_status") not in {"SUPPORTED", "READY_FOR_OWNER_DECISION"}
            for claim in required_claims
        ):
            return _out("ESCALATE", "RESEARCH_RESULT_SEMANTICS_INVALID")
    elif engine_id == "verification":
        verifier_targets = {item["claim_id"]: item.get("exact_claim_target_ref") for item in verification["claim_verdicts"]} if verification else {}
        if any(claim.get("engine_semantics") != "verification"
               or not isinstance(claim.get("exact_claim_target_ref"), str)
               or verifier_targets.get(claim["claim_id"]) != claim.get("exact_claim_target_ref")
               for claim in required_claims):
            return _out("ESCALATE", "VERIFICATION_EXACT_TARGET_MISMATCH")
    elif engine_id == "production/software" and not executor.get("evidence_refs"):
        return _out("ESCALATE", "SOFTWARE_EVIDENCE_MISSING")
    if satisfied and executor.get("status") == "COMPLETE":
        return _out("COMPLETE", "AUTHORITATIVE_ACCEPTANCE_SATISFIED")

    incomplete = authority.get("incomplete_transition")
    if incomplete == "ASSIGN":
        intent_ref = authority.get("next_control_intent_ref")
        intent = artifacts.get(intent_ref) if isinstance(intent_ref, str) else None
        if not isinstance(intent, Mapping) or intent.get("artifact_type") != "CONTROL_INTENT" or intent.get("assignment_id") != assignment_id:
            return _out("ESCALATE", "NEXT_ASSIGN_AUTHORITY_MISSING")
        if "assignment" in intent or "assignment_id_to_issue" in intent or "spawn_ready" in intent:
            return _out("ESCALATE", "DIRECT_SPAWN_BYPASS_FORBIDDEN")
        return _out("ASSIGN", "AUTHORIZED_MORE_WORK", next_control_intent_ref=intent_ref,
                    next_entrypoint="tools.resolver_spawn.resolve_spawn")
    if incomplete == "WAIT" or executor.get("status") in {"PARTIAL", "BLOCKED"}:
        return _out("WAIT", "AUTHORIZED_WORK_PENDING")
    return _out("ESCALATE", "UNRESOLVED_RESULT_STATE")


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve one local structured post-spawn control bundle")
    parser.add_argument("bundle", nargs="?", help="JSON bundle path; stdin when omitted")
    args = parser.parse_args()
    try:
        with (open(args.bundle, encoding="utf-8") if args.bundle else sys.stdin) as source:
            bundle = json.load(source)
        result = resolve_transition(bundle)
    except (OSError, json.JSONDecodeError) as exc:
        result = _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=[str(exc)])
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result.get("control_state") in BATONS else 1


if __name__ == "__main__":
    raise SystemExit(main())
