from __future__ import annotations

import copy
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.research_policy import (
    FATAL_FINDINGS,
    classify_text,
    machine_only_regression_results,
    validate_experiment,
    validate_human_research_authorization,
    validate_method_freeze,
    validate_question,
    validate_separate_human_work_package,
    validate_source,
    validate_work_package,
)


def base_wp() -> dict:
    return {
        "WORK_PACKAGE_ID":"WP-001","QUESTION_ID":"Q-001","NAMESPACE":"research/default",
        "EXECUTOR_ROLE":"AI_R_MASTER","VERIFIER_ROLE":"AI_R_VERIFIER","MACHINE_EXECUTABLE":True,
        "REQUIRES_THIRD_PARTY_HUMAN":False,"REQUIRES_OWNER_MANUAL_RESEARCH":False,
        "REQUIRES_EXTERNAL_REVIEWER":False,"REQUIRES_EXTERNAL_HUMAN_REVIEW":False,
        "REQUIRES_NEW_HUMAN_DATA":False,"REQUIRES_HUMAN_DATA_COLLECTION":False,
        "CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS":True,"OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS":True,
        "EXECUTION_SURFACE":"local machine runtime","SOURCE_ACCESS_METHOD":"public machine-accessible corpus",
        "COMPUTATION_METHOD":"deterministic structural analysis","VERIFICATION_METHOD":"automated reproducibility check",
        "LIMITATIONS":[],"PROHIBITED_OVERCLAIMS":["Do not claim direct population measurement."],"OWNER_GATE_IF_ANY":None,
    }


def base_question() -> dict:
    return {
        "QUESTION_ID":"Q-001","QUESTION":"What structural pattern is supported?","TARGET_CONSTRUCT":"structural pattern",
        "MACHINE_EXECUTABLE":True,"AVAILABLE_MACHINE_METHODS":["deterministic corpus analysis"],
        "AVAILABLE_EXTERNAL_PREEXISTING_EVIDENCE":["Published survey may be used as static evidence."],
        "REQUIRES_THIRD_PARTY_HUMAN":False,"REQUIRES_OWNER_MANUAL_RESEARCH":False,
        "REQUIRES_EXTERNAL_HUMAN_REVIEW":False,"REQUIRES_HUMAN_DATA_COLLECTION":False,
        "DIRECT_MEASUREMENT_POSSIBLE":False,"PROXY_MEASUREMENT_POSSIBLE":True,
        "EXPECTED_LIMITATION":"Direct population measurement remains unavailable.","OWNER_DECISION_COMPONENT":None,
        "CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS":True,"OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS":True,
        "ADMISSION_STATUS":"ADMITTED_MACHINE_RESEARCH",
    }


def owner_auth_pair() -> tuple[dict, dict]:
    auth = {
        "AUTHORIZATION_ID":"HRA-001","OWNER_DECISION_RECORD_REF":"ODR-001","OWNER_AUTHORITY_ROLE":"OWNER_K0",
        "PROJECT_ID":"P-1","QUESTION_ID":"Q-H1","SCOPE":"one bounded recognition study",
        "NAMESPACE":"human-research/P-1/Q-H1","NON_TRANSITIVE":True,
        "CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM":True,"REAL_NON_OWNER_HUMANS_MAY_PARTICIPATE":True,
        "DEFAULT_RESEARCH_MODE_UNCHANGED":True,
    }
    record = {
        "artifact_type":"OWNER_DECISION_RECORD","artifact_id":"ODR-001","produced_by_role":"owner-interface",
        "assignment_id":"A-OWNER-001","input_state_ref":"state:pre-human-research","status":"RECORDED",
        "provenance":["OWNER_K0 explicit authorization decision"],"related_artifacts":["P-1","Q-H1"],
        "question_ref":"Q-H1","options_presented":["AUTHORIZE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM","DO_NOT_AUTHORIZE"],
        "selected_option":"AUTHORIZE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM","owner_constraints":["bounded scope only"],
        "consequences_acknowledged":["default Research remains machine-only"],"authority_role":"OWNER_K0",
        "decision_kind":"CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM","project_id":"P-1","authorized_question_id":"Q-H1",
        "authorized_scope":"one bounded recognition study","authorized_namespace":"human-research/P-1/Q-H1",
        "authorization_id":"HRA-001","non_transitive":True,"default_research_mode_unchanged":True,
    }
    return auth, record


def resolver_for(record: dict):
    return lambda ref: record if ref == record.get("artifact_id") else None


