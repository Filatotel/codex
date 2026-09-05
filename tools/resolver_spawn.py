#!/usr/bin/env python3
"""Thin, bundle-local composition of governed pre-spawn control artifacts."""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from copy import deepcopy
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.assignment_compiler import compile_assignment, validate_compiled_assignment
from tools.executability import (
    evaluate_assignment_admissibility,
    validate_admissibility_against_profile,
    validate_assignment_execution_contract,
    validate_capability_profile,
    validate_execution_route,
    validate_state_observation,
)
from tools.research_policy import admit_work_package

TERMINAL_STATES = {"WAIT", "ESCALATE", "COMPLETE"}
SEMANTIC_FIELDS = ("objective", "authority", "scope", "acceptance", "stop_conditions", "result_to")
RESEARCH_POLICY_SURFACE = "tools.research_policy.admit_work_package"
RESEARCH_RESULT_FIELDS = {"ADMISSION_STATUS", "ERROR_CODE", "REQUIRE_MACHINE_REDESIGN", "ERRORS"}
RESEARCH_ADMISSION_FIELDS = {
    "artifact_id", *RESEARCH_RESULT_FIELDS, "WORK_PACKAGE_ID", "QUESTION_ID", "POLICY_SURFACE", "PROVENANCE", "WORK_PACKAGE",
}


def _out(control_state: str, reason: str, **details: object) -> dict[str, object]:
    return {"status": control_state, "control_state": control_state, "reason": reason, **details}


def _artifact_resolver(artifacts: object):
    if not isinstance(artifacts, list):
        return None, {}, ["artifacts must be a list"]
    by_id: dict[str, Mapping[str, object]] = {}
    errors: list[str] = []
    for index, item in enumerate(artifacts):
        if not isinstance(item, Mapping):
            errors.append(f"artifacts[{index}] must be an object")
            continue
        artifact_id = item.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id.strip():
            errors.append(f"artifacts[{index}].artifact_id must be a non-empty string")
            continue
        if artifact_id in by_id:
            errors.append(f"duplicate artifact_id: {artifact_id}")
            continue
        by_id[artifact_id] = item
    return by_id.get, by_id, errors


def _profile_is_only_stale(errors: list[str]) -> bool:
    """Classify freshness failures already reported by the authoritative validator."""
    return bool(errors) and all("expired" in error for error in errors)


def _valid_prerequisites(value: object) -> tuple[list[dict[str, object]], list[str]]:
    if not isinstance(value, list):
        return [], ["selected_prerequisite_actions must be a list"]
    actions, errors = [], []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            errors.append(f"selected_prerequisite_actions[{index}] must be an object")
            continue
        action = deepcopy(dict(item))
        if not isinstance(action.get("action_id"), str) or not action["action_id"].strip():
            errors.append(f"selected_prerequisite_actions[{index}].action_id must be non-empty")
        capabilities = action.get("required_capabilities")
        if not isinstance(capabilities, list) or not all(isinstance(cap, str) and cap.strip() for cap in capabilities):
            errors.append(f"selected_prerequisite_actions[{index}].required_capabilities must be a string list")
        evidence = action.get("evidence_path")
        if evidence is not None and (not isinstance(evidence, str) or not evidence.strip()):
            errors.append(f"selected_prerequisite_actions[{index}].evidence_path must be null or non-empty")
        actions.append(action)
    return actions, errors


