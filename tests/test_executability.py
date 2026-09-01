from __future__ import annotations

import unittest

from tools.executability import (
    evaluate_assignment_admissibility,
    validate_admissibility_against_profile,
    validate_admissibility_record,
    validate_capability_profile,
)


class ExecutabilityContractTest(unittest.TestCase):
    def test_required_subset_available_is_admissible(self) -> None:
        result = evaluate_assignment_admissibility(
            ["repository_remote_read", "repository_remote_write"],
            ["repository_remote_write", "repository_remote_read", "connector:github"],
        )
        self.assertEqual(result["status"], "ADMISSIBLE")
        self.assertEqual(result["unsatisfied_required_capabilities"], [])

    def test_missing_local_runtime_is_not_admissible(self) -> None:
        result = evaluate_assignment_admissibility(
            ["repository_remote_read", "repository_local_checkout", "shell", "python_runtime"],
            ["repository_remote_read", "repository_remote_write", "connector:github"],
        )
        self.assertEqual(result["status"], "NOT_ADMISSIBLE")
        self.assertEqual(
            result["unsatisfied_required_capabilities"],
            ["python_runtime", "repository_local_checkout", "shell"],
        )

    def test_playwright_is_not_browser_free_fallback(self) -> None:
        result = evaluate_assignment_admissibility(
            ["repository_local_checkout", "node_runtime", "package_install", "playwright_runtime"],
            ["repository_remote_read", "repository_remote_write", "connector:github"],
        )
        self.assertEqual(result["status"], "NOT_ADMISSIBLE")
        self.assertIn("playwright_runtime", result["unsatisfied_required_capabilities"])

    def test_record_status_cannot_claim_admissible_with_missing_capability(self) -> None:
        record = {
            "status": "ADMISSIBLE",
            "mandatory_actions": [
                {
                    "action_id": "run_local_validator",
                    "required_capabilities": ["shell", "python_runtime"],
                    "evidence_path": "python tools/validate_structure.py",
                }
            ],
            "required_capabilities": ["shell", "python_runtime"],
            "available_capabilities": ["python_runtime"],
            "unsatisfied_required_capabilities": [],
            "mandatory_evidence_paths": ["python tools/validate_structure.py"],
        }
        errors = validate_admissibility_record(record)
        self.assertTrue(any("status drift" in error for error in errors), msg=str(errors))
        self.assertTrue(any("unsatisfied_required_capabilities drift" in error for error in errors), msg=str(errors))

    def test_record_cannot_underdeclare_mandatory_action_capabilities(self) -> None:
        record = {
            "status": "ADMISSIBLE",
            "mandatory_actions": [
                {
                    "action_id": "run_tests",
                    "required_capabilities": ["repository_local_checkout", "shell", "python_runtime"],
                    "evidence_path": "python -m unittest",
                }
            ],
            "required_capabilities": ["python_runtime"],
            "available_capabilities": ["python_runtime"],
            "unsatisfied_required_capabilities": [],
            "mandatory_evidence_paths": ["python -m unittest"],
        }
        errors = validate_admissibility_record(record)
        self.assertTrue(any("do not equal union" in error for error in errors), msg=str(errors))

    def test_profile_requires_evidence_for_every_available_capability(self) -> None:
        profile = {
            "artifact_id": "CAP-1",
            "destination_id": "agent-1",
            "available_capabilities": ["repository_remote_read", "connector:github"],
            "unavailable_capabilities": ["shell"],
            "capability_evidence": [
                {"capability": "repository_remote_read", "evidence_ref": "github-readback"}
            ],
        }
        errors = validate_capability_profile(profile)
        self.assertTrue(any("missing evidence" in error for error in errors), msg=str(errors))

    def test_admissibility_is_bound_to_exact_profile(self) -> None:
        profile = {
            "artifact_id": "CAP-1",
            "destination_id": "agent-1",
            "available_capabilities": ["repository_remote_read", "connector:github"],
            "unavailable_capabilities": ["shell"],
            "capability_evidence": [
                {"capability": "repository_remote_read", "evidence_ref": "github-readback"},
                {"capability": "connector:github", "evidence_ref": "github-connector-discovery"},
            ],
        }
        record = {
            "status": "ADMISSIBLE",
            "destination_id": "agent-1",
            "capability_profile_ref": "CAP-1",
            "mandatory_actions": [
                {
                    "action_id": "read_remote_state",
                    "required_capabilities": ["repository_remote_read"],
                    "evidence_path": "GitHub repository readback",
                }
            ],
            "required_capabilities": ["repository_remote_read"],
            "available_capabilities": ["repository_remote_read", "connector:github"],
            "unsatisfied_required_capabilities": [],
            "mandatory_evidence_paths": ["GitHub repository readback"],
        }
        self.assertEqual(validate_admissibility_against_profile(record, profile), [])

        record["available_capabilities"] = ["repository_remote_read", "shell"]
        errors = validate_admissibility_against_profile(record, profile)
        self.assertTrue(any("do not match cited capability profile" in error for error in errors), msg=str(errors))


if __name__ == "__main__":
    unittest.main()
