#!/usr/bin/env python3
"""Bundle-local composition of governed post-spawn Control Director artifacts."""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.executability import (
    validate_assignment_execution_contract,
    validate_capability_profile,
    validate_director_decision,
    validate_execution_route,
    validate_executor_result,
    validate_state_observation,
    validate_verification_result,
)

BATONS = {"ASSIGN", "WAIT", "ESCALATE", "COMPLETE"}
VERIFICATION_SEVERITY = {"CONFIRMED": 0, "QUALIFIED": 1, "NOT_PROVEN": 2, "BLOCKED": 3}


def _out(state: str, reason: str, **details: object) -> dict[str, object]:
    return {"status": state, "control_state": state, "reason": reason, **details}


def _artifacts(value: object) -> tuple[dict[str, Mapping[str, object]], list[str]]:
    if not isinstance(value, list):
        return {}, ["artifacts must be a list"]
    found: dict[str, Mapping[str, object]] = {}
    errors: list[str] = []
    for index, artifact in enumerate(value):
        if not isinstance(artifact, Mapping):
            errors.append(f"artifacts[{index}] must be an object")
            continue
        artifact_id = artifact.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id.strip():
            errors.append(f"artifacts[{index}].artifact_id must be non-empty")
        elif artifact_id in found:
            errors.append(f"duplicate artifact_id: {artifact_id}")
        else:
            found[artifact_id] = artifact
    return found, errors


def _proof_problem(
    proof: Mapping[str, object],
    assignment: Mapping[str, object],
    artifacts: Mapping[str, Mapping[str, object]],
) -> tuple[str, str] | None:
    if proof.get("artifact_type") != "ASSIGNMENT_ADMISSIBILITY" or proof.get("status") != "ADMISSIBLE":
        return "ESCALATE", "INVALID_PROOF_CLASS"
    contract = assignment.get("execution_contract")
    lifecycle = proof.get("transition_proof")
    if not isinstance(contract, Mapping) or not isinstance(lifecycle, Mapping):
        return "ESCALATE", "MALFORMED_PROOF_LIFECYCLE"
    expected = {
        "proof_class": "ASSIGNMENT_ADMISSION",
        "proof_status": "PROVEN",
        "assignment_ref": assignment.get("artifact_id"),
        "admissibility_ref": proof.get("artifact_id"),
        "destination_id": contract.get("destination_id"),
        "runtime_identity": contract.get("runtime_identity"),
    }
    if any(lifecycle.get(field) != value for field, value in expected.items()):
        return "ESCALATE", "PROOF_CHAIN_IDENTITY_MISMATCH"
    if contract.get("admissibility_ref") != proof.get("artifact_id"):
        return "ESCALATE", "PROOF_CHAIN_IDENTITY_MISMATCH"
    bindings = lifecycle.get("dependency_bindings")
    if not isinstance(bindings, list) or not bindings:
        return "ESCALATE", "MALFORMED_PROOF_LIFECYCLE"
    for binding in bindings:
        if not isinstance(binding, Mapping):
            return "ESCALATE", "MALFORMED_PROOF_LIFECYCLE"
        ref, identity = binding.get("dependency_ref"), binding.get("proven_identity")
        current = artifacts.get(ref) if isinstance(ref, str) else None
        if not isinstance(current, Mapping) or validate_state_observation(current):
            return "ESCALATE", "UNAUTHORIZED_PROOF_DEPENDENCY"
        if current.get("state_identity") != identity:
            return "WAIT", "RELEVANT_PROOF_STALE"
    return None


def _incomplete(authority: Mapping[str, object], artifacts: Mapping[str, Mapping[str, object]], assignment_id: object) -> dict[str, object]:
    outcome = authority.get("incomplete_outcome")
    if outcome == "ASSIGN":
        ref = authority.get("next_control_intent_ref")
        intent = artifacts.get(ref) if isinstance(ref, str) else None
        if not isinstance(intent, Mapping) or intent.get("artifact_type") != "CONTROL_INTENT" or intent.get("assignment_id") != assignment_id:
            return _out("ESCALATE", "NEXT_ASSIGN_AUTHORITY_MISSING")
        if any(field in intent for field in ("assignment", "assignment_id_to_issue", "spawn_ready")):
            return _out("ESCALATE", "DIRECT_SPAWN_BYPASS_FORBIDDEN")
        return _out("ASSIGN", "AUTHORIZED_MORE_WORK", next_control_intent_ref=ref,
                    next_entrypoint="tools.resolver_spawn.resolve_spawn")
    if outcome == "WAIT":
        return _out("WAIT", "AUTHORIZED_REQUIREMENT_PENDING")
    return _out("ESCALATE", "AUTHORIZED_MATERIAL_CONFLICT")


