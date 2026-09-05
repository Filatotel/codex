from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.test_assignment_compiler import action, claim, draft, envelope
from tests.test_executability import governed_chain, valid_chain
from tests.test_research_machine_only import base_wp
import tools.resolver_spawn as resolver_spawn
from tools.research_policy import admit_work_package
from tools.resolver_spawn import resolve_spawn

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_POLICY_SURFACE = "tools.research_policy.admit_work_package"


def _append_artifact(value: dict, artifact: dict) -> str:
    value["artifacts"].append(artifact)
    return artifact["artifact_id"]


def _attach_default_canon_prerequisites(value: dict, workflow: str) -> None:
    """Keep pre-existing Canon resolver fixtures valid under governed workflow closure."""
    state_ref = value["input_state_observation_ref"]
    if workflow == "establish_canon_foundation":
        owner_ref = _append_artifact(value, {
            "artifact_id": "OWNER-FOUNDATION-INPUT-1", "artifact_type": "OWNER_DECISION_RECORD",
            "provenance": ["OWNER/K0"],
        })
        value["workflow_prerequisite_bindings"] = {
            "owner_or_authorized_foundation_input": owner_ref,
            "exact_state_identity": state_ref,
        }
    elif workflow == "reconcile_research_into_canon":
        canon_ref = _append_artifact(value, {
            "artifact_id": "CANON-CURRENT-1", "artifact_type": "CANON_STATE", "provenance": ["OWNER/K0"],
        })
        research_ref = _append_artifact(value, {
            "artifact_id": "FINDING-1", "artifact_type": "RESEARCH_FINDING", "provenance": ["RESEARCH-RELEASE-1"],
        })
        authority_ref = _append_artifact(value, {
            "artifact_id": "CANON-MUTATION-AUTH-1", "artifact_type": "OWNER_DECISION_RECORD", "provenance": ["OWNER/K0"],
        })
        value["workflow_prerequisite_bindings"] = {
            "exact_current_canon_ref": canon_ref,
            "exact_research_release_or_finding_refs": [research_ref],
            "canon_mutation_authority_for_any_accepted_change": authority_ref,
        }
    elif workflow == "manage_production_canon_change":
        canon_ref = _append_artifact(value, {
            "artifact_id": "CANON-CURRENT-1", "artifact_type": "CANON_STATE", "provenance": ["OWNER/K0"],
        })
        signal_ref = _append_artifact(value, {
            "artifact_id": "PRODUCTION-CHANGE-1", "artifact_type": "PRODUCTION_CHANGE", "provenance": ["PRODUCTION-1"],
        })
        authority_ref = _append_artifact(value, {
            "artifact_id": "CANON-MUTATION-AUTH-1", "artifact_type": "OWNER_DECISION_RECORD", "provenance": ["OWNER/K0"],
        })
        value["workflow_prerequisite_bindings"] = {
            "exact_current_canon_ref": canon_ref,
            "exact_production_change_signal": signal_ref,
            "canon_mutation_authority_for_any_accepted_change": authority_ref,
        }
    elif workflow == "validate_canon":
        candidate_ref = _append_artifact(value, {
            "artifact_id": "CANON-CANDIDATE-1", "artifact_type": "CANON_STATE", "provenance": ["OWNER/K0"],
        })
        value["workflow_prerequisite_bindings"] = {"exact_canon_candidate_ref": candidate_ref}


def bundle(engine="production/software", capability="implement_software_change", workflow="implementation"):
    assignment, _, profile = deepcopy(valid_chain())
    _, route = governed_chain(assignment, {}, profile)
    compilation = draft("MOVING_BRANCH")
    compilation["mandatory_actions"] = [action(capabilities=["python_runtime", "shell"])]
    compilation["authorized_required_capabilities"] = ["python_runtime", "shell"]
    env = envelope()
    evidence = profile["evidence_artifacts"][0]
    state_observation = {"artifact_type": "STATE_OBSERVATION", "artifact_id": "STATE-OBS-1",
        "produced_by_role": "control-director", "input_state_ref": compilation["input_state_ref"],
        "status": "CURRENT", "provenance": ["OWNER/K0"], "related_artifacts": [],
        "state_identity": "git:input-state", "authority_scope": "assignment-input"}
    value = {
        "decision": {"control_state": "ASSIGN", "engine_id": engine, "engine_status": "available",
                     "semantic_capability": capability, "workflow_id": workflow, "execution_mode": "local"},
        "assignment_compilation_draft": compilation,
        "assignment_draft_semantics": {"objective": "Perform the already-authorized bounded work.", "authority": ["OWNER/K0"],
            "scope": {"allowed": ["bounded work"], "forbidden": ["scope expansion"]}, "acceptance": ["produce required evidence"],
            "required_outputs": ["result"], "stop_conditions": ["runtime drift"], "result_to": "agent-1"},
        "selected_prerequisite_actions": [], "execution_envelope_ref": env["artifact_id"],
        "capability_profile_ref": profile["artifact_id"], "route_ref": route["artifact_id"],
        "admissibility_id": "ADM-RESOLVED", "assignment_id": "ASSIGN-RESOLVED",
        "input_state_observation_ref": state_observation["artifact_id"],
        "artifacts": [env, evidence, profile, route, state_observation],
    }
    if engine == "canon":
        _attach_default_canon_prerequisites(value, workflow)
    return value


