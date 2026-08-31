from __future__ import annotations

import copy
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.research_policy import (
    classify_text,
    validate_question,
    validate_work_package,
    admit_work_package,
    verify_machine_invariant,
    validate_human_research_authorization,
    validate_separate_human_work_package,
)


def base_wp() -> dict:
    return {
        "WORK_PACKAGE_ID": "WP-001",
        "QUESTION_ID": "Q-001",
        "NAMESPACE": "research/default",
        "EXECUTOR_ROLE": "AI_R_MASTER",
        "VERIFIER_ROLE": "AI_R_VERIFIER",
        "MACHINE_EXECUTABLE": True,
        "REQUIRES_THIRD_PARTY_HUMAN": False,
        "REQUIRES_OWNER_MANUAL_RESEARCH": False,
        "REQUIRES_EXTERNAL_REVIEWER": False,
        "REQUIRES_EXTERNAL_HUMAN_REVIEW": False,
        "REQUIRES_NEW_HUMAN_DATA": False,
        "REQUIRES_HUMAN_DATA_COLLECTION": False,
        "CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS": True,
        "OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS": True,
        "EXECUTION_SURFACE": "local machine runtime",
        "SOURCE_ACCESS_METHOD": "public machine-accessible corpus",
        "COMPUTATION_METHOD": "deterministic structural analysis",
        "VERIFICATION_METHOD": "automated reproducibility check",
        "LIMITATIONS": [],
        "PROHIBITED_OVERCLAIMS": ["do not claim direct population measurement"],
        "OWNER_GATE_IF_ANY": None,
    }


