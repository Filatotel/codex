from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_resolver_spawn import bundle as spawn_bundle
from tools.resolver_spawn import resolve_spawn
from tools.resolver_transition import resolve_transition

ROOT = Path(__file__).resolve().parents[1]


def transition_bundle(*, verification=True, incomplete="WAIT", verification_status="CONFIRMED"):
    pre_spawn = spawn_bundle()
    spawned = resolve_spawn(pre_spawn)
    if spawned.get("status") != "SPAWN_READY":
        raise AssertionError(spawned)
    assignment = spawned["assignment"]
    admission = spawned["assignment_admissibility"]
    result = {
        "artifact_type": "EXECUTOR_RESULT", "artifact_id": "RESULT-1", "produced_by_role": "executor",
        "assignment_id": assignment["assignment_id"], "input_state_ref": assignment["input_state_ref"], "status": "COMPLETE",
        "provenance": [assignment["artifact_id"]], "related_artifacts": [assignment["artifact_id"]],
        "resulting_state_refs": ["STATE-RESULT"], "evidence_refs": ["EVIDENCE-RESULT"],
        "deferred_findings": [], "limitations": [],
        "claims": [{"claim_id": "claim-result", "claim": "The required output was produced.",
                    "evidence_refs": ["EVIDENCE-RESULT"]}],
    }
    verification_result = {
        "artifact_type": "VERIFICATION_RESULT", "artifact_id": "VERIFY-1", "produced_by_role": "control-verifier",
        "assignment_id": assignment["assignment_id"], "input_state_ref": assignment["input_state_ref"],
        "status": verification_status, "provenance": [result["artifact_id"]],
        "related_artifacts": [result["artifact_id"]], "executor_result_ref": result["artifact_id"],
        "claim_verdicts": [{"claim_id": "claim-result", "verdict": verification_status if verification_status != "BLOCKED" else "NOT_PROVEN",
                            "evidence_refs": ["EVIDENCE-RESULT"]}], "additional_findings": [], "evidence_gaps": [],
    }
    outcome_map = {"CONFIRMED": "COMPLETE", "QUALIFIED": "WAIT", "NOT_PROVEN": incomplete, "BLOCKED": "WAIT"}
    director = {
        "artifact_type": "DIRECTOR_DECISION", "artifact_id": "DIRECTOR-POST", "produced_by_role": "control-director",
        "assignment_id": assignment["assignment_id"], "input_state_ref": assignment["input_state_ref"], "status": "PENDING",
        "provenance": [assignment["artifact_id"]], "related_artifacts": [assignment["artifact_id"], admission["artifact_id"]],
        "executor_result_ref": result["artifact_id"], "verification_result_ref": verification_result["artifact_id"] if verification else None,
        "control_state": "WAIT", "decision": "Reconcile the structured post-spawn control point.", "next_owner": "control-director",
        "transition_authority": {
            "transition_id": "TRANSITION-1", "assignment_ref": assignment["artifact_id"],
            "acceptance_requirements": [{"requirement_id": "acceptance-output", "claim_id": "claim-result",
                                         "required_evidence_refs": ["EVIDENCE-RESULT"]}],
            "verification_required": verification,
            "verification_target_claim_ids": ["claim-result"] if verification else [],
            "allowed_verification_outcomes": ["CONFIRMED", "QUALIFIED", "NOT_PROVEN", "BLOCKED"] if verification else [],
            "verification_outcome_map": outcome_map if verification else {},
            "incomplete_outcome": incomplete, "next_control_intent_ref": None,
            "required_proof_refs": [admission["artifact_id"]], "requires_current_executability": False,
        },
    }
    current = {"artifact_type": "STATE_OBSERVATION", "artifact_id": "STATE-RESULT", "produced_by_role": "control-director",
               "input_state_ref": assignment["input_state_ref"], "status": "CURRENT", "provenance": [result["artifact_id"]],
               "related_artifacts": [result["artifact_id"]], "state_identity": "git:result", "authority_scope": "transition-result"}
    artifacts = deepcopy(pre_spawn["artifacts"]) + [spawned["compiled_assignment"], admission, assignment, result, director, current]
    if verification:
        artifacts.append(verification_result)
    return {"refs": {"current_state_ref": current["artifact_id"], "prior_director_decision_ref": director["artifact_id"],
                     "assignment_ref": assignment["artifact_id"], "executor_result_ref": result["artifact_id"],
                     "verification_result_ref": verification_result["artifact_id"] if verification else None,
                     "current_capability_profile_ref": spawned["capability_profile_ref"]},
            "artifacts": artifacts, "spawned": spawned}


def artifact(value, artifact_id):
    return next(item for item in value["artifacts"] if item.get("artifact_id") == artifact_id)


