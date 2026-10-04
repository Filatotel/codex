from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from tests.test_executability_parity import schema_accepts


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "engines/foundation/schemas"
ENVELOPE = {
    "artifact_type",
    "artifact_id",
    "produced_by_role",
    "assignment_id",
    "input_state_ref",
    "status",
    "provenance",
    "related_artifacts",
}
UNKNOWN_CLASSES = {
    "OWNER_PREFERENCE",
    "EXTERNAL_FACT",
    "FEASIBILITY",
    "ARCHITECTURE_DECISION",
    "IMPLEMENTATION_DEPENDENT",
    "NICE_TO_KNOW",
}


def load_schema(name: str) -> dict:
    path = SCHEMA_DIR / name
    if not path.is_file():
        raise AssertionError(f"missing Foundation schema: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def common(artifact_type: str, artifact_id: str) -> dict:
    return {
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "produced_by_role": "executor",
        "assignment_id": "ASSIGN-FOUNDATION-1",
        "input_state_ref": "OWNER-REQUEST-1",
        "status": "WORKING",
        "provenance": ["OWNER-REQUEST-1"],
        "related_artifacts": [],
        "authoritative": False,
    }


class FoundationMaterializationTest(unittest.TestCase):
    def test_foundation_schemas_use_common_envelope_and_are_non_authoritative(self) -> None:
        cases = {
            "project-seed.schema.json": {
                **common("PROJECT_SEED", "SEED-1"),
                "working_summary": "A working interpretation of the project.",
            },
            "project-outcome.schema.json": {
                **common("PROJECT_OUTCOME", "OUTCOME-1"),
                "target_outcome": "A governed project concept.",
                "completion_condition": None,
                "required_deliverables": [],
                "requires_downstream_realization": "UNKNOWN",
            },
            "consequential-unknown-map.schema.json": {
                **common("CONSEQUENTIAL_UNKNOWN_MAP", "UNKNOWN-MAP-1"),
                "items": [],
            },
        }

        for name, value in cases.items():
            with self.subTest(schema=name):
                schema = load_schema(name)
                self.assertTrue(ENVELOPE.issubset(set(schema["required"])))
                self.assertIn("authoritative", schema["required"])
                self.assertEqual(schema["properties"]["artifact_type"]["const"], value["artifact_type"])
                self.assertEqual(schema["properties"]["status"]["const"], "WORKING")
                self.assertEqual(schema["properties"]["authoritative"]["const"], False)
                self.assertFalse(schema.get("additionalProperties", True))
                self.assertTrue(schema_accepts(value, schema), name)

                authoritative = deepcopy(value)
                authoritative["authoritative"] = True
                self.assertFalse(schema_accepts(authoritative, schema), name)

    def test_consequential_unknown_map_has_exact_v0_classification_vocabulary(self) -> None:
        schema = load_schema("consequential-unknown-map.schema.json")
        item_schema = schema["properties"]["items"]["items"]
        self.assertFalse(item_schema.get("additionalProperties", True))
        self.assertEqual(set(item_schema["properties"]["classification"]["enum"]), UNKNOWN_CLASSES)
        self.assertEqual(set(item_schema["properties"]["state"]["enum"]), {"OPEN", "DEFERRED"})

        for classification in UNKNOWN_CLASSES:
            value = {
                **common("CONSEQUENTIAL_UNKNOWN_MAP", f"MAP-{classification}"),
                "items": [
                    {
                        "id": "U-1",
                        "question": "A material unresolved question?",
                        "classification": classification,
                        "why_it_matters": "It may change the project or next action.",
                        "state": "OPEN",
                    }
                ],
            }
            self.assertTrue(schema_accepts(value, schema), classification)

    def test_foundation_artifact_protocol_does_not_promote_working_state_to_common_authority(self) -> None:
        protocol = (ROOT / "protocols/artifacts.md").read_text(encoding="utf-8")
        self.assertIn("PROJECT_SEED", protocol)
        self.assertIn("PROJECT_OUTCOME", protocol)
        self.assertIn("CONSEQUENTIAL_UNKNOWN_MAP", protocol)
        self.assertIn("non-authoritative", protocol.lower())
        common_types = protocol.split("## Required common artifact types", 1)[1].split(
            "## Engine-owned Foundation working artifacts", 1
        )[0]
        for artifact_type in ("PROJECT_SEED", "PROJECT_OUTCOME", "CONSEQUENTIAL_UNKNOWN_MAP"):
            self.assertNotIn(f"`{artifact_type}`", common_types)


if __name__ == "__main__":
    unittest.main()
