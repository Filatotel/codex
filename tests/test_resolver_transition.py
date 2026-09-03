from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_executability import valid_chain
from tools.resolver_transition import resolve_transition

ROOT = Path(__file__).resolve().parents[1]


def bundle(*, engine="production/software", verification=True, complete=True):
    assignment, admission, profile = deepcopy(valid_chain())
    assignment.update({"artifact_id": "ASSIGN-1", "assignment_id": "ASSIGN-1", "input_state_ref": "STATE-INPUT",
                       "related_artifacts": ["ADM-1", "STATE-INPUT"]})
    assignment["execution_contract"]["required_capabilities"] = ["python_runtime"]
    assignment["execution_contract"]["runtime_identity"] = profile["runtime_identity"]
    admission.update({"artifact_id": "ADM-1", "assignment_id": "ASSIGN-1", "transition_proof": {
        "dependency_bindings": [{"dependency_ref": "STATE-INPUT", "proven_identity": "sha:input"}]}})
    profile["artifact_id"] = "PROFILE-CURRENT"
    current = {"artifact_type": "STATE", "artifact_id": "STATE-CURRENT", "state_identity": "sha:result", "engine_id": engine}
    input_state = {"artifact_type": "STATE", "artifact_id": "STATE-INPUT", "state_identity": "sha:input"}
    result = {
        "artifact_type": "EXECUTOR_RESULT", "artifact_id": "RESULT-1", "produced_by_role": "executor",
        "assignment_id": "ASSIGN-1", "input_state_ref": "STATE-INPUT", "status": "COMPLETE" if complete else "PARTIAL",
        "provenance": ["ASSIGN-1"], "related_artifacts": ["ASSIGN-1"], "resulting_state_refs": ["STATE-CURRENT"],
        "evidence_refs": ["EVIDENCE-1"], "deferred_findings": [], "limitations": [],
        "claims": [{"claim_id": "claim-accepted", "claim": "Bounded acceptance claim",
                    "acceptance_status": "SATISFIED" if complete else "NOT_SATISFIED",
                    "acceptance_requirement_ids": ["acceptance-1"], "engine_semantics": engine}],
    }
    verification_result = {
        "artifact_type": "VERIFICATION_RESULT", "artifact_id": "VERIFY-1", "produced_by_role": "control-verifier",
        "assignment_id": "ASSIGN-1", "input_state_ref": "STATE-INPUT", "status": "CONFIRMED",
        "provenance": ["RESULT-1"], "related_artifacts": ["RESULT-1"], "executor_result_ref": "RESULT-1",
        "claim_verdicts": [{"claim_id": "claim-accepted", "verdict": "CONFIRMED", "evidence_refs": ["EVIDENCE-1"]}],
        "additional_findings": [], "evidence_gaps": [],
    }
    director = {
        "artifact_type": "DIRECTOR_DECISION", "artifact_id": "DIRECTOR-1", "produced_by_role": "control-director",
        "assignment_id": "ASSIGN-1", "input_state_ref": "STATE-INPUT", "transition_authority": {
            "acceptance_requirements": [{"requirement_id": "acceptance-1", "claim_id": "claim-accepted", "required": True}],
            "verification_required": verification, "required_proof_refs": ["ADM-1"],
            "requires_current_executability": False, "incomplete_transition": "WAIT",
        },
    }
    capability_evidence = deepcopy(profile["evidence_artifacts"][0])
    artifacts = [current, input_state, director, assignment, admission, profile, result, verification_result, capability_evidence]
    return {"refs": {"current_state_ref": "STATE-CURRENT", "prior_director_decision_ref": "DIRECTOR-1",
                     "assignment_ref": "ASSIGN-1", "executor_result_ref": "RESULT-1",
                     "verification_result_ref": "VERIFY-1", "current_capability_profile_ref": "PROFILE-CURRENT"},
            "artifacts": artifacts}


