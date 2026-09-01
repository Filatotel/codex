from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ExecutabilityStructureTest(unittest.TestCase):
    def test_assignment_requires_proven_execution_contract(self) -> None:
        schema = json.loads((ROOT / "schemas/assignment.schema.json").read_text(encoding="utf-8"))
        self.assertIn("execution_contract", schema["required"])
        contract = schema["properties"]["execution_contract"]
        self.assertEqual(contract["properties"]["proof_status"]["const"], "PROVEN")
        self.assertEqual(contract["properties"]["unsatisfied_required_capabilities"]["maxItems"], 0)
        for required in [
            "destination_id",
            "capability_profile_ref",
            "admissibility_ref",
            "required_capabilities",
            "mandatory_evidence_paths",
            "execution_mode",
        ]:
            self.assertIn(required, contract["required"])

    def test_admissibility_schema_fails_closed(self) -> None:
        schema = json.loads((ROOT / "schemas/assignment-admissibility.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["status"]["enum"], ["ADMISSIBLE", "NOT_ADMISSIBLE"])
        serialized = json.dumps(schema)
        self.assertIn('"maxItems": 0', serialized)
        self.assertIn('"minItems": 1', serialized)

    def test_root_router_and_director_require_preflight_before_assign(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        router = (ROOT / "ROUTER.md").read_text(encoding="utf-8")
        director = (ROOT / "roles/control-director/ROLE.md").read_text(encoding="utf-8")
        for text in [agents, router, director]:
            self.assertIn("ASSIGNMENT_NOT_ADMISSIBLE", text)
            self.assertIn("REQUIRED_CAPABILITIES", text)
        self.assertIn("NO ASSIGNMENT WITHOUT EXECUTABILITY PROOF", agents)
        self.assertIn("prove REQUIRED_CAPABILITIES ⊆ AVAILABLE_CAPABILITIES", director)

    def test_engine_manifests_require_destination_preflight(self) -> None:
        software = (ROOT / "engines/production/software/MANIFEST.yaml").read_text(encoding="utf-8")
        verification = (ROOT / "engines/verification/MANIFEST.yaml").read_text(encoding="utf-8")
        research = (ROOT / "engines/research/MANIFEST.yaml").read_text(encoding="utf-8")
        self.assertIn("destination_executability_preflight_passes", software)
        self.assertIn("destination_executability_preflight_passes_for_mandatory_evidence", verification)
        self.assertIn("method_level_machine_only_admission_not_destination_proof", research)

    def test_skill_authoring_requires_execution_contract(self) -> None:
        authoring = (ROOT / "library/skills/skill-authoring/SKILL.md").read_text(encoding="utf-8")
        template = (ROOT / "library/templates/SKILL_TEMPLATE.md").read_text(encoding="utf-8")
        self.assertIn("Execution contract", authoring)
        self.assertIn("Required execution capabilities", template)
        self.assertIn("Supported execution modes", template)
        self.assertIn("ASSIGNMENT_NOT_ADMISSIBLE", template)


if __name__ == "__main__":
    unittest.main()