class ResearchMachineOnlyPolicyTest(unittest.TestCase):
    def test_01_recruit_30_native_speakers_rejected(self) -> None:
        wp = base_wp()
        wp["COMPUTATION_METHOD"] = "Recruit 30 native speakers and ask them to rate the items."
        result = admit_work_package(wp)
        self.assertEqual(result["ADMISSION_STATUS"], "REJECT_METHOD")
        self.assertEqual(result["ERROR_CODE"], "METHOD_NOT_MACHINE_EXECUTABLE")
        self.assertTrue(any("ACTIVE_DEPENDENCY" in e for e in result["ERRORS"]))

    def test_02_expert_validation_rejected(self) -> None:
        wp = base_wp()
        wp["VERIFICATION_METHOD"] = "Ask an expert to validate terminology."
        self.assertTrue(validate_work_package(wp))

    def test_03_owner_ab_choice_passes(self) -> None:
        wp = base_wp()
        wp["OWNER_GATE_IF_ANY"] = "OWNER_ADJUDICATION"
        wp["LIMITATIONS"] = ["Owner chooses between A/B after the evidence package."]
        self.assertEqual(validate_work_package(wp), [])

    def test_04_published_survey_is_external_evidence(self) -> None:
        findings = classify_text("Use a published study containing 500 survey respondents as pre-existing evidence.")
        self.assertFalse(any(f.classification == "ACTIVE_DEPENDENCY" for f in findings))
        self.assertTrue(any(f.classification == "STATIC_EXTERNAL_SOURCE" for f in findings))

    def test_05_unmeasured_user_preference_passes(self) -> None:
        wp = base_wp()
        wp["LIMITATIONS"] = ["Direct user preference cannot be measured from available public data; result is UNMEASURED_HUMAN_CONSTRUCT."]
        self.assertEqual(validate_work_package(wp), [])

    def test_06_labeled_model_proxy_passes(self) -> None:
        wp = base_wp()
        wp["COMPUTATION_METHOD"] = "MODEL_PROXY ensemble comparison, explicitly labeled as proxy-only."
        wp["LIMITATIONS"] = ["Actual population recognition remains unmeasured."]
        self.assertEqual(validate_work_package(wp), [])

    def test_07_llm_called_human_responses_fails(self) -> None:
        wp = base_wp()
        wp["COMPUTATION_METHOD"] = "Use simulated LLM outputs as human responses."
        self.assertTrue(any("PROXY_OVERCLAIM" in e for e in validate_work_package(wp)))

    def test_08_automated_verifier_passes(self) -> None:
        wp = base_wp()
        wp["VERIFICATION_METHOD"] = "Automated machine verifier checks provenance and reproducibility."
        self.assertEqual(validate_work_package(wp), [])
        summary = verify_machine_invariant(wp)
        self.assertEqual(summary["STATUS"], "PASS")
        self.assertEqual(summary["THIRD_PARTY_HUMAN_DEPENDENCY"], 0)

    def test_09_generic_human_scope_gate_fails(self) -> None:
        wp = base_wp()
        wp["OWNER_GATE_IF_ANY"] = "Human Scope Gate"
        errors = validate_work_package(wp)
        self.assertTrue(any("OWNER_GATE_IF_ANY" in e or "AMBIGUOUS_HUMAN_GATE_TERMINOLOGY" in e for e in errors))

    def test_10_survey_prompt_without_authorization_rejected(self) -> None:
        wp = base_wp()
        wp["SOURCE_ACCESS_METHOD"] = "Deploy a survey to collect human evidence."
        result = admit_work_package(wp)
        self.assertEqual(result["ADMISSION_STATUS"], "REJECT_METHOD")
        self.assertTrue(result["REQUIRE_MACHINE_REDESIGN"])

    def test_11_separate_owner_authorized_human_workstream_is_bounded(self) -> None:
        auth = {
            "CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM": True,
            "PROJECT_ID": "P-1",
            "QUESTION_ID": "Q-H1",
            "REAL_NON_OWNER_HUMANS_MAY_PARTICIPATE": True,
            "SCOPE": "one bounded recognition study",
            "NAMESPACE": "human-research/P-1/Q-H1",
        }
        human_wp = {
            "PROJECT_ID": "P-1",
            "QUESTION_ID": "Q-H1",
            "NAMESPACE": "human-research/P-1/Q-H1",
        }
        self.assertEqual(validate_human_research_authorization(auth), [])
        self.assertEqual(validate_separate_human_work_package(human_wp, auth), [])
        # The same object still cannot enter the default engine.
        default = base_wp()
        default["NAMESPACE"] = human_wp["NAMESPACE"]
        self.assertTrue(validate_work_package(default))

    def test_12_owner_manual_url_collection_fails(self) -> None:
        wp = base_wp()
        wp["REQUIRES_OWNER_MANUAL_RESEARCH"] = True
        wp["SOURCE_ACCESS_METHOD"] = "Owner must manually collect 100 URLs."
        self.assertTrue(validate_work_package(wp))

    def test_13_owner_accept_reject_design_decision_passes(self) -> None:
        wp = base_wp()
        wp["OWNER_GATE_IF_ANY"] = "OWNER_ACCEPTANCE"
        wp["LIMITATIONS"] = ["Owner accepts or rejects the design decision after machine evidence."]
        self.assertEqual(validate_work_package(wp), [])

    def test_14_no_public_evidence_yields_unknown_not_recruitment(self) -> None:
        wp = base_wp()
        wp["SOURCE_ACCESS_METHOD"] = "No suitable public evidence is currently available."
        wp["COMPUTATION_METHOD"] = "Return UNKNOWN / INSUFFICIENT_PUBLIC_EVIDENCE."
        wp["LIMITATIONS"] = ["No direct measurement is claimed."]
        self.assertEqual(validate_work_package(wp), [])

    def test_15_archived_interview_corpus_passes(self) -> None:
        wp = base_wp()
        wp["SOURCE_ACCESS_METHOD"] = "Analyze an archived interview corpus as pre-existing human-derived evidence."
        self.assertEqual(validate_work_package(wp), [])


if __name__ == "__main__":
    unittest.main()
