from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from tests.test_research_machine_only import base_experiment, base_wp
from tests.test_resolver_spawn import bundle as spawn_bundle
from tools.executability import validate_director_decision
from tools.research_policy import admit_work_package, validate_experiment
from tools.resolver_spawn import resolve_spawn
from tools.resolver_transition import resolve_transition

ROOT = Path(__file__).resolve().parents[1]
BATONS = {"ASSIGN", "WAIT", "ESCALATE", "COMPLETE"}


def artifact(value: dict, artifact_id: str) -> dict:
    return next(item for item in value["artifacts"] if item.get("artifact_id") == artifact_id)


def post_spawn_bundle(
    pre_spawn: dict,
    *,
    verification: bool = True,
    incomplete: str = "WAIT",
    verification_status: str = "CONFIRMED",
    claim_verdict: str | None = None,
) -> dict:
    """Build role-native post-spawn inputs around exact production spawn artifacts.

    This fixture does not decide the baton. It only materializes the structured
    Executor, Verifier, Director-authority, and resulting-state artifacts that the
    production transition entrypoint consumes.
    """
    spawned = resolve_spawn(pre_spawn)
    if spawned.get("status") != "SPAWN_READY":
        raise AssertionError(spawned)

    assignment = spawned["assignment"]
    admission = spawned["assignment_admissibility"]
    result = {
        "artifact_type": "EXECUTOR_RESULT",
        "artifact_id": "RESULT-1",
        "produced_by_role": "executor",
        "assignment_id": assignment["assignment_id"],
        "input_state_ref": assignment["input_state_ref"],
        "status": "COMPLETE",
        "provenance": [assignment["artifact_id"]],
        "related_artifacts": [assignment["artifact_id"]],
        "resulting_state_refs": ["STATE-RESULT"],
        "evidence_refs": ["EVIDENCE-RESULT"],
        "deferred_findings": [],
        "limitations": [],
        "claims": [
            {
                "claim_id": "claim-result",
                "claim": "The authorized bounded output was produced.",
                "evidence_refs": ["EVIDENCE-RESULT"],
            }
        ],
    }

    if claim_verdict is None:
        claim_verdict = verification_status if verification_status != "BLOCKED" else "NOT_PROVEN"
    verification_result = {
        "artifact_type": "VERIFICATION_RESULT",
        "artifact_id": "VERIFY-1",
        "produced_by_role": "control-verifier",
        "assignment_id": assignment["assignment_id"],
        "input_state_ref": assignment["input_state_ref"],
        "status": verification_status,
        "provenance": [result["artifact_id"]],
        "related_artifacts": [result["artifact_id"]],
        "executor_result_ref": result["artifact_id"],
        "claim_verdicts": [
            {
                "claim_id": "claim-result",
                "verdict": claim_verdict,
                "evidence_refs": ["EVIDENCE-RESULT"],
            }
        ],
        "additional_findings": [],
        "evidence_gaps": [],
    }

    outcome_map = {
        "CONFIRMED": "COMPLETE",
        "QUALIFIED": "WAIT",
        "NOT_PROVEN": "WAIT",
        "BLOCKED": "WAIT",
    }
    director = {
        "artifact_type": "DIRECTOR_DECISION",
        "artifact_id": "DIRECTOR-POST",
        "produced_by_role": "control-director",
        "assignment_id": assignment["assignment_id"],
        "input_state_ref": assignment["input_state_ref"],
        "status": "PENDING",
        "provenance": [assignment["artifact_id"]],
        "related_artifacts": [assignment["artifact_id"], admission["artifact_id"]],
        "executor_result_ref": result["artifact_id"],
        "verification_result_ref": verification_result["artifact_id"] if verification else None,
        "control_state": "WAIT",
        "decision": "Reconcile the structured post-spawn control point.",
        "next_owner": "control-director",
        "transition_authority": {
            "transition_id": "TRANSITION-1",
            "assignment_ref": assignment["artifact_id"],
            "acceptance_requirements": [
                {
                    "requirement_id": "acceptance-output",
                    "claim_id": "claim-result",
                    "required_evidence_refs": ["EVIDENCE-RESULT"],
                }
            ],
            "verification_required": verification,
            "verification_target_claim_ids": ["claim-result"] if verification else [],
            "allowed_verification_outcomes": [
                "CONFIRMED",
                "QUALIFIED",
                "NOT_PROVEN",
                "BLOCKED",
            ] if verification else [],
            "verification_outcome_map": outcome_map if verification else {},
            "incomplete_outcome": incomplete,
            "next_control_intent_ref": None,
            "required_proof_refs": [admission["artifact_id"]],
            "requires_current_executability": False,
        },
    }
    current = {
        "artifact_type": "STATE_OBSERVATION",
        "artifact_id": "STATE-RESULT",
        "produced_by_role": "control-director",
        "input_state_ref": assignment["input_state_ref"],
        "status": "CURRENT",
        "provenance": [result["artifact_id"]],
        "related_artifacts": [result["artifact_id"]],
        "state_identity": "git:result",
        "authority_scope": "transition-result",
    }

    artifacts = deepcopy(pre_spawn["artifacts"]) + [
        spawned["compiled_assignment"],
        admission,
        assignment,
        result,
        director,
        current,
    ]
    if verification:
        artifacts.append(verification_result)

    return {
        "refs": {
            "current_state_ref": current["artifact_id"],
            "prior_director_decision_ref": director["artifact_id"],
            "assignment_ref": assignment["artifact_id"],
            "executor_result_ref": result["artifact_id"],
            "verification_result_ref": verification_result["artifact_id"] if verification else None,
            "current_capability_profile_ref": spawned["capability_profile_ref"],
        },
        "artifacts": artifacts,
        "spawned": spawned,
    }


