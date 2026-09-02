from __future__ import annotations

from copy import deepcopy
import unittest

from tools.assignment_compiler import (
    AUTHORITY_CLASSES, CONTEXT_AUTHORITIES,
    COMPILED_CAPABILITY_MISMATCH, INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET,
    PLATFORM_FACT_REAUTHENTICATION, RESPONSIBILITY_MISMATCH,
    UNSUPPORTED_EXECUTION_ENVELOPE, compile_assignment, validate_compiled_assignment,
)
from tools.executability import evaluate_assignment_admissibility

SUPPORTED = {"local_execution", "local_observation", "remote_observation", "provided_context", "control_adjudication"}


def draft(authority_class="MOVING_PR"):
    return {
        "compiled_artifact_id":"COMPILED-1", "assignment_draft_ref":"DRAFT-1", "input_state_ref":"state-1",
        "provenance":["OWNER-1"], "related_artifacts":["DRAFT-1"], "authority_class":authority_class,
        "context_facts":[
            {"fact_id":"workspace", "fact_kind":"repository_checkout", "authority_source":"PLATFORM_PROVIDED", "value_or_ref":"provided:workspace", "mutable":True, "required_for":["execution"]},
            {"fact_id":"local_result", "fact_kind":"test_result", "authority_source":"EXECUTOR_RESOLVED", "value_or_ref":"runtime", "mutable":True, "required_for":["acceptance"]},
        ],
        "invariants":[],
        "mandatory_actions":[{"action_id":"test", "responsibility":"EXECUTOR", "operation":"RUN_TESTS", "obligation_class":"local_execution", "context_fact_ref":"local_result", "required_capabilities":["shell","python_runtime"], "evidence_path":"python -m unittest"}],
        "evidence_requirements":[], "acceptance_requirements":[{"requirement_id":"tests-pass"}], "stop_conditions":[],
    }


def codes(result): return {error["code"] for error in result["compilation_errors"]}


