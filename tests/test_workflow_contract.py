from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tests.test_resolver_spawn import bundle
from tools.resolver_spawn import resolve_spawn
from tools.workflow_contract import resolve_workflow_contract


def _candidate(artifact_id: str = "CANON-CANDIDATE-1") -> dict[str, object]:
    return {
        "artifact_type": "CANON_STATE",
        "artifact_id": artifact_id,
        "provenance": ["OWNER/K0"],
    }


def _freeze_authority(candidate_id: str = "CANON-CANDIDATE-1", *, artifact_id: str = "FREEZE-AUTH-1") -> dict[str, object]:
    return {
        "artifact_type": "FREEZE_AUTHORITY",
        "artifact_id": artifact_id,
        "produced_by_role": "owner-interface",
        "status": "AUTHORIZED",
        "provenance": ["OWNER-DECISION-1"],
        "authority_role": "OWNER_K0",
        "target_ref": candidate_id,
        "candidate_identity": candidate_id,
        "workflow_id": "validate_and_freeze_canon",
        "authorizes_exact_candidate_freeze": True,
    }


def freeze_bundle(*, authority: dict[str, object] | None = None) -> dict:
    value = bundle("canon", "freeze_canon", "validate_and_freeze_canon")
    candidate = _candidate()
    value["artifacts"].append(candidate)
    bindings: dict[str, object] = {"exact_canon_candidate_ref": candidate["artifact_id"]}
    if authority is not None:
        value["artifacts"].append(authority)
        bindings["explicit_freeze_authority"] = authority["artifact_id"]
    value["workflow_prerequisite_bindings"] = bindings
    return value


class WorkflowContractUnitTest(unittest.TestCase):
    def test_engine_neutral_required_input_omission_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "engines/demo/MANIFEST.yaml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                "engine_id: demo\n"
                "status: available\n"
                "workflow_contracts:\n"
                "  execute:\n"
                "    upstream_requirements:\n"
                "      - {\"requirement_id\":\"required_input\",\"proof_class\":\"ARTIFACT_REF\"}\n"
                "capabilities:\n"
                "  do_work: execute\n",
                encoding="utf-8",
            )
            decision = {
                "engine_id": "demo", "engine_status": "available",
                "semantic_capability": "do_work", "workflow_id": "execute",
            }
            result = resolve_workflow_contract(decision, {}, {}.get, root=root)
            self.assertEqual((result["status"], result["reason"]), ("ERROR", "WORKFLOW_PREREQUISITE_REQUIRED"))
            self.assertEqual(result["missing_requirement"], "required_input")

    def test_engine_neutral_capability_workflow_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "engines/demo/MANIFEST.yaml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                "engine_id: demo\n"
                "status: available\n"
                "workflow_contracts:\n"
                "  execute:\n"
                "    upstream_requirements: []\n"
                "  other:\n"
                "    upstream_requirements: []\n"
                "capabilities:\n"
                "  do_work: execute\n",
                encoding="utf-8",
            )
            decision = {
                "engine_id": "demo", "engine_status": "available",
                "semantic_capability": "do_work", "workflow_id": "other",
            }
            result = resolve_workflow_contract(decision, {}, {}.get, root=root)
            self.assertEqual((result["status"], result["reason"]), ("ERROR", "CAPABILITY_WORKFLOW_IDENTITY_MISMATCH"))


class CanonWorkflowAdmissionIntegrationTest(unittest.TestCase):
    def assert_fail_closed(self, value: dict, reason: str | None = None) -> dict:
        result = resolve_spawn(value)
        self.assertNotEqual(result.get("status"), "SPAWN_READY", result)
        self.assertNotIn("assignment", result)
        if reason is not None:
            self.assertEqual(result.get("reason"), reason, result)
        return result

    def test_validate_with_exact_candidate_reaches_spawn_ready_without_freeze_authority(self) -> None:
        value = bundle("canon", "validate_canon", "validate_canon")
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        self.assertEqual(result["workflow_contract_source"], "engines/canon/MANIFEST.yaml")
        self.assertEqual(result["workflow_prerequisite_refs"], ["CANON-CANDIDATE-1"])
        self.assertNotIn("FREEZE-AUTH-1", result["assignment_admissibility"]["related_artifacts"])

    def test_validate_without_exact_candidate_fails_closed(self) -> None:
        value = bundle("canon", "validate_canon", "validate_canon")
        value["workflow_prerequisite_bindings"] = {}
        self.assert_fail_closed(value, "WORKFLOW_PREREQUISITE_REQUIRED")

    def test_freeze_with_valid_scoped_authority_reaches_spawn_ready_and_binds_proof_refs(self) -> None:
        value = freeze_bundle(authority=_freeze_authority())
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        for artifact_id in ("CANON-CANDIDATE-1", "FREEZE-AUTH-1"):
            self.assertIn(artifact_id, result["workflow_prerequisite_refs"])
            self.assertIn(artifact_id, result["assignment_admissibility"]["related_artifacts"])
            self.assertIn(artifact_id, result["assignment"]["related_artifacts"])
        self.assertEqual(result["assignment"]["execution_contract"]["proof_status"], "PROVEN")

    def test_freeze_without_authority_fails_closed(self) -> None:
        self.assert_fail_closed(freeze_bundle(), "WORKFLOW_PREREQUISITE_REQUIRED")

    def test_freeze_wrong_or_fake_authority_fails_closed(self) -> None:
        wrong = _freeze_authority()
        wrong["target_ref"] = "OTHER-CANDIDATE"
        self.assert_fail_closed(freeze_bundle(authority=wrong), "WORKFLOW_AUTHORITY_SCOPE_MISMATCH")

        fake = _freeze_authority()
        fake["artifact_type"] = "OWNER_DECISION_RECORD"
        self.assert_fail_closed(freeze_bundle(authority=fake), "WORKFLOW_AUTHORITY_TYPE_MISMATCH")

    def test_selected_prerequisite_actions_cannot_mask_missing_workflow_requirement(self) -> None:
        value = freeze_bundle()
        value["selected_prerequisite_actions"] = [{
            "action_id": "pretend-freeze-authority",
            "required_capabilities": ["shell"],
            "evidence_path": "caller says freeze authority exists",
        }]
        result = self.assert_fail_closed(value, "WORKFLOW_PREREQUISITE_REQUIRED")
        self.assertEqual(result["workflow_contract_details"]["missing_requirement"], "explicit_freeze_authority")

    def test_capability_workflow_identity_mix_fails_closed(self) -> None:
        value = bundle("canon", "validate_canon", "validate_canon")
        value["decision"]["workflow_id"] = "validate_and_freeze_canon"
        self.assert_fail_closed(value, "CAPABILITY_WORKFLOW_IDENTITY_MISMATCH")

    def test_missing_destination_capability_preserves_assignment_not_admissible(self) -> None:
        value = bundle("canon", "validate_canon", "validate_canon")
        value["assignment_compilation_draft"]["mandatory_actions"][0]["required_capabilities"].append("database_access")
        value["assignment_compilation_draft"]["authorized_required_capabilities"].append("database_access")
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "ASSIGNMENT_NOT_ADMISSIBLE"), result)
        self.assertEqual(result["missing_capabilities"], ["database_access"])
        self.assertNotIn("assignment", result)


if __name__ == "__main__":
    unittest.main()
