"""PR target-alignment negative controls for Issue #61."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from tests.test_resolver_transition import transition_bundle, artifact
from tools.executability import validate_director_decision
from tools.resolver_transition import resolve_transition

ROOT = Path(__file__).resolve().parents[1]


def reviewed_bundle(tier="V3"):
    value = transition_bundle()
    director = artifact(value, "DIRECTOR-POST")
    authority = director["transition_authority"]
    gate = {
        "tier": tier,
        "issue_ref": "github:Filatotel/example/issues/42",
        "outcome_claim_id": "business-outcome",
        "delivery_scope": "STAGED" if tier == "V3" else "FULL",
    }
    if tier in {"V3", "V4"}:
        gate.update({
            "target_ref": "canon:approved-target-v2",
            "architecture_claim_id": "architecture-alignment",
            "progress_claim_id": "progress-to-target",
        })
    if tier == "V4":
        gate.update({
            "transition_claim_id": "migration-safety",
            "transition_mode": "DESTRUCTIVE_CUTOVER",
            "owner_decision_ref": "owner:authorized-cutover",
        })
    authority["review_gate"] = gate
    executor = artifact(value, "RESULT-1")
    verifier = artifact(value, "VERIFY-1")
    claim_ids = [gate["outcome_claim_id"]]
    if tier in {"V3", "V4"}:
        claim_ids += [gate["architecture_claim_id"], gate["progress_claim_id"]]
    if tier == "V4":
        claim_ids.append(gate["transition_claim_id"])
    for claim_id in claim_ids:
        executor["claims"].append({"claim_id": claim_id, "claim": f"Confirmed {claim_id}.",
                                   "evidence_refs": ["EVIDENCE-RESULT"]})
        verifier["claim_verdicts"].append({"claim_id": claim_id, "verdict": "CONFIRMED",
                                           "evidence_refs": ["EVIDENCE-RESULT"]})
        authority["verification_target_claim_ids"].append(claim_id)
        authority["acceptance_requirements"].append({
            "requirement_id": "acceptance-" + claim_id,
            "claim_id": claim_id,
            "required_evidence_refs": ["EVIDENCE-RESULT"],
        })
    return value


class TargetAlignmentReviewTest(unittest.TestCase):
    def assert_reason(self, value, reason):
        actual = resolve_transition(value)
        self.assertEqual(actual["reason"], reason, actual)
        self.assertNotEqual(actual["control_state"], "COMPLETE", actual)

    def test_unaffected_technical_v1_does_not_invent_architecture_gate(self):
        self.assertEqual(resolve_transition(transition_bundle())["control_state"], "COMPLETE")

    def test_business_v2_requires_outcome_claim(self):
        value = reviewed_bundle("V2")
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")
        authority = artifact(value, "DIRECTOR-POST")["transition_authority"]
        authority["verification_target_claim_ids"].remove("business-outcome")
        self.assert_reason(value, "TARGET_ALIGNMENT_CONTRACT_MISSING")

    def test_architecture_v3_all_required_claims_prove_stage_only(self):
        value = reviewed_bundle()
        self.assertEqual(validate_director_decision(artifact(value, "DIRECTOR-POST")), [])
        result = resolve_transition(value)
        self.assertEqual((result["control_state"], result["delivery_scope"]), ("COMPLETE", "STAGED"))

    def test_ci_green_cannot_replace_architecture_claim(self):
        value = reviewed_bundle()
        verifier = artifact(value, "VERIFY-1")
        next(v for v in verifier["claim_verdicts"] if v["claim_id"] == "architecture-alignment")["verdict"] = "NOT_PROVEN"
        self.assert_reason(value, "TARGET_ALIGNMENT_NOT_PROVEN")

    def test_progress_to_target_must_be_proven(self):
        value = reviewed_bundle()
        next(v for v in artifact(value, "VERIFY-1")["claim_verdicts"]
             if v["claim_id"] == "progress-to-target")["verdict"] = "QUALIFIED"
        self.assert_reason(value, "TARGET_ALIGNMENT_NOT_PROVEN")

    def test_claim_must_be_in_director_acceptance_not_just_tests(self):
        value = reviewed_bundle()
        authority = artifact(value, "DIRECTOR-POST")["transition_authority"]
        authority["acceptance_requirements"] = [
            r for r in authority["acceptance_requirements"] if r["claim_id"] != "progress-to-target"
        ]
        self.assert_reason(value, "TARGET_ALIGNMENT_CONTRACT_MISSING")

    def test_target_evidence_missing_is_not_pass(self):
        value = reviewed_bundle()
        next(v for v in artifact(value, "VERIFY-1")["claim_verdicts"]
             if v["claim_id"] == "architecture-alignment")["evidence_refs"] = []
        self.assert_reason(value, "TARGET_ALIGNMENT_EVIDENCE_MISSING")

    def test_target_ref_absent_fails_closed(self):
        value = reviewed_bundle()
        del artifact(value, "DIRECTOR-POST")["transition_authority"]["review_gate"]["target_ref"]
        self.assert_reason(value, "MALFORMED_DIRECTOR_DECISION")

    def test_review_gate_cannot_turn_off_independent_verification(self):
        value = reviewed_bundle("V2")
        artifact(value, "DIRECTOR-POST")["transition_authority"]["verification_required"] = False
        self.assert_reason(value, "MALFORMED_DIRECTOR_DECISION")

    def test_v4_destructive_requires_owner_authority_and_transition_evidence(self):
        value = reviewed_bundle("V4")
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")
        gate = artifact(value, "DIRECTOR-POST")["transition_authority"]["review_gate"]
        del gate["owner_decision_ref"]
        self.assert_reason(value, "MALFORMED_DIRECTOR_DECISION")
        gate["owner_decision_ref"] = "owner:authorized-cutover"
        next(v for v in artifact(value, "VERIFY-1")["claim_verdicts"]
             if v["claim_id"] == "migration-safety")["verdict"] = "NOT_PROVEN"
        self.assert_reason(value, "TARGET_ALIGNMENT_NOT_PROVEN")

    def test_exact_state_drift_still_blocks_promoted_claims(self):
        value = reviewed_bundle()
        artifact(value, "STATE-OBS-1")["state_identity"] = "git:changed-head"
        self.assert_reason(value, "RELEVANT_PROOF_STALE")

    def test_schema_declares_same_elevated_contract(self):
        schema = json.loads((ROOT / "schemas/director-decision.schema.json").read_text())
        gate = schema["properties"]["transition_authority"]["properties"]["review_gate"]
        self.assertEqual(set(gate["properties"]["tier"]["enum"]), {"V2", "V3", "V4"})
        self.assertIn("outcome_claim_id", gate["required"])
        self.assertEqual(len(gate["allOf"]), 3)


if __name__ == "__main__":
    unittest.main()