class ResolverTransitionTest(unittest.TestCase):
    def test_real_spawn_output_flows_into_transition(self):
        value = transition_bundle()
        self.assertEqual(value["spawned"]["status"], "SPAWN_READY")
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_spawn_materializes_deterministic_selective_lifecycle(self):
        first, second = resolve_spawn(spawn_bundle()), resolve_spawn(spawn_bundle())
        self.assertEqual(first["assignment_admissibility"]["transition_proof"], second["assignment_admissibility"]["transition_proof"])
        proof = first["assignment_admissibility"]["transition_proof"]
        self.assertEqual(proof["assignment_ref"], first["assignment"]["artifact_id"])
        self.assertEqual(proof["admissibility_ref"], first["assignment_admissibility"]["artifact_id"])
        self.assertEqual(proof["dependency_bindings"], [{"dependency_ref": "STATE-OBS-1", "proven_identity": "git:input-state"}])

    def test_l1_real_proof_relevant_change(self):
        value = transition_bundle(); artifact(value, "STATE-OBS-1")["state_identity"] = "git:changed"
        self.assertEqual(resolve_transition(value)["reason"], "RELEVANT_PROOF_STALE")

    def test_l2_real_proof_unrelated_change(self):
        value = transition_bundle(); value["artifacts"].append({"artifact_type": "STATE_OBSERVATION", "artifact_id": "UNRELATED",
            "produced_by_role": "control-director", "input_state_ref": None, "status": "CURRENT", "provenance": [],
            "related_artifacts": [], "state_identity": "other", "authority_scope": "unrelated"})
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def _current_profile(self, value, *, destination=None, remove_capability=None):
        old = artifact(value, value["spawned"]["capability_profile_ref"])
        profile = deepcopy(old); profile["artifact_id"] = "PROFILE-NOW"
        evidence = deepcopy(profile["evidence_artifacts"][0]); evidence["artifact_id"] = "EVIDENCE-NOW"
        profile["evidence_artifacts"] = [evidence]; profile["related_artifacts"] = [evidence["artifact_id"]]
        for item in profile["capability_evidence"]: item["evidence_ref"] = evidence["artifact_id"]
        if destination is not None: profile["destination_id"] = destination
        if remove_capability:
            profile["available_capabilities"].remove(remove_capability); profile["unavailable_capabilities"].append(remove_capability)
            profile["capability_evidence"] = [item for item in profile["capability_evidence"] if item["capability"] != remove_capability]
            evidence["capabilities"].remove(remove_capability)
        value["artifacts"].extend([profile, evidence]); value["refs"]["current_capability_profile_ref"] = profile["artifact_id"]
        artifact(value, "DIRECTOR-POST")["transition_authority"]["requires_current_executability"] = True

    def test_l3_real_proof_runtime_drift(self):
        value = transition_bundle(); self._current_profile(value, remove_capability="shell")
        result = resolve_transition(value)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "BLOCKED_RUNTIME_DRIFT"))

    def test_l4_wrong_destination_profile(self):
        value = transition_bundle(); self._current_profile(value, destination="other-destination")
        self.assertEqual(resolve_transition(value)["reason"], "CURRENT_PROFILE_EXECUTION_SURFACE_MISMATCH")

    def test_executor_cannot_self_certify_acceptance(self):
        value = transition_bundle(verification=False, incomplete="WAIT")
        result = artifact(value, "RESULT-1"); result["acceptance_status"] = "SATISFIED"
        result["claims"][0]["evidence_refs"] = []
        self.assertEqual(resolve_transition(value)["control_state"], "WAIT")

    def test_missing_required_verification_waits(self):
        value = transition_bundle(); value["refs"]["verification_result_ref"] = None
        self.assertEqual(resolve_transition(value)["reason"], "VERIFICATION_RESULT_PENDING")

    def test_verifier_cannot_replace_executor(self):
        value = transition_bundle(); value["refs"]["executor_result_ref"] = None
        self.assertEqual(resolve_transition(value)["reason"], "EXECUTOR_RESULT_PENDING")

    def test_not_proven_baton_is_director_owned(self):
        waiting = transition_bundle(verification_status="NOT_PROVEN", incomplete="WAIT")
        self.assertEqual(resolve_transition(waiting)["control_state"], "WAIT")
        escalating = transition_bundle(verification_status="NOT_PROVEN", incomplete="ESCALATE")
        self.assertEqual(resolve_transition(escalating)["control_state"], "ESCALATE")

    def test_malformed_director_and_non_proven_assignment_fail(self):
        value = transition_bundle(); del artifact(value, "DIRECTOR-POST")["decision"]
        self.assertEqual(resolve_transition(value)["reason"], "MALFORMED_DIRECTOR_DECISION")
        value = transition_bundle(); artifact(value, "ASSIGN-RESOLVED")["execution_contract"]["proof_status"] = "UNPROVEN"
        self.assertEqual(resolve_transition(value)["reason"], "INVALID_GOVERNED_ASSIGNMENT")

    def test_arbitrary_proof_and_wrong_admission_ref_fail(self):
        value = transition_bundle(); admission = artifact(value, "ADM-RESOLVED"); admission["artifact_type"] = "OTHER_PROOF"
        self.assertIn(resolve_transition(value)["reason"], {"INVALID_GOVERNED_ASSIGNMENT", "INVALID_PROOF_CLASS"})
        value = transition_bundle(); artifact(value, "ASSIGN-RESOLVED")["execution_contract"]["admissibility_ref"] = "OTHER"
        self.assertEqual(resolve_transition(value)["reason"], "ASSIGNMENT_PROOF_CHAIN_UNRESOLVED")

    def test_assign_fence(self):
        value = transition_bundle(verification=False, incomplete="ASSIGN")
        intent = {"artifact_type": "CONTROL_INTENT", "artifact_id": "INTENT-1",
                  "assignment_id": "ASSIGN-RESOLVED", "next_action": "run pre-spawn composition"}
        value["artifacts"].append(intent); artifact(value, "DIRECTOR-POST")["transition_authority"]["next_control_intent_ref"] = "INTENT-1"
        artifact(value, "RESULT-1")["claims"][0]["evidence_refs"] = []
        result = resolve_transition(value)
        self.assertEqual(result["next_entrypoint"], "tools.resolver_spawn.resolve_spawn")
        self.assertNotIn("assignment", result)

    def test_cli_reads_local_json(self):
        value = transition_bundle(); value.pop("spawned")
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as handle:
            json.dump(value, handle); handle.flush()
            completed = subprocess.run([sys.executable, str(ROOT / "tools/resolver_transition.py"), handle.name], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(completed.stdout)["control_state"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