def attach_research_admission(value, work_package=None, admission_id="RESEARCH-ADM-1"):
    work = deepcopy(work_package or base_wp())
    admission_result = admit_work_package(work)
    admission = {
        "artifact_id": admission_id,
        **admission_result,
        "WORK_PACKAGE_ID": work["WORK_PACKAGE_ID"],
        "QUESTION_ID": work["QUESTION_ID"],
        "POLICY_SURFACE": RESEARCH_POLICY_SURFACE,
        "PROVENANCE": [RESEARCH_POLICY_SURFACE, work["WORK_PACKAGE_ID"], work["QUESTION_ID"]],
        "WORK_PACKAGE": work,
    }
    value["decision"].update({"research_admission_ref": admission_id,
                              "research_work_package_id": work["WORK_PACKAGE_ID"],
                              "research_question_id": work["QUESTION_ID"]})
    value["artifacts"].append(admission)
    return admission


class ResolverSpawnTest(unittest.TestCase):
    def assert_spawn_ready(self, value):
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        self.assertEqual(result["assignment"]["objective"], value["assignment_draft_semantics"]["objective"])
        return result

    def test_representative_software_research_and_verification(self):
        cases = [
            bundle(),
            bundle("research", "execute_research_work", "machine-only-execution"),
            bundle("verification", "verify_completion_claim", "exact-evidence-verification"),
        ]
        attach_research_admission(cases[1])
        cases[2]["assignment_compilation_draft"]["evidence_requirements"] = [
            action("verification-evidence", capabilities=["python_runtime"], obligation_class="local_evidence")]
        for value in cases:
            with self.subTest(engine=value["decision"]["engine_id"]):
                self.assert_spawn_ready(value)

    def test_research_requires_structured_machine_only_admission(self):
        value = bundle("research", "execute_research_work", "machine-only-execution")
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "RESEARCH_ADMISSION_REQUIRED"))
        self.assertNotIn("assignment", result)

    def test_compilation_rejected_escalates_without_assignment(self):
        value = bundle(); value["assignment_compilation_draft"]["mandatory_actions"][0]["claim_ref"] = "missing"
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "COMPILE_REJECTED"))
        self.assertNotIn("assignment", result)

    def test_missing_capability_waits_with_subset_details(self):
        value = bundle(); value["assignment_compilation_draft"]["mandatory_actions"][0]["required_capabilities"].append("database_access")
        value["assignment_compilation_draft"]["authorized_required_capabilities"].append("database_access")
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "ASSIGNMENT_NOT_ADMISSIBLE"))
        self.assertEqual(result["missing_capabilities"], ["database_access"])
        self.assertNotIn("assignment", result)

    def test_control_obligation_capability_does_not_expand_executor_destination(self):
        value = bundle()
        value["assignment_compilation_draft"]["authorized_claims"].append(
            claim("control-outcome", responsibility="CONTROL")
        )
        value["assignment_compilation_draft"]["mandatory_actions"].append(
            action("owner-check", claim_ref="control-outcome", responsibility="CONTROL", capabilities=["owner_authority"])
        )
        result = self.assert_spawn_ready(value)
        self.assertNotIn("owner_authority", result["assignment_admissibility"]["required_capabilities"])
        self.assertFalse(any(item.get("action_id") == "owner-check" for item in result["assignment_admissibility"]["mandatory_actions"]))

    def test_stale_profile_waits_but_malformed_profile_escalates(self):
        stale = bundle(); profile = stale["artifacts"][2]
        profile["freshness_boundary"]["observed_at"] = "2024-01-01T00:00:00Z"
        profile["freshness_boundary"]["valid_until"] = "2025-01-01T00:00:00Z"
        profile["evidence_artifacts"][0]["observed_at"] = "2024-01-01T00:00:00Z"
        profile["evidence_artifacts"][0]["valid_until"] = "2025-01-01T00:00:00Z"
        stale["artifacts"][1]["observed_at"] = "2024-01-01T00:00:00Z"
        stale["artifacts"][1]["valid_until"] = "2025-01-01T00:00:00Z"
        result = resolve_spawn(stale)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "CAPABILITY_PROFILE_STALE"))
        malformed = bundle(); del malformed["artifacts"][2]["destination_id"]
        result = resolve_spawn(malformed)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "MALFORMED_CAPABILITY_PROFILE"))

    def test_route_profile_destination_mismatch_escalates(self):
        value = bundle(); value["artifacts"][3]["segments"][1]["destination_id"] = "other"
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "EXECUTION_ROUTE_INVALID"))

    def test_prerequisite_action_is_accounted_and_bare_capability_is_rejected(self):
        value = bundle(); value["selected_prerequisite_actions"] = [{"action_id": "render", "required_capabilities": ["shell"], "evidence_path": "render-check"}]
        result = self.assert_spawn_ready(value)
        self.assertIn("render-check", result["assignment_admissibility"]["mandatory_evidence_paths"])
        value = bundle(); value["additional_required_capabilities"] = ["outbound_network"]
        result = resolve_spawn(value)
        self.assertEqual(result["reason"], "UNACCOUNTED_CAPABILITY_EXPANSION")

    def test_non_materialized_engine_and_terminal_batons(self):
        value = bundle("canon", "reconcile_canon", "none"); value["decision"]["engine_status"] = "not_materialized"
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "ENGINE_NOT_MATERIALIZED"))
        for state in ("WAIT", "ESCALATE", "COMPLETE"):
            value = bundle(); value["decision"]["control_state"] = state
            result = resolve_spawn(value)
            self.assertEqual((result["control_state"], result["status"]), (state, state))
            self.assertNotIn("assignment", result)

    def test_missing_semantics_fail_closed(self):
        value = bundle(); del value["assignment_draft_semantics"]["objective"]
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "MISSING_ASSIGNMENT_SEMANTICS"), result)

    def test_duplicate_action_identity_fails_closed(self):
        value = bundle(); value["selected_prerequisite_actions"] = [{"action_id": "test", "required_capabilities": ["shell"], "evidence_path": None}]
        result = resolve_spawn(value)
        self.assertEqual(result["reason"], "CONTRADICTORY_CONTROL_ARTIFACTS")

    def test_malformed_profile_or_route_ref_escalates_without_exception(self):
        for field, bad_value in (("capability_profile_ref", []), ("route_ref", {})):
            with self.subTest(field=field):
                value = bundle(); value[field] = bad_value
                result = resolve_spawn(value)
                self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "MALFORMED_CONTROL_ARTIFACT"))
                self.assertNotIn("assignment", result)

    def test_duplicate_artifact_identity_fails_closed(self):
        value = bundle(); value["artifacts"].append(deepcopy(value["artifacts"][2]))
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "CONTRADICTORY_CONTROL_ARTIFACTS"))
        self.assertTrue(any("duplicate artifact_id" in error for error in result["errors"]))

    def test_compiled_capability_drop_is_caught_by_full_proof(self):
        value = bundle()
        real_compile = resolver_spawn.compile_assignment

        def compile_with_extra_capability(*args, **kwargs):
            compiled = real_compile(*args, **kwargs)
            compiled["authorized_required_capabilities"] = sorted(set(compiled["authorized_required_capabilities"]) | {"database_access"})
            return compiled

        with patch.object(resolver_spawn, "compile_assignment", side_effect=compile_with_extra_capability), \
             patch.object(resolver_spawn, "validate_compiled_assignment", return_value=[]):
            result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "FINAL_ASSIGNMENT_PROOF_FAILED"))
        self.assertTrue(any("drops compiled assignment capabilities" in error for error in result["errors"]))

    def test_final_assignment_ref_mismatch_is_caught_by_full_proof(self):
        value = bundle()
        real_proof = resolver_spawn.validate_assignment_execution_contract

        def validate_with_bad_ref(assignment, *args, **kwargs):
            mutated = deepcopy(assignment)
            mutated["execution_contract"]["admissibility_ref"] = "ADM-WRONG"
            return real_proof(mutated, *args, **kwargs)

        with patch.object(resolver_spawn, "validate_assignment_execution_contract", side_effect=validate_with_bad_ref):
            result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "FINAL_ASSIGNMENT_PROOF_FAILED"))
        self.assertTrue(any("admissibility_ref mismatch" in error for error in result["errors"]))

    def test_malformed_final_capability_entry_escalates_without_exception(self):
        value = bundle()
        value["assignment_compilation_draft"]["mandatory_actions"][0]["required_capabilities"] = [5]
        value["assignment_compilation_draft"]["authorized_required_capabilities"] = []
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "MALFORMED_MANDATORY_ACTION"))
        self.assertNotIn("assignment", result)

    def test_cli_reads_only_local_json_and_emits_json(self):
        value = bundle()
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as handle:
            json.dump(value, handle); handle.flush()
            completed = subprocess.run([sys.executable, str(ROOT / "tools/resolver_spawn.py"), handle.name], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(completed.stdout)["status"], "SPAWN_READY")


if __name__ == "__main__":
    unittest.main()