def base_experiment() -> dict:
    return {
        "EXPERIMENT_ID":"EXP-1","RUN_ID":"RUN-1","METHOD_VERSION":"1.0","METHOD_STATUS":"FROZEN",
        "FREEZE_ID":"FRZ-1","INPUT_DATASET":"public machine-readable corpus","INPUT_VERSION":"1",
        "INPUT_HASH":"sha256:input","MODEL_OR_TOOL":"python","MODEL_OR_TOOL_VERSION":"3",
        "PROMPT_OR_RULESET_VERSION":"rules-1","RANDOM_SEED":1,"N_RUNS":1,"BENCHMARK_SET":[],"HOLDOUT_SET":[],
        "PERTURBATION_SET":[],"ADVERSARIAL_CASES":[],"ERROR_METRIC":"exact mismatch","AGGREGATION_METHOD":"deterministic",
        "UNCERTAINTY_METHOD":"sensitivity bounds","CROSS_METHOD_AGREEMENT":"not applicable",
        "CROSS_MODEL_DISAGREEMENT":"not applicable","OUTPUT_HASH":"sha256:output","REPRODUCTION_POINTER":"runs/RUN-1",
        "LIMITATIONS":["Proxy only."],"PROHIBITED_OVERCLAIMS":["Do not claim direct population recognition."],
    }


def base_freeze() -> dict:
    return {
        "FREEZE_ID":"FRZ-1","QUESTION_ID":"Q-1","METHOD_VERSION":"1.0","METHOD_STATUS":"FROZEN",
        "INPUT_IDENTITY":"public corpus v1","METHOD":"deterministic computational analysis","MODEL_OR_TOOL_VERSION":"python-3",
        "PROMPT_OR_RULESET_VERSION":"rules-1","DATASET_SAMPLING":"deterministic full-corpus pass","RANDOM_SEED_POLICY":"fixed seed",
        "METRICS":["exact agreement"],"AGGREGATION":"mean","THRESHOLDS":{"minimum":0.8},"LIMITATIONS":["Proxy only."],
        "PLANNED_SENSITIVITY_ANALYSIS":"parameter sweep","METHOD_FROZEN":True,"MACHINE_EXECUTABLE":True,
        "REQUIRES_THIRD_PARTY_HUMAN":False,"REQUIRES_OWNER_MANUAL_RESEARCH":False,
        "REQUIRES_EXTERNAL_HUMAN_REVIEW":False,"REQUIRES_HUMAN_DATA_COLLECTION":False,
    }