def _research_admission(
    decision: Mapping[str, object],
    artifacts: Mapping[str, Mapping[str, object]],
) -> tuple[Mapping[str, object] | None, dict[str, object] | None]:
    """Revalidate exact Research work through the existing Research policy surface."""
    admission_ref = decision.get("research_admission_ref")
    if not isinstance(admission_ref, str) or not admission_ref.strip():
        return None, _out("ESCALATE", "RESEARCH_ADMISSION_REQUIRED", engine_id="research")
    selected_work_id = decision.get("research_work_package_id")
    selected_question_id = decision.get("research_question_id")
    if not isinstance(selected_work_id, str) or not selected_work_id.strip() or not isinstance(selected_question_id, str) or not selected_question_id.strip():
        return None, _out("ESCALATE", "RESEARCH_WORK_IDENTITY_REQUIRED", engine_id="research")

    admission = artifacts.get(admission_ref)
    if not isinstance(admission, Mapping):
        return None, _out("ESCALATE", "RESEARCH_ADMISSION_UNRESOLVED", engine_id="research", research_admission_ref=admission_ref)
    if set(admission) != RESEARCH_ADMISSION_FIELDS:
        return None, _out("ESCALATE", "MALFORMED_RESEARCH_ADMISSION", engine_id="research", research_admission_ref=admission_ref)
    if admission.get("artifact_id") != admission_ref or admission.get("POLICY_SURFACE") != RESEARCH_POLICY_SURFACE:
        return None, _out("ESCALATE", "MALFORMED_RESEARCH_ADMISSION", engine_id="research", research_admission_ref=admission_ref)

    work_package = admission.get("WORK_PACKAGE")
    if not isinstance(work_package, Mapping):
        return None, _out("ESCALATE", "MALFORMED_RESEARCH_ADMISSION", engine_id="research", research_admission_ref=admission_ref)
    work_id = work_package.get("WORK_PACKAGE_ID")
    question_id = work_package.get("QUESTION_ID")
    if not isinstance(work_id, str) or not work_id.strip() or not isinstance(question_id, str) or not question_id.strip():
        return None, _out("ESCALATE", "MALFORMED_RESEARCH_ADMISSION", engine_id="research", research_admission_ref=admission_ref)
    if admission.get("WORK_PACKAGE_ID") != work_id or admission.get("QUESTION_ID") != question_id:
        return None, _out("ESCALATE", "RESEARCH_ADMISSION_IDENTITY_MISMATCH", engine_id="research", research_admission_ref=admission_ref)
    if selected_work_id != work_id or selected_question_id != question_id:
        return None, _out("ESCALATE", "RESEARCH_ADMISSION_IDENTITY_MISMATCH", engine_id="research", research_admission_ref=admission_ref)
    if admission.get("PROVENANCE") != [RESEARCH_POLICY_SURFACE, work_id, question_id]:
        return None, _out("ESCALATE", "MALFORMED_RESEARCH_ADMISSION", engine_id="research", research_admission_ref=admission_ref)

    authoritative_result = admit_work_package(dict(work_package))
    carried_result = {field: admission.get(field) for field in RESEARCH_RESULT_FIELDS}
    if carried_result != authoritative_result:
        return None, _out("ESCALATE", "RESEARCH_ADMISSION_RESULT_MISMATCH", engine_id="research", research_admission_ref=admission_ref)
    if authoritative_result.get("ADMISSION_STATUS") != "ADMITTED_MACHINE_RESEARCH":
        return None, _out("ESCALATE", "RESEARCH_ADMISSION_NOT_ADMITTED", engine_id="research", research_admission_ref=admission_ref)
    return admission, None


