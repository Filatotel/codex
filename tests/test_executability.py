from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.executability import (
    evaluate_assignment_admissibility,
    validate_admissibility_against_profile,
    validate_admissibility_record,
    validate_assignment_execution_contract,
    validate_capability_profile,
)


ROOT = Path(__file__).resolve().parents[1]


def valid_chain() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    profile = {
        "artifact_type": "CAPABILITY_PROFILE",
        "artifact_id": "CAP-1",
        "produced_by_role": "control-director",
        "assignment_id": None,
        "input_state_ref": "state-1",
        "status": "CURRENT",
        "provenance": ["local-probe"],
        "related_artifacts": ["EVIDENCE-1"],
        "destination_id": "agent-1",
        "runtime_identity": "runtime-1",
        "available_capabilities": ["shell", "python_runtime"],
        "unavailable_capabilities": ["outbound_network"],
        "capability_evidence": [
            {"capability": "shell", "evidence_ref": "EVIDENCE-1"},
            {"capability": "python_runtime", "evidence_ref": "EVIDENCE-1"},
        ],
        "evidence_artifacts": [{
            "artifact_type": "CAPABILITY_EVIDENCE",
            "artifact_id": "EVIDENCE-1",
            "status": "RESOLVED",
            "runtime_identity": "runtime-1",
            "capabilities": ["shell", "python_runtime"],
            "observed_at": "2026-01-01T00:00:00Z",
            "valid_until": "2999-01-01T00:00:00Z",
        }],
        "freshness_boundary": {
            "observed_at": "2026-01-01T00:00:00Z",
            "valid_until": "2999-01-01T00:00:00Z",
        },
        "limitations": [],
    }
    record = {
        "artifact_type": "ASSIGNMENT_ADMISSIBILITY",
        "artifact_id": "ADM-1",
        "produced_by_role": "control-director",
        "assignment_id": None,
        "input_state_ref": "state-1",
        "status": "ADMISSIBLE",
        "provenance": ["CAP-1"],
        "related_artifacts": ["CAP-1"],
        "assignment_draft_id": "DRAFT-1",
        "destination_id": "agent-1",
        "runtime_identity": "runtime-1",
        "capability_profile_ref": "CAP-1",
        "mandatory_actions": [{
            "action_id": "run_tests",
            "required_capabilities": ["shell", "python_runtime"],
            "evidence_path": "python -m unittest",
        }],
        "required_capabilities": ["shell", "python_runtime"],
        "available_capabilities": ["shell", "python_runtime"],
        "unsatisfied_required_capabilities": [],
        "mandatory_evidence_paths": ["python -m unittest"],
        "execution_mode": "local",
    }
    assignment = {
        "artifact_type": "ASSIGNMENT",
        "artifact_id": "ASSIGN-1",
        "assignment_id": "ASSIGN-1",
        "execution_contract": {
            "assignment_draft_ref": "DRAFT-1",
            "destination_id": "agent-1",
            "runtime_identity": "runtime-1",
            "capability_profile_ref": "CAP-1",
            "admissibility_ref": "ADM-1",
            "proof_status": "PROVEN",
            "required_capabilities": ["shell", "python_runtime"],
            "unsatisfied_required_capabilities": [],
            "mandatory_evidence_paths": ["python -m unittest"],
            "execution_mode": "local",
        },
    }
    return assignment, record, profile


