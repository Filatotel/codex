from __future__ import annotations

import unittest

from tools.executability import evaluate_assignment_admissibility, validate_admissibility_record


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
            "required_capabilities": ["shell", "python_runtime"],
            "available_capabilities": ["python_runtime"],
            "unsatisfied_required_capabilities": [],
        }
        errors = validate_admissibility_record(record)
        self.assertTrue(any("status drift" in error for error in errors), msg=str(errors))
        self.assertTrue(any("unsatisfied_required_capabilities drift" in error for error in errors), msg=str(errors))


if __name__ == "__main__":
    unittest.main()
