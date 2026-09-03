"""Phase-2 gate: prove the existing control surfaces compose as one bounded loop.

External executor work is deliberately represented by its governed result artifact;
all pre-spawn decisions run through the production ``resolve_spawn`` entrypoint.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import unittest

from tests.test_resolver_spawn import bundle
from tools.resolver_spawn import resolve_spawn


ROOT = Path(__file__).resolve().parents[1]
BATONS = {"ASSIGN", "WAIT", "ESCALATE", "COMPLETE"}


def schema(name: str) -> dict[str, object]:
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def assert_required_shape(test: unittest.TestCase, artifact: dict[str, object], schema_name: str) -> None:
    """Check the closed identity/role/status boundary used by result contracts."""
    contract = schema(schema_name)
    test.assertFalse(set(contract["required"]) - set(artifact))
    for field, rules in contract["properties"].items():
        if field not in artifact:
            continue
        if "const" in rules:
            test.assertEqual(artifact[field], rules["const"])
        if "enum" in rules:
            test.assertIn(artifact[field], rules["enum"])


def executor_result(assignment_id: str, engine: str) -> dict[str, object]:
    return {
        "artifact_type": "EXECUTOR_RESULT", "artifact_id": f"EXEC-{engine}",
        "produced_by_role": "executor", "assignment_id": assignment_id,
        "input_state_ref": "state-1", "status": "COMPLETE",
        "provenance": [assignment_id], "related_artifacts": [assignment_id],
        "resulting_state_refs": [f"state-after-{engine}"],
        "evidence_refs": [f"evidence-{engine}"], "deferred_findings": [],
        "limitations": [], "claims": [{"claim_id": "work-produced", "claim": "bounded work was produced"}],
    }


def verification_result(executor: dict[str, object], *, proven: bool = True) -> dict[str, object]:
    verdict = "CONFIRMED" if proven else "NOT_PROVEN"
    return {
        "artifact_type": "VERIFICATION_RESULT", "artifact_id": f"VERIFY-{executor['artifact_id']}",
        "produced_by_role": "control-verifier", "assignment_id": executor["assignment_id"],
        "input_state_ref": executor["resulting_state_refs"][0], "status": verdict,
        "provenance": [executor["artifact_id"]], "related_artifacts": [executor["artifact_id"]],
        "executor_result_ref": executor["artifact_id"],
        "claim_verdicts": [{"claim_id": "work-produced", "verdict": verdict,
                            "evidence_refs": executor["evidence_refs"] if proven else []}],
        "additional_findings": [], "evidence_gaps": [] if proven else ["independent evidence unavailable"],
    }


def director_result(executor: dict[str, object], verification: dict[str, object]) -> dict[str, object]:
    complete = verification["status"] == "CONFIRMED"
    return {
        "artifact_type": "DIRECTOR_DECISION", "artifact_id": f"DIRECT-{executor['artifact_id']}",
        "produced_by_role": "control-director", "assignment_id": executor["assignment_id"],
        "input_state_ref": verification["input_state_ref"], "status": "DECIDED",
        "provenance": [executor["artifact_id"], verification["artifact_id"]],
        "related_artifacts": [executor["artifact_id"], verification["artifact_id"]],
        "executor_result_ref": executor["artifact_id"],
        "verification_result_ref": verification["artifact_id"],
        "control_state": "COMPLETE" if complete else "WAIT",
        "decision": "accept verified result" if complete else "wait for required independent evidence",
        "next_owner": None if complete else "control-verifier",
    }


class Phase2OperationalizationGate(unittest.TestCase):
    def _run_loop(self, engine: str, capability: str, workflow: str) -> tuple[dict, dict, dict, dict]:
        value = bundle(engine, capability, workflow)
        if engine == "research":
            value["decision"]["research_admission"] = "MACHINE_ONLY_ADMITTED"
        spawned = resolve_spawn(value)
        self.assertEqual((spawned["control_state"], spawned["status"]), ("ASSIGN", "SPAWN_READY"), spawned)
        self.assertEqual(spawned["compiled_assignment"]["compilation_status"], "COMPILED")
        self.assertEqual(spawned["assignment_admissibility"]["status"], "ADMISSIBLE")
        self.assertEqual(spawned["assignment"]["execution_contract"]["proof_status"], "PROVEN")

        executed = executor_result(spawned["assignment_ref"], engine)
        verified = verification_result(executed)
        directed = director_result(executed, verified)
        assert_required_shape(self, executed, "executor-result.schema.json")
        assert_required_shape(self, verified, "verification-result.schema.json")
        assert_required_shape(self, directed, "director-decision.schema.json")
        self.assertNotEqual(executed["artifact_type"], verified["artifact_type"])
        self.assertEqual(directed["executor_result_ref"], executed["artifact_id"])
        self.assertEqual(directed["verification_result_ref"], verified["artifact_id"])
        self.assertIn(directed["control_state"], BATONS)
        return value, spawned, executed, directed

    def test_A_to_O_representative_control_loops_and_negative_invariants(self) -> None:
        loops = [
            self._run_loop("production/software", "implement_software_change", "implementation"),
            self._run_loop("research", "execute_research_work", "machine-only-execution"),
            self._run_loop("verification", "verify_completion_claim", "exact-evidence-verification"),
        ]
        self.assertEqual([loop[3]["control_state"] for loop in loops], ["COMPLETE"] * 3)

        # An Executor success cannot satisfy the verifier contract or force COMPLETE.
        executed = loops[0][2]
        with self.assertRaises(AssertionError):
            assert_required_shape(self, executed, "verification-result.schema.json")
        not_proven = verification_result(executed, proven=False)
        ceiling_decision = director_result(executed, not_proven)
        self.assertEqual((not_proven["status"], ceiling_decision["control_state"]), ("NOT_PROVEN", "WAIT"))

        # An unrelated artifact does not invalidate the exact admission chain.
        unchanged = deepcopy(loops[0][0])
        unchanged["artifacts"].append({"artifact_type": "NOTE", "artifact_id": "UNRELATED-1"})
        unaffected = resolve_spawn(unchanged)
        self.assertEqual(unaffected["status"], "SPAWN_READY", unaffected)
        self.assertEqual(unaffected["assignment_admissibility"]["required_capabilities"],
                         loops[0][1]["assignment_admissibility"]["required_capabilities"])

        # Relevant capability drift invalidates route/admission instead of reusing authority.
        drifted = deepcopy(loops[0][0])
        profile = drifted["artifacts"][2]
        profile["available_capabilities"].remove("python_runtime")
        profile["unavailable_capabilities"].append("python_runtime")
        profile["capability_evidence"] = [item for item in profile["capability_evidence"]
                                           if item["capability"] != "python_runtime"]
        profile["evidence_artifacts"][0]["capabilities"].remove("python_runtime")
        rejected = resolve_spawn(drifted)
        self.assertIn(rejected["control_state"], {"WAIT", "ESCALATE"})
        self.assertNotEqual(rejected["status"], "SPAWN_READY")
        self.assertNotIn("assignment", rejected)

        # A later ASSIGN is only a request: it must traverse the proof chain again.
        second = deepcopy(loops[0][0])
        second["assignment_id"] = "ASSIGN-SECOND"
        second["admissibility_id"] = "ADM-SECOND"
        second["capability_profile_ref"] = "missing-profile"
        bypass = resolve_spawn(second)
        self.assertEqual((bypass["control_state"], bypass["reason"]),
                         ("ESCALATE", "REFERENCE_IDENTITY_MISMATCH"))
        self.assertNotIn("assignment", bypass)

        # Every returned production baton is explicit and belongs to the closed vocabulary.
        outcomes = [resolve_spawn({**bundle(), "decision": {**bundle()["decision"], "control_state": state}})
                    for state in ("WAIT", "ESCALATE", "COMPLETE")]
        outcomes.extend([loop[1] for loop in loops])
        outcomes.extend([rejected, bypass])
        self.assertTrue(all(item["control_state"] in BATONS for item in outcomes))

    def test_N6_N7_resolver_is_a_thin_non_scheduling_composition_boundary(self) -> None:
        source = (ROOT / "tools" / "resolver_spawn.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertTrue({"tools.assignment_compiler", "tools.executability"} <= imported_modules)
        self.assertFalse(any(isinstance(node, (ast.While, ast.AsyncFor, ast.AsyncFunctionDef)) for node in ast.walk(tree)))
        forbidden_authority = ("scheduler", "delegate", "worker_pool", "parallel_dispatch", "retry_until", "lease")
        self.assertFalse(any(term in source.lower() for term in forbidden_authority))


if __name__ == "__main__":
    unittest.main()