def install_current_profile(
    value: dict,
    *,
    destination: str | None = None,
    runtime: str | None = None,
    remove_capability: str | None = None,
) -> None:
    old = artifact(value, value["spawned"]["capability_profile_ref"])
    profile = deepcopy(old)
    profile["artifact_id"] = "PROFILE-NOW"
    evidence = deepcopy(profile["evidence_artifacts"][0])
    evidence["artifact_id"] = "EVIDENCE-NOW"
    profile["evidence_artifacts"] = [evidence]
    profile["related_artifacts"] = [evidence["artifact_id"]]
    for item in profile["capability_evidence"]:
        item["evidence_ref"] = evidence["artifact_id"]

    if destination is not None:
        profile["destination_id"] = destination
    if runtime is not None:
        profile["runtime_identity"] = runtime
        evidence["runtime_identity"] = runtime
    if remove_capability is not None:
        profile["available_capabilities"].remove(remove_capability)
        profile["unavailable_capabilities"].append(remove_capability)
        profile["capability_evidence"] = [
            item for item in profile["capability_evidence"]
            if item["capability"] != remove_capability
        ]
        evidence["capabilities"].remove(remove_capability)

    value["artifacts"].extend([profile, evidence])
    value["refs"]["current_capability_profile_ref"] = profile["artifact_id"]
    artifact(value, "DIRECTOR-POST")["transition_authority"]["requires_current_executability"] = True