class AssignmentCompilerTest(unittest.TestCase):
    def test_enum_contract(self):
        self.assertEqual(AUTHORITY_CLASSES, ("FROZEN_CANDIDATE","MOVING_PR","MOVING_BRANCH","POST_MERGE_STATE","LIVE_REMOTE_STATE"))
        self.assertEqual(CONTEXT_AUTHORITIES, ("PLATFORM_PROVIDED","RESOLVER_BOUND","EXECUTOR_RESOLVED","REMOTE_LIVE"))

    def test_frozen_candidate_exact_sha_compiles(self):
        value=draft("FROZEN_CANDIDATE")
        value["invariants"]=[{"invariant_id":"candidate", "identity_kind":"CANDIDATE_HEAD", "classification":"immutable", "responsibility":"CONTROL", "value_or_ref":"sha:abc123", "independent_freeze_authority_ref":"OWNER-1"}]
        result=compile_assignment(value,SUPPORTED)
        self.assertEqual(result["status"],"COMPILED"); self.assertEqual(validate_compiled_assignment(result),[])

    def test_moving_targets_reject_implicit_frozen_head(self):
        for authority in ("MOVING_PR","MOVING_BRANCH"):
            value=draft(authority)
            value["invariants"]=[{"invariant_id":"old-head", "identity_kind":"CANDIDATE_HEAD", "classification":"immutable", "responsibility":"EXECUTOR", "value_or_ref":"sha:abc123"}]
            result=compile_assignment(value,SUPPORTED)
            self.assertEqual(result["status"],"REJECTED"); self.assertIn(INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET,codes(result)); self.assertEqual(result["authorized_required_capabilities"],[])

    def test_platform_checkout_remote_reauthentication_is_rejected(self):
        value=draft()
        value["mandatory_actions"].append({"action_id":"rediscover", "responsibility":"EXECUTOR", "operation":"REAUTHENTICATE_CONTEXT_FACT", "obligation_class":"remote_observation", "context_fact_ref":"workspace", "required_capabilities":["repository_remote_read","connector:github","outbound_network"], "evidence_path":"remote lookup"})
        result=compile_assignment(value,SUPPORTED)
        self.assertEqual(result["status"],"REJECTED"); self.assertIn(PLATFORM_FACT_REAUTHENTICATION,codes(result)); self.assertFalse(set(result["authorized_required_capabilities"]) & {"repository_remote_read","connector:github","outbound_network"})

    def test_local_moving_pr_and_post_merge_compile(self):
        for authority in ("MOVING_PR","POST_MERGE_STATE"):
            result=compile_assignment(draft(authority),SUPPORTED)
            self.assertEqual(result["status"],"COMPILED"); self.assertEqual(result["authorized_required_capabilities"],["python_runtime","shell"])

    def test_live_remote_requirement_compiles(self):
        value=draft("LIVE_REMOTE_STATE")
        value["context_facts"].append({"fact_id":"remote", "fact_kind":"repository_state", "authority_source":"REMOTE_LIVE", "value_or_ref":"remote:current", "mutable":True, "required_for":["objective"]})
        value["mandatory_actions"]=[{"action_id":"read-remote", "responsibility":"EXECUTOR", "operation":"READ_REMOTE_STATE", "obligation_class":"remote_observation", "context_fact_ref":"remote", "required_capabilities":["repository_remote_read"], "evidence_path":"remote state"}]
        result=compile_assignment(value,SUPPORTED)
        self.assertEqual(result["status"],"COMPILED"); self.assertEqual(result["authorized_required_capabilities"],["repository_remote_read"])

    def test_responsibility_partition_excludes_platform_and_control_capabilities(self):
        value=draft()
        value["mandatory_actions"].extend([
            {"action_id":"bind", "responsibility":"PLATFORM", "operation":"PROVIDE_CONTEXT", "obligation_class":"provided_context", "context_fact_ref":"workspace", "required_capabilities":["platform_binding"], "evidence_path":None},
            {"action_id":"adjudicate", "responsibility":"CONTROL", "operation":"ADJUDICATE", "obligation_class":"control_adjudication", "context_fact_ref":None, "required_capabilities":["owner_authority"], "evidence_path":None},
        ])
        result=compile_assignment(value,SUPPORTED)
        self.assertEqual(result["status"],"COMPILED"); self.assertEqual(result["authorized_required_capabilities"],["python_runtime","shell"])
        bad=deepcopy(value); bad["mandatory_actions"][1]["responsibility"]="EXECUTOR"
        rejected=compile_assignment(bad,SUPPORTED); self.assertIn(RESPONSIBILITY_MISMATCH,codes(rejected))

    def test_unsupported_portfolio_precedes_destination_admission(self):
        value=draft(); value["mandatory_actions"][0]["obligation_class"]="unsupported_hardware"
        result=compile_assignment(value,SUPPORTED)
        self.assertEqual(result["status"],"REJECTED"); self.assertEqual(result["supported_execution_envelope_status"],"UNSUPPORTED"); self.assertIn(UNSUPPORTED_EXECUTION_ENVELOPE,codes(result))
        compiled=compile_assignment(draft(),SUPPORTED)
        self.assertEqual(compiled["status"],"COMPILED")
        self.assertEqual(evaluate_assignment_admissibility(compiled["authorized_required_capabilities"],["shell"])["status"],"NOT_ADMISSIBLE")

    def test_declared_capability_mismatch_rejected(self):
        value=draft(); value["authorized_required_capabilities"]=["repository_remote_read"]
        result=compile_assignment(value,SUPPORTED)
        self.assertIn(COMPILED_CAPABILITY_MISMATCH,codes(result))

    def test_recompiled_semantics_have_new_identity(self):
        first=compile_assignment(draft(),SUPPORTED)
        changed=draft(); changed["compiled_artifact_id"]="COMPILED-2"; changed["mandatory_actions"][0]["required_capabilities"].append("repository_local_checkout")
        second=compile_assignment(changed,SUPPORTED)
        self.assertNotEqual(first["artifact_id"],second["artifact_id"]); self.assertNotEqual(first["authorized_required_capabilities"],second["authorized_required_capabilities"])


if __name__ == "__main__": unittest.main()
