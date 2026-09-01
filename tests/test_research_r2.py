from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.research_policy import classify_text, lint_active_repository


def has_active(text: str) -> bool:
    return any(f.classification == "ACTIVE_DEPENDENCY" for f in classify_text(text))


class ResearchKernelR2RegressionTest(unittest.TestCase):
    def test_R2_T01_human_annotators(self) -> None:
        self.assertTrue(has_active("Hire five human annotators to label the dataset."))

    def test_R2_T02_human_raters(self) -> None:
        self.assertTrue(has_active("Use human raters to score outputs."))

    def test_R2_T03_external_coders(self) -> None:
        self.assertTrue(has_active("Have external coders classify responses."))

    def test_R2_T04_crowdsource_annotation(self) -> None:
        self.assertTrue(has_active("Crowdsource annotation of the corpus."))

    def test_R2_T05_prohibition_passes(self) -> None:
        findings = classify_text("Do not use human annotators.")
        self.assertFalse(any(f.classification == "ACTIVE_DEPENDENCY" for f in findings))
        self.assertTrue(any(f.classification == "EXPLICIT_PROHIBITION" for f in findings))

    def test_R2_T06_archived_annotation_passes(self) -> None:
        findings = classify_text("Archived human annotations may be analyzed.")
        self.assertFalse(any(f.classification == "ACTIVE_DEPENDENCY" for f in findings))
        self.assertTrue(any(f.classification == "STATIC_EXTERNAL_SOURCE" for f in findings))

    def test_R2_T07_mixed_prohibition_does_not_erase_action(self) -> None:
        self.assertTrue(has_active("Human annotation is prohibited; nevertheless hire five annotators."))

    def test_R2_T08_lint_allows_control_prohibition_and_retired_text(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text(
                "Never creates authority to recruit humans.\n"
                "If required metadata is missing, ask the user again.\n"
                "Do not use human annotators.\n"
                "The legacy workflow used human coders but is retired.\n",
                encoding="utf-8",
            )
            self.assertEqual(lint_active_repository(root), [])

    def test_R2_T09_lint_rejects_injected_active_human_research(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text(
                "Hire five human annotators to label the dataset.", encoding="utf-8"
            )
            self.assertTrue(lint_active_repository(root))

    def test_additional_required_human_labor_forms(self) -> None:
        for text in (
            "Send the samples to crowdworkers for labeling.",
            "Contract human reviewers to rate model quality.",
            "Employ human coders to classify the responses.",
            "Outsource the samples to human annotators for labeling.",
        ):
            with self.subTest(text=text):
                self.assertTrue(has_active(text))


if __name__ == "__main__":
    unittest.main()