def resolve_spawn(control_bundle: Mapping[str, object]) -> dict[str, object]:
    """Resolve one already-selected local control bundle to a baton outcome."""
    if not isinstance(control_bundle, Mapping):
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT")
    decision = control_bundle.get("decision")
    if not isinstance(decision, Mapping):
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=["decision must be an object"])
    state = decision.get("control_state")
    if state in TERMINAL_STATES:
        return _out(str(state), "INPUT_CONTROL_STATE_PRESERVED")
    if state != "ASSIGN":
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=["control_state is invalid"])
    for field in ("engine_id", "engine_status", "semantic_capability", "workflow_id"):
        if not isinstance(decision.get(field), str) or not str(decision[field]).strip():
            return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=[f"decision.{field} is required"])
    if decision["engine_status"] != "available":
        reason = "ENGINE_NOT_MATERIALIZED" if decision["engine_status"] == "not_materialized" else "ENGINE_UNAVAILABLE"
        return _out("ESCALATE", reason, engine_id=decision["engine_id"])
    if "additional_required_capabilities" in control_bundle or "final_required_capabilities" in control_bundle:
        return _out("ESCALATE", "UNACCOUNTED_CAPABILITY_EXPANSION")

    resolver, artifacts, artifact_errors = _artifact_resolver(control_bundle.get("artifacts", []))
    if artifact_errors:
        reason = "CONTRADICTORY_CONTROL_ARTIFACTS" if any(error.startswith("duplicate artifact_id:") for error in artifact_errors) else "MALFORMED_CONTROL_ARTIFACT"
        return _out("ESCALATE", reason, errors=artifact_errors)
    research_admission = None
    if decision["engine_id"] == "research":
        research_admission, research_error = _research_admission(decision, artifacts)
        if research_error is not None:
            return research_error

    state_observation_ref = control_bundle.get("input_state_observation_ref")
    state_observation = artifacts.get(state_observation_ref) if isinstance(state_observation_ref, str) else None
    if not isinstance(state_observation, Mapping):
        return _out("ESCALATE", "INPUT_STATE_OBSERVATION_REQUIRED")
    state_errors = validate_state_observation(state_observation)
    if state_errors:
        return _out("ESCALATE", "MALFORMED_STATE_OBSERVATION", errors=state_errors)
    draft = control_bundle.get("assignment_compilation_draft")
    semantics = control_bundle.get("assignment_draft_semantics")
    if not isinstance(draft, Mapping) or not isinstance(semantics, Mapping):
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT")
    missing_semantics = [field for field in SEMANTIC_FIELDS if field not in semantics]
    if missing_semantics:
        return _out("ESCALATE", "MISSING_ASSIGNMENT_SEMANTICS", errors=missing_semantics)
    envelope_ref = control_bundle.get("execution_envelope_ref")
    compiled = compile_assignment(draft, envelope_ref, resolver, resolver) if isinstance(envelope_ref, str) and envelope_ref.strip() else None
    if compiled is None:
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=["execution_envelope_ref is required"])
    if compiled.get("compilation_status") != "COMPILED":
        return _out("ESCALATE", "COMPILE_REJECTED", compilation_errors=compiled.get("compilation_errors", []))
    compiled_errors = validate_compiled_assignment(compiled, resolver, resolver)
    if compiled_errors:
        return _out("ESCALATE", "COMPILED_ASSIGNMENT_INVALID", errors=compiled_errors)

    prerequisites, prerequisite_errors = _valid_prerequisites(control_bundle.get("selected_prerequisite_actions", []))
    if prerequisite_errors:
        return _out("ESCALATE", "MALFORMED_PREREQUISITE_ACTION", errors=prerequisite_errors)
    compiled_actions = [
        deepcopy(item) for item in compiled["authorized_mandatory_actions"]
        if isinstance(item, Mapping) and item.get("responsibility") == "EXECUTOR"
    ]
    compiled_evidence = [
        deepcopy(item) for item in compiled["authorized_evidence_requirements"]
        if isinstance(item, Mapping) and item.get("responsibility") == "EXECUTOR"
    ]
    final_actions = compiled_actions + compiled_evidence + prerequisites
    capability_errors = []
    for index, action in enumerate(final_actions):
        capabilities = action.get("required_capabilities")
        if not isinstance(capabilities, list) or not all(isinstance(cap, str) and cap.strip() for cap in capabilities):
            capability_errors.append(f"final mandatory action[{index}].required_capabilities must be a string list")
    if capability_errors:
        return _out("ESCALATE", "MALFORMED_MANDATORY_ACTION", errors=capability_errors)
    action_ids = [item.get("action_id") for item in final_actions if isinstance(item, Mapping)]
    if len(action_ids) != len(set(action_ids)):
        return _out("ESCALATE", "CONTRADICTORY_CONTROL_ARTIFACTS", errors=["duplicate final mandatory action id"])
    required = sorted({cap.strip() for action in final_actions for cap in action.get("required_capabilities", [])})
    paths = sorted({path for action in final_actions if isinstance((path := action.get("evidence_path")), str) and path.strip()})

    profile_ref, route_ref = control_bundle.get("capability_profile_ref"), control_bundle.get("route_ref")
    invalid_refs = [
        field for field, value in (("capability_profile_ref", profile_ref), ("route_ref", route_ref))
        if not isinstance(value, str) or not value.strip()
    ]
    if invalid_refs:
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=[f"{field} must be a non-empty string" for field in invalid_refs])
    profile, route = artifacts.get(profile_ref), artifacts.get(route_ref)
    if not isinstance(profile, Mapping) or not isinstance(route, Mapping):
        return _out("ESCALATE", "REFERENCE_IDENTITY_MISMATCH")
    profile_errors = validate_capability_profile(profile, resolver)
    if profile_errors:
        state = "WAIT" if _profile_is_only_stale(profile_errors) else "ESCALATE"
        reason = "CAPABILITY_PROFILE_STALE" if state == "WAIT" else "MALFORMED_CAPABILITY_PROFILE"
        return _out(state, reason, errors=profile_errors, capability_profile_ref=profile_ref)
    route_profiles = {key: value for key, value in artifacts.items() if isinstance(value, Mapping) and value.get("artifact_type") == "CAPABILITY_PROFILE"}
    route_errors = validate_execution_route(route, route_profiles, resolver)
    if route_errors:
        return _out("ESCALATE", "EXECUTION_ROUTE_INVALID", errors=route_errors)

    subset = evaluate_assignment_admissibility(required, profile.get("available_capabilities", []))
    research_refs = [str(research_admission["artifact_id"])] if isinstance(research_admission, Mapping) else []
    admissibility = {
        "artifact_type": "ASSIGNMENT_ADMISSIBILITY", "artifact_id": control_bundle.get("admissibility_id"),
        "produced_by_role": "control-director", "assignment_id": control_bundle.get("assignment_id"), "input_state_ref": draft.get("input_state_ref"),
        "status": subset["status"], "provenance": [str(profile_ref)], "related_artifacts": [str(profile_ref), str(route_ref), *research_refs],
        "assignment_draft_id": draft.get("assignment_draft_ref"), "compiled_assignment_ref": compiled.get("artifact_id"),
        "destination_id": profile.get("destination_id"), "runtime_identity": profile.get("runtime_identity"),
        "capability_profile_ref": profile_ref, "route_ref": route_ref, "mandatory_actions": final_actions,
        "required_capabilities": required, "available_capabilities": subset["available_capabilities"],
        "unsatisfied_required_capabilities": subset["unsatisfied_required_capabilities"], "mandatory_evidence_paths": paths,
        "execution_mode": decision.get("execution_mode"),
        "transition_proof": {"proof_class": "ASSIGNMENT_ADMISSION", "proof_status": "PROVEN",
            "assignment_ref": control_bundle.get("assignment_id"), "admissibility_ref": control_bundle.get("admissibility_id"),
            "destination_id": profile.get("destination_id"), "runtime_identity": profile.get("runtime_identity"),
            "dependency_bindings": [{"dependency_ref": state_observation.get("artifact_id"),
                                     "proven_identity": state_observation.get("state_identity")}]},
    }
    admission_errors = validate_admissibility_against_profile(admissibility, profile, resolver)
    if admission_errors:
        return _out("ESCALATE", "ASSIGNMENT_ADMISSIBILITY_INVALID", errors=admission_errors)
    if subset["status"] != "ADMISSIBLE":
        return _out("WAIT", "ASSIGNMENT_NOT_ADMISSIBLE", required_capabilities=required,
                    available_capabilities=subset["available_capabilities"], missing_capabilities=subset["unsatisfied_required_capabilities"],
                    destination_id=profile.get("destination_id"), capability_profile_ref=profile_ref)

    assignment = deepcopy(dict(semantics))
    assignment.update({
        "artifact_type": "ASSIGNMENT", "artifact_id": control_bundle.get("assignment_id"), "produced_by_role": "control-director",
        "assignment_id": control_bundle.get("assignment_id"), "input_state_ref": draft.get("input_state_ref"), "status": "ISSUED",
        "provenance": [str(admissibility["artifact_id"])], "related_artifacts": [str(admissibility["artifact_id"]), str(profile_ref), str(route_ref), *research_refs],
        "execution_contract": {"assignment_draft_ref": draft.get("assignment_draft_ref"), "compiled_assignment_ref": compiled.get("artifact_id"),
            "destination_id": profile.get("destination_id"), "runtime_identity": profile.get("runtime_identity"), "capability_profile_ref": profile_ref,
            "admissibility_ref": admissibility.get("artifact_id"), "route_ref": route_ref, "proof_status": "PROVEN",
            "required_capabilities": required, "unsatisfied_required_capabilities": [], "mandatory_evidence_paths": paths,
            "execution_mode": decision.get("execution_mode")},
    })
    proof_errors = validate_assignment_execution_contract(assignment, admissibility, profile, resolver, route, route_profiles,
                                                           compiled, resolver)
    if proof_errors:
        return _out("ESCALATE", "FINAL_ASSIGNMENT_PROOF_FAILED", errors=proof_errors)
    result = {"status": "SPAWN_READY", "control_state": "ASSIGN", "engine_id": decision["engine_id"],
              "workflow_id": decision["workflow_id"], "compiled_assignment_ref": compiled["artifact_id"],
              "capability_profile_ref": profile_ref, "route_ref": route_ref, "admissibility_ref": admissibility["artifact_id"],
              "assignment_ref": assignment["artifact_id"], "compiled_assignment": compiled,
              "assignment_admissibility": admissibility, "assignment": assignment,
              "capability_profile": profile, "execution_route": route,
              "input_state_observation": state_observation}
    if isinstance(research_admission, Mapping):
        result["research_admission_ref"] = research_admission["artifact_id"]
        result["research_admission"] = research_admission
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve one local structured control bundle to a pre-spawn outcome")
    parser.add_argument("bundle", nargs="?", help="JSON bundle path; stdin when omitted")
    args = parser.parse_args()
    try:
        with (open(args.bundle, encoding="utf-8") if args.bundle else sys.stdin) as source:
            bundle = json.load(source)
        result = resolve_spawn(bundle)
    except (OSError, json.JSONDecodeError) as exc:
        result = _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=[str(exc)])
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result.get("control_state") in {"ASSIGN", "WAIT", "ESCALATE", "COMPLETE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
