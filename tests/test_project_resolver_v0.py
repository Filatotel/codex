from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProjectResolverV0Test(unittest.TestCase):
    def test_ordinary_chat_is_valid_liaison_mode_without_sbc(self) -> None:
        role = (ROOT / "roles/owner-interface/ROLE.md").read_text(encoding="utf-8")
        actionability = (ROOT / "roles/owner-interface/skills/owner-actionability/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("ORDINARY_CHAT", role)
        self.assertIn("Absence of SBC context", actionability)
        self.assertIn("does not itself create `BLOCKED_NO_ADMISSIBLE_SURFACE`", actionability)
        self.assertIn("Never invent SBC Browser", actionability)

    def test_diagnosis_vertical_slice_resolves_to_existing_skill(self) -> None:
        bootstrap = (ROOT / "BOOTSTRAP.md").read_text(encoding="utf-8")
        router = (ROOT / "ROUTER.md").read_text(encoding="utf-8")
        manifest = (ROOT / "engines/production/software/MANIFEST.yaml").read_text(encoding="utf-8")
        workflow = (ROOT / "engines/production/software/workflows/diagnosis.md").read_text(encoding="utf-8")
        skill = ROOT / "engines/production/software/skills/systematic-debugging/SKILL.md"

        self.assertIn("diagnose_software_failure", router)
        self.assertIn("diagnose_software_failure: diagnosis", manifest)
        self.assertIn("systematic-debugging", workflow)
        self.assertTrue(skill.is_file())
        self.assertIn("does not require PAK", bootstrap)
        self.assertIn("does not make diagnosis the default route", bootstrap)


if __name__ == "__main__":
    unittest.main()