class ResearchMachineOnlyPolicyTest(unittest.TestCase):
    def test_T01_T42_bounded_regression_matrix(self) -> None:
        results = machine_only_regression_results()
        self.assertEqual(set(results), {f"T{i:02d}" for i in range(1,43)})
        self.assertEqual({k:v for k,v in results.items() if v != "PASS"}, {}, msg=str(results))

    def test_clause_action_classifier_preserves_mixed_findings(self) -> None:
        classes = {f.classification for f in classify_text("Human recruitment is prohibited; nevertheless recruit 20 speakers.")}
        self.assertIn("EXPLICIT_PROHIBITION", classes); self.assertIn("ACTIVE_DEPENDENCY", classes)
        classes = {f.classification for f in classify_text("Use a published survey, then recruit 20 respondents.")}
        self.assertIn("STATIC_EXTERNAL_SOURCE", classes); self.assertIn("ACTIVE_DEPENDENCY", classes)
        classes = {f.classification for f in classify_text("Analyze archived interviews and interview five new speakers.")}
        self.assertIn("STATIC_EXTERNAL_SOURCE", classes); self.assertIn("ACTIVE_DEPENDENCY", classes)

    def test_owner_user_control_and_prohibition_text_are_non_fatal(self) -> None:
        cases = (
            "Ask the user again if required project authority is missing.",
            "Contact the user for the missing repository identifier.",
            "Consult Owner/K0 before accepting the project decision.",
            "Never recruit human participants.",
            "This workflow never creates authority to recruit humans.",
            "Human annotation is prohibited.",
            "No third-party human research is allowed.",
            "The legacy workflow used human annotation before retirement.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertFalse(any(f.classification in FATAL_FINDINGS for f in classify_text(text)), msg=str(classify_text(text)))

    def test_third_party_annotation_rating_coding_and_crowd_labor_are_fatal(self) -> None:
        cases = (
            "Hire five human annotators to label the dataset.",
            "Assign human annotators to label the dataset.",
            "Use three human raters to score the outputs.",
            "Use human raters to score the responses.",
            "Employ coders to code the interview responses.",
            "Employ human coders to code the samples.",
            "Contract crowdworkers to classify the samples.",
            "Contract crowdworkers to classify the dataset.",
            "Have external reviewers rate every generated item.",
            "The legacy pipeline requires human annotation for every new sample.",
            "In the legacy pipeline, human annotation remains mandatory.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertTrue(any(f.classification == "ACTIVE_DEPENDENCY" for f in classify_text(text)), msg=str(classify_text(text)))

    def test_question_recursively_checks_semantic_fields(self) -> None:
        q = base_question(); q["AVAILABLE_MACHINE_METHODS"] = ["deterministic pass", ["Recruit native speakers"]]
        self.assertTrue(validate_question(q))
        q = base_question(); q["AVAILABLE_EXTERNAL_PREEXISTING_EVIDENCE"] = ["Published survey; then recruit new respondents."]
        self.assertTrue(validate_question(q))

    def test_default_objects_reject_undeclared_payloads(self) -> None:
        wp = base_wp(); wp["PARTICIPANT_PLAN"] = "Recruit 50 speakers."; self.assertTrue(validate_work_package(wp))
        wp = base_wp(); wp["METADATA"] = {"execution":{"reviewers":"external experts"}}; self.assertTrue(validate_work_package(wp))

    def test_authorization_requires_governed_owner_resolver(self) -> None:
        auth, record = owner_auth_pair()
        self.assertTrue(validate_human_research_authorization(auth))
        self.assertEqual(validate_human_research_authorization(auth, resolver_for(record)), [])
        fake = copy.deepcopy(auth); fake["OWNER_DECISION_RECORD_REF"] = "ODR-NOT-FOUND"
        self.assertTrue(validate_human_research_authorization(fake, resolver_for(record)))
        for field,value in (("project_id","P-OTHER"),("authorized_question_id","Q-OTHER"),("authorized_scope","broader scope"),("authorized_namespace","human-research/P-1/OTHER")):
            bad = copy.deepcopy(record); bad[field] = value
            self.assertTrue(validate_human_research_authorization(auth, resolver_for(bad)), msg=field)

    def test_genuine_owner_authorization_passes_only_separate_namespace(self) -> None:
        auth, record = owner_auth_pair(); resolver = resolver_for(record)
        human_wp = {"PROJECT_ID":"P-1","QUESTION_ID":"Q-H1","NAMESPACE":"human-research/P-1/Q-H1"}
        self.assertEqual(validate_separate_human_work_package(human_wp, auth, resolver), [])
        default = base_wp(); default["NAMESPACE"] = human_wp["NAMESPACE"]
        self.assertTrue(validate_work_package(default))

    def test_source_provenance_fails_closed(self) -> None:
        source = {"SOURCE_ID":"SRC-1","PROVENANCE_CLASS":"EXTERNAL_PREEXISTING_HUMAN_DATA","ORIGIN":"EXTERNAL_PREEXISTING","HUMAN_ORIGIN":True,"PROJECT_GENERATION_PROHIBITED":False,"DESCRIPTION":"Published survey dataset."}
        self.assertTrue(validate_source(source))
        source = {"SOURCE_ID":"SRC-2","PROVENANCE_CLASS":"OTHER","ORIGIN":"PROJECT_MACHINE_GENERATED","HUMAN_ORIGIN":False,"PROJECT_GENERATION_PROHIBITED":False,"DESCRIPTION":"Recruit participants and collect new human responses."}
        self.assertTrue(validate_source(source))

    def test_experiment_semantics_ignore_keys_but_not_values(self) -> None:
        e = base_experiment(); e["INPUT_DATASET"] = "Recruit 20 participants and collect responses."; self.assertTrue(validate_experiment(e))
        e = base_experiment(); e["INPUT_DATASET"] = {"metadata":{"collection_plan":{"participants":"Recruit 20 participants."}}}; self.assertTrue(validate_experiment(e))
        e = base_experiment(); e["INPUT_DATASET"] = "Archived public interview corpus."; self.assertEqual(validate_experiment(e), [])

    def test_method_freeze_requires_machine_only_semantics(self) -> None:
        f = base_freeze(); f["METHOD"] = "Recruit 50 speakers and survey them."; self.assertTrue(validate_method_freeze(f))
        f = base_freeze(); f["INPUT_IDENTITY"] = {"metadata":{"collection_plan":"Recruit 20 participants."}}; self.assertTrue(validate_method_freeze(f))
        self.assertEqual(validate_method_freeze(base_freeze()), [])


if __name__ == "__main__": unittest.main()