class ExecutabilityContractTest(unittest.TestCase):
    def test_required_subset_available_is_admissible(self) -> None:
        result = evaluate_assignment_admissibility(["shell"], ["shell", "python_runtime"])
        self.assertEqual(result["status"], "ADMISSIBLE")
        self.assertEqual(result["unsatisfied_required_capabilities"], [])

    def test_missing_local_runtime_is_not_admissible(self) -> None:
        result = evaluate_assignment_admissibility(
            ["repository_remote_read", "repository_local_checkout", "shell", "python_runtime"],
            ["repository_remote_read", "repository_remote_write", "connector:github"],
        )
        self.assertEqual(result["status"], "NOT_ADMISSIBLE")
        self.assertEqual(result["unsatisfied_required_capabilities"], ["python_runtime", "repository_local_checkout", "shell"])

    def test_complete_chain_passes(self) -> None:
        self.assertEqual(validate_assignment_execution_contract(*valid_chain()), [])

    def assert_contract_rejected(self, assignment: dict[str, object], record: dict[str, object], profile: dict[str, object], fragment: str) -> None:
        errors = validate_assignment_execution_contract(assignment, record, profile)
        self.assertTrue(any(fragment in error for error in errors), msg=str(errors))

    def test_assignment_chain_mismatches_rejected(self) -> None:
        mutations = [
            ("assignment_draft_ref", "UNRELATED", "assignment_draft_ref mismatch"),
            ("admissibility_ref", "ADM-X", "admissibility_ref mismatch"),
            ("capability_profile_ref", "CAP-X", "capability_profile_ref mismatch"),
            ("destination_id", "agent-X", "assignment destination mismatch"),
            ("runtime_identity", "runtime-X", "assignment runtime_identity mismatch"),
            ("required_capabilities", ["shell"], "required_capabilities do not match"),
            ("mandatory_evidence_paths", ["different"], "mandatory_evidence_paths do not match"),
            ("execution_mode", "remote", "execution_mode does not match"),
        ]
        for field, value, fragment in mutations:
            with self.subTest(field=field):
                assignment, record, profile = deepcopy(valid_chain())
                assignment["execution_contract"][field] = value  # type: ignore[index]
                self.assert_contract_rejected(assignment, record, profile, fragment)

    def test_missing_or_blank_draft_binding_rejected(self) -> None:
        for value in [None, ""]:
            assignment, record, profile = deepcopy(valid_chain())
            if value is None:
                del assignment["execution_contract"]["assignment_draft_ref"]  # type: ignore[index]
            else:
                assignment["execution_contract"]["assignment_draft_ref"] = value  # type: ignore[index]
            self.assert_contract_rejected(assignment, record, profile, "assignment_draft_ref")

    def test_non_admissible_and_nonempty_unsatisfied_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        record["status"] = "NOT_ADMISSIBLE"
        record["available_capabilities"] = ["shell"]
        record["unsatisfied_required_capabilities"] = ["python_runtime"]
        profile["available_capabilities"] = ["shell"]
        profile["capability_evidence"] = [{"capability": "shell", "evidence_ref": "EVIDENCE-1"}]
        assignment["execution_contract"]["unsatisfied_required_capabilities"] = ["python_runtime"]  # type: ignore[index]
        self.assert_contract_rejected(assignment, record, profile, "non-ADMISSIBLE")
        self.assert_contract_rejected(assignment, record, profile, "unsatisfied required capabilities")

    def test_profile_overlap_and_missing_evidence_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        profile["unavailable_capabilities"] = ["shell"]
        self.assert_contract_rejected(assignment, record, profile, "both available and unavailable")
        assignment, record, profile = deepcopy(valid_chain())
        profile["capability_evidence"] = []
        self.assert_contract_rejected(assignment, record, profile, "missing evidence")

    def test_incomplete_profile_rejected(self) -> None:
        for field in ["artifact_type", "produced_by_role", "status", "provenance", "related_artifacts", "runtime_identity", "freshness_boundary", "limitations"]:
            with self.subTest(field=field):
                assignment, record, profile = deepcopy(valid_chain())
                del profile[field]
                self.assertTrue(validate_assignment_execution_contract(assignment, record, profile))

    def test_expired_profile_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        profile["freshness_boundary"]["valid_until"] = "2000-01-01T00:00:00Z"  # type: ignore[index]
        self.assert_contract_rejected(assignment, record, profile, "expired")

    def test_unresolved_and_fake_evidence_rejected(self) -> None:
        for evidence_ref in ["UNKNOWN-EVIDENCE", "fabricated"]:
            assignment, record, profile = deepcopy(valid_chain())
            profile["capability_evidence"][0]["evidence_ref"] = evidence_ref  # type: ignore[index]
            self.assert_contract_rejected(assignment, record, profile, "unresolved")

    def test_profile_admissibility_runtime_and_available_mismatch_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        record["runtime_identity"] = "runtime-X"
        self.assert_contract_rejected(assignment, record, profile, "runtime identity mismatch")
        assignment, record, profile = deepcopy(valid_chain())
        record["available_capabilities"] = ["shell"]
        self.assert_contract_rejected(assignment, record, profile, "do not match cited capability profile")

    def test_record_requirement_derivation_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        record["mandatory_actions"][0]["required_capabilities"] = ["shell"]  # type: ignore[index]
        self.assert_contract_rejected(assignment, record, profile, "union of mandatory action requirements")

    def test_cli_requires_complete_arguments(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/executability.py", "--assignment", "a.json"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--assignment requires --record and --profile", result.stderr)

    def test_cli_valid_and_invalid_complete_chain(self) -> None:
        assignment, record, profile = valid_chain()
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for name, value in [("assignment", assignment), ("record", record), ("profile", profile)]:
                path = Path(directory) / f"{name}.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                paths.append(path)
            command = [sys.executable, "tools/executability.py", "--assignment", str(paths[0]), "--record", str(paths[1]), "--profile", str(paths[2])]
            valid = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
            assignment["execution_contract"]["assignment_draft_ref"] = "UNRELATED"  # type: ignore[index]
            paths[0].write_text(json.dumps(assignment), encoding="utf-8")
            invalid = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("assignment_draft_ref mismatch", invalid.stdout)


if __name__ == "__main__":
    unittest.main()