class ResolverTransitionTest(unittest.TestCase):
    def test_t1_verified_complete_software(self):
        self.assertEqual(resolve_transition(bundle())["control_state"], "COMPLETE")

    def test_t2_verification_pending_and_no_executor_substitution(self):
        value = bundle(); value["refs"].pop("verification_result_ref")
        result = resolve_transition(value)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "VERIFICATION_RESULT_PENDING"))

    def test_t3_more_authorized_work_returns_assign_without_assignment(self):
        value = bundle(verification=False, complete=False)
        intent = {"artifact_type": "CONTROL_INTENT", "artifact_id": "INTENT-1", "assignment_id": "ASSIGN-1", "next_action": "compile next authorized work"}
        value["artifacts"].append(intent)
        authority = value["artifacts"][2]["transition_authority"]
        authority.update({"incomplete_transition": "ASSIGN", "next_control_intent_ref": "INTENT-1"})
        result = resolve_transition(value)
        self.assertEqual(result["control_state"], "ASSIGN")
        self.assertEqual(result["next_entrypoint"], "tools.resolver_spawn.resolve_spawn")
        self.assertNotIn("assignment", result)

    def test_t4_material_contradiction(self):
        value = bundle(); value["artifacts"][7]["claim_verdicts"][0]["verdict"] = "NOT_PROVEN"
        value["artifacts"][7]["status"] = "NOT_PROVEN"
        self.assertEqual(resolve_transition(value)["control_state"], "ESCALATE")

    def test_l1_relevant_dependency_change(self):
        value = bundle(); value["artifacts"][1]["state_identity"] = "sha:changed"
        result = resolve_transition(value)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "RELEVANT_PROOF_STALE"))

    def test_l2_unrelated_state_change_is_selective(self):
        value = bundle(); value["artifacts"].append({"artifact_type": "STATE", "artifact_id": "UNRELATED", "state_identity": "sha:new"})
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_l3_runtime_capability_drift(self):
        value = bundle(verification=False, complete=False)
        value["artifacts"][2]["transition_authority"]["requires_current_executability"] = True
        value["artifacts"][3]["execution_contract"]["required_capabilities"].append("database_access")
        result = resolve_transition(value)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "BLOCKED_RUNTIME_DRIFT"))

    def test_research_machine_only_result_semantics(self):
        value = bundle(engine="research")
        value["artifacts"][6]["claims"][0].update({"engine_semantics": "research", "research_status": "SUPPORTED", "machine_only": True})
        value["artifacts"][2]["transition_authority"]["research_admission"] = "MACHINE_ONLY_ADMITTED"
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_verification_engine_claim_target_semantics(self):
        value = bundle(engine="verification")
        value["artifacts"][6]["claims"][0].update({"engine_semantics": "verification", "exact_claim_target_ref": "candidate:sha:result"})
        value["artifacts"][7]["claim_verdicts"][0]["exact_claim_target_ref"] = "candidate:sha:result"
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_n1_missing_executor_waits_and_verifier_cannot_substitute(self):
        value = bundle(); value["refs"].pop("executor_result_ref")
        self.assertEqual(resolve_transition(value)["reason"], "EXECUTOR_RESULT_PENDING")

    def test_n2_assignment_and_n4_verification_identity_mismatch(self):
        value = bundle(); value["artifacts"][6]["assignment_id"] = "OTHER"
        self.assertEqual(resolve_transition(value)["reason"], "EXECUTOR_RESULT_IDENTITY_MISMATCH")
        value = bundle(); value["artifacts"][7]["executor_result_ref"] = "OTHER"
        self.assertEqual(resolve_transition(value)["reason"], "VERIFICATION_RESULT_IDENTITY_MISMATCH")

    def test_n5_malformed_result(self):
        value = bundle(); del value["artifacts"][6]["claims"]
        self.assertEqual(resolve_transition(value)["reason"], "MALFORMED_EXECUTOR_RESULT")

    def test_n9_missing_acceptance_semantics(self):
        value = bundle(); del value["artifacts"][2]["transition_authority"]
        self.assertEqual(resolve_transition(value)["reason"], "MISSING_ACCEPTANCE_SEMANTICS")

    def test_n10_duplicate_artifact_identity(self):
        value = bundle(); value["artifacts"].append(deepcopy(value["artifacts"][0]))
        self.assertEqual(resolve_transition(value)["reason"], "CONTRADICTORY_CONTROL_ARTIFACTS")

    def test_n11_assign_without_authority_and_n12_spawn_bypass(self):
        value = bundle(verification=False, complete=False)
        value["artifacts"][2]["transition_authority"]["incomplete_transition"] = "ASSIGN"
        self.assertEqual(resolve_transition(value)["reason"], "NEXT_ASSIGN_AUTHORITY_MISSING")
        value["artifacts"].append({"artifact_type": "CONTROL_INTENT", "artifact_id": "BAD", "assignment_id": "ASSIGN-1", "assignment": {}})
        value["artifacts"][2]["transition_authority"]["next_control_intent_ref"] = "BAD"
        self.assertEqual(resolve_transition(value)["reason"], "DIRECT_SPAWN_BYPASS_FORBIDDEN")

    def test_cli_local_json(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as handle:
            json.dump(bundle(), handle); handle.flush()
            completed = subprocess.run([sys.executable, str(ROOT / "tools/resolver_transition.py"), handle.name],
                                       check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(completed.stdout)["control_state"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
