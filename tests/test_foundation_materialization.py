from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

from tests.test_executability_parity import schema_accepts


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "engines/foundation/schemas"
SKILL_DIR = ROOT / "engines/foundation/skills"
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
FOUNDATION_SKILLS = (
    "develop-project-seed",
    "define-project-outcome",
    "classify-consequential-unknowns",
    "design-discovery",
)


def load_schema(name: str) -> dict:
    path = SCHEMA_DIR / name
    if not path.is_file():
        raise AssertionError(f"missing Foundation schema: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_skill(name: str) -> str:
    path = SKILL_DIR / name / "SKILL.md"
    if not path.is_file():
        raise AssertionError(f"missing Foundation skill: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


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

    def test_foundation_cognitive_skills_follow_guidance_first_contract(self) -> None:
        names = []
        all_text = []
        for skill_name in FOUNDATION_SKILLS:
            text = load_skill(skill_name)
            all_text.append(text)
            match = re.search(r"^name:\s*(\S+)\s*$", text, re.M)
            self.assertIsNotNone(match, skill_name)
            names.append(match.group(1))
            self.assertEqual(match.group(1), skill_name)
            for heading in ("## Execution contract", "## Thinking guidance", "## Hard invariants", "## Procedure"):
                self.assertIn(heading, text, f"{skill_name}: {heading}")
            lower = text.lower()
            self.assertIn("native", lower, skill_name)
            self.assertTrue("reasoning" in lower or "judgment" in lower, skill_name)
            self.assertIn("durable", lower, skill_name)
            self.assertIn("canon", lower, skill_name)
            self.assertIn("owner", lower, skill_name)

        self.assertEqual(len(names), len(set(names)))
        combined = "\n".join(all_text)
        self.assertNotRegex(combined, r"(?is)(ask|require).{0,80}(at least|minimum)\s+[1-9][0-9]*\s+(questions|fields)")

    def test_develop_project_seed_preserves_source_interpretation_boundaries_and_zero_question_path(self) -> None:
        text = load_skill("develop-project-seed")
        for phrase in (
            "explicit Owner statement",
            "strongly implied context",
            "model working interpretation",
            "model proposal",
            "unresolved material question",
        ):
            self.assertIn(phrase, text)
        self.assertIn("zero clarification questions", text.lower())
        self.assertIn("working interpretation", text.lower())

    def test_project_outcome_does_not_assume_software_or_production(self) -> None:
        text = load_skill("define-project-outcome")
        lower = text.lower()
        for phrase in ("target outcome", "completion condition", "required deliverables", "non-goals"):
            self.assertIn(phrase, lower)
        self.assertIn("software", lower)
        self.assertIn("production", lower)
        self.assertTrue("must not assume" in lower or "do not assume" in lower)

    def test_unknown_classification_is_not_resolution_or_dispatch(self) -> None:
        text = load_skill("classify-consequential-unknowns")
        for classification in UNKNOWN_CLASSES:
            self.assertIn(classification, text)
        lower = text.lower()
        self.assertIn("classification is not resolution", lower)
        self.assertIn("research dispatch", lower)
        self.assertIn("owner decision", lower)
        self.assertIn("architecture authority", lower)
        self.assertIn("non-consequential", lower)

    def test_design_discovery_is_optional_and_creates_no_fourth_artifact(self) -> None:
        text = load_skill("design-discovery")
        lower = text.lower()
        self.assertIn("optional", lower)
        self.assertIn("proposal", lower)
        self.assertIn("architecture", lower)
        self.assertIn("does not create a `design_discovery_result`", lower)
        self.assertNotIn("artifact_type: DESIGN_DISCOVERY_RESULT", text)


if __name__ == "__main__":
    unittest.main()
