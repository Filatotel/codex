from __future__ import annotations

from pathlib import Path
import unittest

from tests.test_resolver_spawn import bundle
from tools.resolver_spawn import resolve_spawn


ROOT = Path(__file__).resolve().parents[1]
FOUNDATION_OUTPUTS = [
    "foundation:project-seed",
    "foundation:project-outcome",
    "foundation:consequential-unknown-map",
]


def foundation_bundle() -> dict:
    value = bundle("foundation", "form_project_foundation", "form_project_foundation")
    owner_material = {
        "artifact_type": "OWNER_SUPPLIED_PROJECT_MATERIAL",
        "artifact_id": "OWNER-MATERIAL-1",
        "provenance": ["OWNER/K0"],
    }
    value["artifacts"].append(owner_material)
    value["workflow_prerequisite_bindings"] = {
        "exact_owner_or_supplied_project_material": owner_material["artifact_id"]
    }
    return value


class FoundationResolverIntegrationTest(unittest.TestCase):
    def test_foundation_uses_generic_spawn_with_three_durable_outputs(self) -> None:
        value = foundation_bundle()
        value["selected_prerequisite_actions"] = [
            {
                "action_id": "foundation-durable-working-state",
                "required_capabilities": ["durable_artifact_write"],
                "evidence_path": "three Foundation working artifacts via declared durable system of record",
            }
        ]
        value["assignment_draft_semantics"]["required_durable_outputs"] = list(FOUNDATION_OUTPUTS)
        value["assignment_draft_semantics"]["durable_system_of_record_ref"] = "SOR-FOUNDATION-V0"

        result = resolve_spawn(value)

        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        self.assertEqual(result["engine_id"], "foundation")
        self.assertEqual(result["workflow_id"], "form_project_foundation")
        self.assertEqual(result["workflow_prerequisite_refs"], ["OWNER-MATERIAL-1"])
        self.assertEqual(result["assignment_admissibility"]["status"], "ADMISSIBLE")
        self.assertIn("OWNER-MATERIAL-1", result["assignment_admissibility"]["related_artifacts"])
        self.assertIn("durable_artifact_write", result["assignment_admissibility"]["required_capabilities"])
        self.assertEqual(result["assignment"]["required_durable_outputs"], FOUNDATION_OUTPUTS)
        self.assertEqual(result["assignment"]["durable_system_of_record_ref"], "SOR-FOUNDATION-V0")

    def test_foundation_prerequisite_is_real_and_cannot_be_masked_by_durable_action(self) -> None:
        value = bundle("foundation", "form_project_foundation", "form_project_foundation")
        value["selected_prerequisite_actions"] = [
            {
                "action_id": "foundation-durable-working-state",
                "required_capabilities": ["durable_artifact_write"],
                "evidence_path": "three Foundation working artifacts via declared durable system of record",
            }
        ]
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "WORKFLOW_PREREQUISITE_REQUIRED"))
        self.assertEqual(result["workflow_contract_details"]["missing_requirement"], "exact_owner_or_supplied_project_material")
        self.assertNotIn("assignment", result)

    def test_foundation_has_no_special_spawn_runtime(self) -> None:
        source = (ROOT / "tools/resolver_spawn.py").read_text(encoding="utf-8")
        self.assertNotIn("resolve_foundation_spawn", source)
        self.assertNotIn("foundation_spawn", source)

    def test_generic_durable_contract_is_the_readiness_boundary(self) -> None:
        workflow = (ROOT / "engines/foundation/workflows/form-project-foundation.md").read_text(encoding="utf-8")
        protocol = (ROOT / "protocols/artifacts.md").read_text(encoding="utf-8")
        self.assertIn("required_durable_outputs", workflow)
        self.assertIn("durable_output_refs", workflow)
        self.assertIn("independent readback", workflow.lower())
        self.assertIn("reference coverage and readback are distinct gates", protocol.lower())
        self.assertIn("local/session copy", workflow.lower())


if __name__ == "__main__":
    unittest.main()