def _effective_verification_outcome(
    aggregate_status: str,
    target_claim_ids: set[str],
    verdicts: Mapping[str, str],
) -> str:
    """Return the weakest governed verification outcome across aggregate and required claims."""
    outcomes = [aggregate_status, *(verdicts[claim_id] for claim_id in target_claim_ids)]
    return max(outcomes, key=VERIFICATION_SEVERITY.__getitem__)


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
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT")
    for field in ("current_state_ref", "prior_director_decision_ref", "assignment_ref", "executor_result_ref"):
        if not isinstance(refs.get(field), str) or not refs[field]:
            return _out("WAIT", "EXECUTOR_RESULT_PENDING") if field == "executor_result_ref" else _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT")

    current = artifacts.get(refs["current_state_ref"])
    director = artifacts.get(refs["prior_director_decision_ref"])
    assignment = artifacts.get(refs["assignment_ref"])
    executor = artifacts.get(refs["executor_result_ref"])
    if not isinstance(current, Mapping) or validate_state_observation(current):
        return _out("ESCALATE", "MALFORMED_STATE_OBSERVATION")
    if not isinstance(director, Mapping) or (errors := validate_director_decision(director)):
        return _out("ESCALATE", "MALFORMED_DIRECTOR_DECISION", errors=errors if isinstance(director, Mapping) else [])
    if not isinstance(executor, Mapping):
        return _out("WAIT", "EXECUTOR_RESULT_PENDING")
    if errors := validate_executor_result(executor):
        return _out("ESCALATE", "MALFORMED_EXECUTOR_RESULT", errors=errors)

    authority = director["transition_authority"]
    assignment_id = assignment.get("assignment_id") if isinstance(assignment, Mapping) else None
    if (not isinstance(assignment, Mapping) or authority.get("assignment_ref") != assignment.get("artifact_id")
            or director.get("assignment_id") != assignment_id or executor.get("assignment_id") != assignment_id
            or executor.get("input_state_ref") != assignment.get("input_state_ref")
            or director.get("executor_result_ref") != executor.get("artifact_id")):
        return _out("ESCALATE", "CONTROL_POINT_IDENTITY_MISMATCH")
    if current.get("artifact_id") not in executor.get("resulting_state_refs", []):
        return _out("ESCALATE", "CURRENT_STATE_IDENTITY_MISMATCH")

    contract = assignment.get("execution_contract")
    proof_ref = contract.get("admissibility_ref") if isinstance(contract, Mapping) else None
    profile_ref = contract.get("capability_profile_ref") if isinstance(contract, Mapping) else None
    route_ref = contract.get("route_ref") if isinstance(contract, Mapping) else None
    compiled_ref = contract.get("compiled_assignment_ref") if isinstance(contract, Mapping) else None
    proof, profile, route, compiled = (artifacts.get(ref) for ref in (proof_ref, profile_ref, route_ref, compiled_ref))
    if not all(isinstance(item, Mapping) for item in (proof, profile, route, compiled)):
        return _out("ESCALATE", "ASSIGNMENT_PROOF_CHAIN_UNRESOLVED")
    profiles = {key: value for key, value in artifacts.items() if value.get("artifact_type") == "CAPABILITY_PROFILE"}
    route_errors = validate_execution_route(route, profiles, artifacts.get)
    chain_errors = validate_assignment_execution_contract(
        assignment, proof, profile, artifacts.get, route, profiles, compiled, artifacts.get,
    )
    if route_errors or chain_errors:
        return _out("ESCALATE", "INVALID_GOVERNED_ASSIGNMENT", errors=route_errors + chain_errors)

    required_proofs = authority.get("required_proof_refs", [])
    if required_proofs != [proof_ref]:
        return _out("ESCALATE", "PROOF_CHAIN_IDENTITY_MISMATCH")
    if problem := _proof_problem(proof, assignment, artifacts):
        return _out(*problem, proof_ref=proof_ref)

    if authority.get("requires_current_executability"):
        current_profile_ref = refs.get("current_capability_profile_ref")
        current_profile = artifacts.get(current_profile_ref) if isinstance(current_profile_ref, str) else None
        if not isinstance(current_profile, Mapping) or (errors := validate_capability_profile(current_profile, artifacts.get)):
            return _out("WAIT", "CURRENT_EXECUTABILITY_REVALIDATION_REQUIRED", errors=errors if isinstance(current_profile, Mapping) else [])
        if (current_profile.get("destination_id") != contract.get("destination_id")
                or current_profile.get("runtime_identity") != contract.get("runtime_identity")):
            return _out("ESCALATE", "CURRENT_PROFILE_EXECUTION_SURFACE_MISMATCH")
        missing = sorted(set(contract.get("required_capabilities", [])) - set(current_profile.get("available_capabilities", [])))
        if missing:
            return _out("WAIT", "BLOCKED_RUNTIME_DRIFT", missing_capabilities=missing)

    verification = None
    if authority.get("verification_required"):
        verification_ref = refs.get("verification_result_ref")
        if not isinstance(verification_ref, str) or verification_ref not in artifacts:
            return _out("WAIT", "VERIFICATION_RESULT_PENDING")
        verification = artifacts[verification_ref]
        if errors := validate_verification_result(verification):
            return _out("ESCALATE", "MALFORMED_VERIFICATION_RESULT", errors=errors)
        if (director.get("verification_result_ref") != verification_ref
                or verification.get("assignment_id") != assignment_id
                or verification.get("executor_result_ref") != executor.get("artifact_id")
                or verification.get("input_state_ref") != executor.get("input_state_ref")):
            return _out("ESCALATE", "VERIFICATION_RESULT_IDENTITY_MISMATCH")

    claims = {claim["claim_id"]: claim for claim in executor["claims"]}
    factual_requirements_met = True
    for requirement in authority["acceptance_requirements"]:
        claim = claims.get(requirement["claim_id"])
        required_evidence = set(requirement["required_evidence_refs"])
        if not isinstance(claim, Mapping) or not required_evidence.issubset(set(claim.get("evidence_refs", []))) \
                or not required_evidence.issubset(set(executor.get("evidence_refs", []))):
            factual_requirements_met = False

    if verification is not None:
        target_ids = set(authority["verification_target_claim_ids"])
        verdicts = {item["claim_id"]: item["verdict"] for item in verification["claim_verdicts"]}
        if target_ids != set(claims).intersection(target_ids) or target_ids - set(verdicts):
            return _out("ESCALATE", "VERIFICATION_TARGET_IDENTITY_MISMATCH")
        effective_outcome = _effective_verification_outcome(verification["status"], target_ids, verdicts)
        mapped = authority["verification_outcome_map"].get(effective_outcome)
        if mapped not in BATONS or effective_outcome not in authority["allowed_verification_outcomes"]:
            return _incomplete(authority, artifacts, assignment_id)
        if mapped != "COMPLETE":
            return _out(mapped, "AUTHORIZED_VERIFICATION_OUTCOME", verification_outcome=effective_outcome)

    if factual_requirements_met and executor.get("status") == "COMPLETE":
        return _out("COMPLETE", "DIRECTOR_ACCEPTANCE_CONDITION_SATISFIED")
    return _incomplete(authority, artifacts, assignment_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve one local structured post-spawn control bundle")
    parser.add_argument("bundle", nargs="?", help="JSON bundle path; stdin when omitted")
    args = parser.parse_args()
    try:
        with (open(args.bundle, encoding="utf-8") if args.bundle else sys.stdin) as source:
            result = resolve_transition(json.load(source))
    except (OSError, json.JSONDecodeError) as exc:
        result = _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=[str(exc)])
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result.get("control_state") in BATONS else 1


if __name__ == "__main__":
    raise SystemExit(main())