class Phase2OperationalizationGateTest(unittest.TestCase):
    def assert_baton(self, result: dict) -> None:
        self.assertIn(result.get("control_state"), BATONS, result)

    def test_A_software_real_end_to_end_loop(self) -> None:
        value = post_spawn_bundle(spawn_bundle())
        spawned = value["spawned"]
        self.assertEqual(spawned["status"], "SPAWN_READY")
        self.assertEqual(spawned["compiled_assignment"]["compilation_status"], "COMPILED")
        self.assertEqual(spawned["assignment_admissibility"]["status"], "ADMISSIBLE")
        self.assertEqual(spawned["assignment_admissibility"]["transition_proof"]["proof_status"], "PROVEN")
        self.assertEqual(spawned["assignment"]["execution_contract"]["proof_status"], "PROVEN")
        self.assertEqual(
            spawned["assignment"]["execution_contract"]["required_capabilities"],
            spawned["assignment_admissibility"]["required_capabilities"],
        )
        result = resolve_transition(value)
        self.assert_baton(result)
        self.assertEqual(result["control_state"], "COMPLETE", result)

    def test_B_research_real_end_to_end_loop_uses_authoritative_machine_admission(self) -> None:
        work_package = base_wp()
        admission = admit_work_package(work_package)
        self.assertEqual(admission["ADMISSION_STATUS"], "ADMITTED_MACHINE_RESEARCH", admission)
        self.assertEqual(validate_experiment(base_experiment()), [])

        pre_spawn = spawn_bundle("research", "execute_research_work", "machine-only-execution")
        pre_spawn["decision"]["research_admission"] = "MACHINE_ONLY_ADMITTED"
        value = post_spawn_bundle(pre_spawn)
        self.assertEqual(value["spawned"]["engine_id"], "research")
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

        rejected = base_wp()
        rejected["REQUIRES_THIRD_PARTY_HUMAN"] = True
        self.assertNotEqual(admit_work_package(rejected)["ADMISSION_STATUS"], "ADMITTED_MACHINE_RESEARCH")
        no_admission = spawn_bundle("research", "execute_research_work", "machine-only-execution")
        denied = resolve_spawn(no_admission)
        self.assertEqual((denied["control_state"], denied["reason"]), ("ESCALATE", "RESEARCH_ADMISSION_REQUIRED"))
        self.assertNotIn("assignment", denied)

    def test_C_verification_real_end_to_end_loop_and_artifact_separation(self) -> None:
        pre_spawn = spawn_bundle("verification", "verify_completion_claim", "exact-evidence-verification")
        value = post_spawn_bundle(pre_spawn)
        self.assertEqual(value["spawned"]["engine_id"], "verification")
        executor = artifact(value, "RESULT-1")
        verification = artifact(value, "VERIFY-1")
        self.assertEqual(executor["artifact_type"], "EXECUTOR_RESULT")
        self.assertEqual(verification["artifact_type"], "VERIFICATION_RESULT")
        self.assertNotEqual(executor["artifact_id"], verification["artifact_id"])
        self.assertEqual(verification["executor_result_ref"], executor["artifact_id"])
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_D_exact_spawn_artifacts_are_directly_consumed_downstream(self) -> None:
        value = post_spawn_bundle(spawn_bundle())
        spawned = value["spawned"]
        self.assertIs(artifact(value, spawned["assignment_ref"]), value["artifacts"][-4])
        self.assertEqual(
            artifact(value, spawned["admissibility_ref"])["transition_proof"],
            spawned["assignment_admissibility"]["transition_proof"],
        )
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_E_executor_and_verifier_cannot_substitute_for_each_other(self) -> None:
        value = post_spawn_bundle(spawn_bundle())
        value["refs"]["executor_result_ref"] = None
        self.assertEqual(resolve_transition(value)["reason"], "EXECUTOR_RESULT_PENDING")

        value = post_spawn_bundle(spawn_bundle())
        value["refs"]["verification_result_ref"] = None
        self.assertEqual(resolve_transition(value)["reason"], "VERIFICATION_RESULT_PENDING")

        value = post_spawn_bundle(spawn_bundle())
        artifact(value, "VERIFY-1")["executor_result_ref"] = "OTHER-RESULT"
        result = resolve_transition(value)
        self.assertEqual(result["control_state"], "ESCALATE", result)

        value = post_spawn_bundle(spawn_bundle())
        artifact(value, "VERIFY-1")["assignment_id"] = "OTHER-ASSIGNMENT"
        result = resolve_transition(value)
        self.assertEqual(result["control_state"], "ESCALATE", result)

    def test_F_verification_authority_ceiling_and_director_mapping(self) -> None:
        confirmed = post_spawn_bundle(spawn_bundle(), verification_status="CONFIRMED")
        self.assertEqual(resolve_transition(confirmed)["control_state"], "COMPLETE")

        qualified = post_spawn_bundle(spawn_bundle(), verification_status="QUALIFIED")
        artifact(qualified, "DIRECTOR-POST")["transition_authority"]["verification_outcome_map"]["QUALIFIED"] = "ESCALATE"
        self.assertEqual(resolve_transition(qualified)["control_state"], "ESCALATE")

        not_proven = post_spawn_bundle(spawn_bundle(), verification_status="NOT_PROVEN")
        self.assertEqual(resolve_transition(not_proven)["control_state"], "WAIT")

        blocked = post_spawn_bundle(spawn_bundle(), verification_status="BLOCKED")
        self.assertEqual(resolve_transition(blocked)["control_state"], "WAIT")

        adversarial = post_spawn_bundle(
            spawn_bundle(),
            verification_status="CONFIRMED",
            claim_verdict="NOT_PROVEN",
        )
        result = resolve_transition(adversarial)
        self.assertEqual(result["control_state"], "WAIT", result)
        self.assertEqual(result.get("verification_outcome"), "NOT_PROVEN")

    def test_G_relevant_bound_dependency_stales_only_that_proof(self) -> None:
        value = post_spawn_bundle(spawn_bundle())
        artifact(value, "STATE-OBS-1")["state_identity"] = "git:changed"
        result = resolve_transition(value)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "RELEVANT_PROOF_STALE"))

    def test_H_unrelated_state_observation_does_not_globally_invalidate(self) -> None:
        value = post_spawn_bundle(spawn_bundle())
        value["artifacts"].append({
            "artifact_type": "STATE_OBSERVATION",
            "artifact_id": "STATE-UNRELATED",
            "produced_by_role": "control-director",
            "input_state_ref": None,
            "status": "CURRENT",
            "provenance": [],
            "related_artifacts": [],
            "state_identity": "unrelated:changed",
            "authority_scope": "unrelated",
        })
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_I_runtime_drift_and_exact_surface_binding(self) -> None:
        value = post_spawn_bundle(spawn_bundle())
        install_current_profile(value, remove_capability="shell")
        result = resolve_transition(value)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "BLOCKED_RUNTIME_DRIFT"))

        value = post_spawn_bundle(spawn_bundle())
        install_current_profile(value, destination="other-destination")
        result = resolve_transition(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "CURRENT_PROFILE_EXECUTION_SURFACE_MISMATCH"))

        value = post_spawn_bundle(spawn_bundle())
        install_current_profile(value, runtime="other-runtime")
        result = resolve_transition(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "CURRENT_PROFILE_EXECUTION_SURFACE_MISMATCH"))

    def test_J_exact_proof_admission_identity_fails_closed(self) -> None:
        mutations = []

        def wrong_admission_ref(value: dict) -> None:
            artifact(value, "ASSIGN-RESOLVED")["execution_contract"]["admissibility_ref"] = "OTHER"
        mutations.append(wrong_admission_ref)

        def proof_for_other_assignment(value: dict) -> None:
            artifact(value, "ADM-RESOLVED")["transition_proof"]["assignment_ref"] = "OTHER-ASSIGNMENT"
        mutations.append(proof_for_other_assignment)

        def proof_not_proven(value: dict) -> None:
            artifact(value, "ADM-RESOLVED")["transition_proof"]["proof_status"] = "UNPROVEN"
        mutations.append(proof_not_proven)

        def wrong_destination(value: dict) -> None:
            artifact(value, "ADM-RESOLVED")["transition_proof"]["destination_id"] = "OTHER"
        mutations.append(wrong_destination)

        def wrong_runtime(value: dict) -> None:
            artifact(value, "ADM-RESOLVED")["transition_proof"]["runtime_identity"] = "OTHER"
        mutations.append(wrong_runtime)

        def malformed_capabilities(value: dict) -> None:
            artifact(value, "ASSIGN-RESOLVED")["execution_contract"]["required_capabilities"] = [5]
        mutations.append(malformed_capabilities)

        for mutate in mutations:
            with self.subTest(mutation=mutate.__name__):
                value = post_spawn_bundle(spawn_bundle())
                mutate(value)
                result = resolve_transition(value)
                self.assert_baton(result)
                self.assertNotEqual(result["control_state"], "COMPLETE", result)

        value = post_spawn_bundle(spawn_bundle())
        fake = deepcopy(artifact(value, "ADM-RESOLVED"))
        fake["artifact_id"] = "FAKE-PROOF"
        fake["artifact_type"] = "UNRELATED_ARTIFACT"
        artifact(value, "ASSIGN-RESOLVED")["execution_contract"]["admissibility_ref"] = fake["artifact_id"]
        value["artifacts"].append(fake)
        result = resolve_transition(value)
        self.assert_baton(result)
        self.assertNotEqual(result["control_state"], "COMPLETE", result)

    def test_K_L_assign_baton_must_reenter_pre_spawn_and_reprove_admissibility(self) -> None:
        value = post_spawn_bundle(spawn_bundle(), verification=False, incomplete="ASSIGN")
        intent = {
            "artifact_type": "CONTROL_INTENT",
            "artifact_id": "INTENT-NEXT",
            "assignment_id": "ASSIGN-RESOLVED",
            "next_action": "compile the next bounded work item",
        }
        value["artifacts"].append(intent)
        artifact(value, "DIRECTOR-POST")["transition_authority"]["next_control_intent_ref"] = intent["artifact_id"]
        artifact(value, "RESULT-1")["claims"][0]["evidence_refs"] = []

        transition = resolve_transition(value)
        self.assertEqual(transition["control_state"], "ASSIGN", transition)
        self.assertEqual(transition["next_entrypoint"], "tools.resolver_spawn.resolve_spawn")
        self.assertNotIn("assignment", transition)
        self.assertNotEqual(transition.get("status"), "SPAWN_READY")

        next_spawn = spawn_bundle()
        next_spawn["assignment_id"] = "ASSIGN-NEXT"
        next_spawn["admissibility_id"] = "ADM-NEXT"
        next_spawn["assignment_compilation_draft"]["mandatory_actions"][0]["required_capabilities"].append("database_access")
        next_spawn["assignment_compilation_draft"]["authorized_required_capabilities"].append("database_access")
        reproved = resolve_spawn(next_spawn)
        self.assertEqual((reproved["control_state"], reproved["reason"]), ("WAIT", "ASSIGNMENT_NOT_ADMISSIBLE"))
        self.assertNotIn("assignment", reproved)

    def test_M_N_generic_director_authority_optional_but_post_spawn_mandatory(self) -> None:
        schema = json.loads((ROOT / "schemas/director-decision.schema.json").read_text(encoding="utf-8"))
        self.assertNotIn("transition_authority", schema["required"])
        self.assertIn("transition_authority", schema["properties"])

        value = post_spawn_bundle(spawn_bundle())
        del artifact(value, "DIRECTOR-POST")["transition_authority"]
        result = resolve_transition(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "MALFORMED_DIRECTOR_DECISION"))

    def test_O_baton_closed_set_on_representative_and_negative_paths(self) -> None:
        scenarios = [
            resolve_transition(post_spawn_bundle(spawn_bundle())),
            resolve_transition(post_spawn_bundle(spawn_bundle(), verification_status="NOT_PROVEN")),
            resolve_spawn(spawn_bundle("canon", "reconcile_canon", "none")),
        ]
        terminal = spawn_bundle()
        terminal["decision"]["control_state"] = "ESCALATE"
        scenarios.append(resolve_spawn(terminal))
        for result in scenarios:
            self.assert_baton(result)

    def test_N9_representative_malformed_inputs_never_reach_success(self) -> None:
        cases = []

        duplicate = post_spawn_bundle(spawn_bundle())
        duplicate["artifacts"].append(deepcopy(duplicate["artifacts"][0]))
        cases.append(duplicate)

        bad_director = post_spawn_bundle(spawn_bundle())
        del artifact(bad_director, "DIRECTOR-POST")["decision"]
        cases.append(bad_director)

        bad_assignment = post_spawn_bundle(spawn_bundle())
        del artifact(bad_assignment, "ASSIGN-RESOLVED")["execution_contract"]
        cases.append(bad_assignment)

        bad_executor = post_spawn_bundle(spawn_bundle())
        artifact(bad_executor, "RESULT-1")["status"] = "CONFIRMED"
        cases.append(bad_executor)

        bad_verification = post_spawn_bundle(spawn_bundle())
        artifact(bad_verification, "VERIFY-1")["claim_verdicts"][0]["verdict"] = "COMPLETE"
        cases.append(bad_verification)

        missing_ref = post_spawn_bundle(spawn_bundle())
        missing_ref["refs"]["assignment_ref"] = None
        cases.append(missing_ref)

        identity_mismatch = post_spawn_bundle(spawn_bundle())
        artifact(identity_mismatch, "RESULT-1")["assignment_id"] = "OTHER"
        cases.append(identity_mismatch)

        bad_lifecycle = post_spawn_bundle(spawn_bundle())
        del artifact(bad_lifecycle, "ADM-RESOLVED")["transition_proof"]["dependency_bindings"]
        cases.append(bad_lifecycle)

        for index, value in enumerate(cases):
            with self.subTest(case=index):
                result = resolve_transition(value)
                self.assert_baton(result)
                self.assertNotEqual(result["control_state"], "COMPLETE", result)

    def test_BLOCKER_schema_forbidden_weaker_outcome_cannot_be_runtime_complete(self) -> None:
        schema = json.loads((ROOT / "schemas/director-decision.schema.json").read_text(encoding="utf-8"))
        mapping_schema = schema["properties"]["transition_authority"]["properties"]["verification_outcome_map"]["properties"]
        self.assertNotIn("COMPLETE", mapping_schema["NOT_PROVEN"]["enum"])
        self.assertNotIn("COMPLETE", mapping_schema["QUALIFIED"]["enum"])
        self.assertNotIn("COMPLETE", mapping_schema["BLOCKED"]["enum"])

        value = post_spawn_bundle(spawn_bundle(), verification_status="NOT_PROVEN")
        director = artifact(value, "DIRECTOR-POST")
        director["transition_authority"]["verification_outcome_map"]["NOT_PROVEN"] = "COMPLETE"

        self.assertTrue(
            validate_director_decision(director),
            "runtime Director validator accepted a transition_authority forbidden by the canonical schema",
        )
        result = resolve_transition(value)
        self.assertNotEqual(
            result["control_state"],
            "COMPLETE",
            "schema-forbidden NOT_PROVEN -> COMPLETE mapping reached protected completion",
        )


if __name__ == "__main__":
    unittest.main()
