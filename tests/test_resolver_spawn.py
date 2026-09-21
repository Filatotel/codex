from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.test_assignment_compiler import action, claim, draft, envelope
from tests.test_executability import governed_chain, valid_chain
from tests.test_research_machine_only import base_wp
import tools.resolver_spawn as resolver_spawn
from tools.research_policy import admit_work_package
from tools.resource_ledger import ResourceLedger
from tools.resolver_spawn import resolve_spawn

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_POLICY_SURFACE = "tools.research_policy.admit_work_package"
RG_NOW = datetime(2026, 9, 20, 4, 0, tzinfo=timezone.utc)
RG_OWNER_AUTHORITY_REF = "OWNER-RG04-AUTH-1"


def _append_artifact(value: dict, artifact: dict) -> str:
    value["artifacts"].append(artifact)
    return artifact["artifact_id"]


def _attach_default_canon_prerequisites(value: dict, workflow: str) -> None:
    state_ref = value["input_state_observation_ref"]
    if workflow == "establish_canon_foundation":
        owner_ref = _append_artifact(value,{"artifact_id":"OWNER-FOUNDATION-INPUT-1","artifact_type":"OWNER_DECISION_RECORD","provenance":["OWNER/K0"]})
        value["workflow_prerequisite_bindings"]={"owner_or_authorized_foundation_input":owner_ref,"exact_state_identity":state_ref}
    elif workflow == "reconcile_research_into_canon":
        canon_ref=_append_artifact(value,{"artifact_id":"CANON-CURRENT-1","artifact_type":"CANON_STATE","provenance":["OWNER/K0"]})
        research_ref=_append_artifact(value,{"artifact_id":"FINDING-1","artifact_type":"RESEARCH_FINDING","provenance":["RESEARCH-RELEASE-1"]})
        value["workflow_prerequisite_bindings"]={"exact_current_canon_ref":canon_ref,"exact_research_release_or_finding_refs":[research_ref]}
    elif workflow == "manage_production_canon_change":
        canon_ref=_append_artifact(value,{"artifact_id":"CANON-CURRENT-1","artifact_type":"CANON_STATE","provenance":["OWNER/K0"]})
        signal_ref=_append_artifact(value,{"artifact_id":"PRODUCTION-CHANGE-1","artifact_type":"PRODUCTION_CHANGE","provenance":["PRODUCTION-1"]})
        value["workflow_prerequisite_bindings"]={"exact_current_canon_ref":canon_ref,"exact_production_change_signal":signal_ref}
    elif workflow == "validate_canon":
        candidate_ref=_append_artifact(value,{"artifact_id":"CANON-CANDIDATE-1","artifact_type":"CANON_STATE","provenance":["OWNER/K0"]})
        value["workflow_prerequisite_bindings"]={"exact_canon_candidate_ref":candidate_ref}


def bundle(engine="production/software",capability="implement_software_change",workflow="implementation"):
    assignment,_,profile=deepcopy(valid_chain()); _,route=governed_chain(assignment,{},profile)
    compilation=draft("MOVING_BRANCH"); compilation["mandatory_actions"]=[action(capabilities=["python_runtime","shell"])]
    compilation["authorized_required_capabilities"]=["python_runtime","shell"]; env=envelope(); evidence=profile["evidence_artifacts"][0]
    state={"artifact_type":"STATE_OBSERVATION","artifact_id":"STATE-OBS-1","produced_by_role":"control-director",
           "input_state_ref":compilation["input_state_ref"],"status":"CURRENT","provenance":["OWNER/K0"],"related_artifacts":[],
           "state_identity":"git:input-state","authority_scope":"assignment-input"}
    value={"decision":{"control_state":"ASSIGN","engine_id":engine,"engine_status":"available","semantic_capability":capability,"workflow_id":workflow,"execution_mode":"local"},
           "assignment_compilation_draft":compilation,"assignment_draft_semantics":{"objective":"Perform the already-authorized bounded work.","authority":["OWNER/K0"],"scope":{"allowed":["bounded work"],"forbidden":["scope expansion"]},"acceptance":["produce required evidence"],"required_outputs":["result"],"stop_conditions":["runtime drift"],"result_to":"agent-1"},
           "selected_prerequisite_actions":[],"execution_envelope_ref":env["artifact_id"],"capability_profile_ref":profile["artifact_id"],
           "route_ref":route["artifact_id"],"admissibility_id":"ADM-RESOLVED","assignment_id":"ASSIGN-RESOLVED",
           "input_state_observation_ref":state["artifact_id"],"artifacts":[env,evidence,profile,route,state]}
    if engine=="canon": _attach_default_canon_prerequisites(value,workflow)
    return value


def attach_research_admission(value, work_package=None, admission_id="RESEARCH-ADM-1"):
    work=deepcopy(work_package or base_wp()); admission_result=admit_work_package(work)
    admission={"artifact_id":admission_id,**admission_result,"WORK_PACKAGE_ID":work["WORK_PACKAGE_ID"],"QUESTION_ID":work["QUESTION_ID"],
               "POLICY_SURFACE":RESEARCH_POLICY_SURFACE,"PROVENANCE":[RESEARCH_POLICY_SURFACE,work["WORK_PACKAGE_ID"],work["QUESTION_ID"]],"WORK_PACKAGE":work}
    value["decision"].update({"research_admission_ref":admission_id,"research_work_package_id":work["WORK_PACKAGE_ID"],"research_question_id":work["QUESTION_ID"]})
    value["artifacts"].append(admission); return admission


def resource_grant(value:dict,*,grant_id="RG-ASSIGN-1",mode="RESERVABLE_LIMIT",ordinary=Decimal("5"),final=Decimal("2"),route_ref=None,candidate_ref=None):
    route_ref=value["route_ref"] if route_ref is None else route_ref
    state=next(x for x in value["artifacts"] if x.get("artifact_id")==value["input_state_observation_ref"])
    if candidate_ref is None: candidate_ref=state["state_identity"]
    capacities=(None,None) if mode=="OBSERVATION_ONLY" else (ordinary,final)
    return {"artifact_type":"RESOURCE_GRANT","artifact_id":grant_id,"produced_by_role":"control-director","assignment_id":value["assignment_id"],
            "input_state_ref":value["assignment_compilation_draft"]["input_state_ref"],"status":"AUTHORIZED","provenance":["owner:resource-authority"],
            "related_artifacts":[],"issued_by":"control-director","authority_source":{"authority_type":"OWNER_APPROVED_RESOURCE_AUTHORITY","authority_ref":RG_OWNER_AUTHORITY_REF},
            "parent_grant_ref":None,"scope":{"scope_ref":f"assignment:{value['assignment_id']}","candidate_ref":candidate_ref,"route_ref":route_ref,"resource_classes":["MODEL_INFERENCE"]},
            "limits":[{"resource_class":"MODEL_INFERENCE","dimension":"TOKENS","limit_mode":mode,"ordinary_limit":capacities[0],"finalization_reserve":capacities[1]}],
            "attempt_limit":3,"valid_until":"2030-01-01T00:00:00Z","finalization_policy":{"protected":True,"allowed_purposes":["FINAL_ACCOUNTING"]}}


def resource_authority_decision(value:dict, grant:dict)->dict:
    return {"artifact_type":"OWNER_DECISION_RECORD","artifact_id":RG_OWNER_AUTHORITY_REF,"produced_by_role":"owner-interface",
            "assignment_id":grant["assignment_id"],"input_state_ref":grant["input_state_ref"],"status":"RECORDED",
            "provenance":["OWNER/K0","decision:resource-authority"],"related_artifacts":[grant["artifact_id"]],"question_ref":"Q-RG04-RESOURCE-AUTHORITY",
            "options_presented":["AUTHORIZE_RESOURCE_AUTHORITY","DO_NOT_AUTHORIZE_RESOURCE_AUTHORITY","DEFER"],"selected_option":"AUTHORIZE_RESOURCE_AUTHORITY",
            "owner_constraints":[],"consequences_acknowledged":["finite-authority"],"authority_role":"OWNER_K0","decision_kind":"OWNER_APPROVED_RESOURCE_AUTHORITY",
            "authorized_resource_grant_ref":grant["artifact_id"],"authorized_scope":grant["scope"]["scope_ref"],"authorized_candidate_ref":grant["scope"]["candidate_ref"],
            "authorized_route_ref":grant["scope"]["route_ref"],"authorized_resource_classes":deepcopy(grant["scope"]["resource_classes"]),
            "authorized_resource_limits":deepcopy(grant["limits"]),"authorized_attempt_limit":grant["attempt_limit"],"authorized_valid_until":grant["valid_until"],
            "authorized_finalization_policy":deepcopy(grant["finalization_policy"]),"non_transitive":True}


def resource_estimate(value:dict,compiled_ref:str,*,estimate_id="RE-ASSIGN-1",upper=Decimal("2"),unknown=False):
    x=({"resource_class":"MODEL_INFERENCE","dimension":"TOKENS","estimate_state":"UNKNOWN","point_estimate":None,"quantiles":[],"upper_bound":None,"confidence":"UNKNOWN","historical_sample_count":None,"unknown_resource_state":"ESTIMATE_UNKNOWN"} if unknown else
       {"resource_class":"MODEL_INFERENCE","dimension":"TOKENS","estimate_state":"ESTIMATED","point_estimate":upper,"quantiles":[],"upper_bound":upper,"confidence":"HIGH","historical_sample_count":9,"unknown_resource_state":"KNOWN"})
    return {"artifact_type":"RESOURCE_ESTIMATE","artifact_id":estimate_id,"produced_by_role":"resource-estimator","assignment_id":value["assignment_id"],
            "input_state_ref":value["assignment_compilation_draft"]["input_state_ref"],"status":"UNKNOWN" if unknown else "ESTIMATED","provenance":["history:1"],"related_artifacts":[],
            "subject_ref":compiled_ref,"route_ref":value["route_ref"],"estimator_revision_ref":"rg02:merged","basis_refs":[] if unknown else ["history:1"],"estimates":[x]}


def attach_resource_governance(value:dict,ledger:ResourceLedger,*,mode="RESERVABLE_LIMIT",ordinary=Decimal("5"),upper=Decimal("2"),unknown=False,side_effect_refs=()):
    legacy=resolve_spawn(deepcopy(value));
    if legacy.get("status")!="SPAWN_READY": raise AssertionError(f"fixture must be executable before resource governance: {legacy}")
    compiled_ref=legacy["compiled_assignment_ref"]; grant=resource_grant(value,mode=mode,ordinary=ordinary); ledger.register_grant(grant)
    est=resource_estimate(value,compiled_ref,upper=upper,unknown=unknown)
    value["artifacts"].extend([resource_authority_decision(value,grant),est,grant])
    value["resource_governance"]={"resource_admission_id":"RA-ASSIGN-1","resource_estimate_ref":est["artifact_id"],"resource_grant_ref":grant["artifact_id"],"availability_evidence_refs":[],"unclassified_metered_side_effect_refs":list(side_effect_refs)}
    return est,grant


class ResolverSpawnTest(unittest.TestCase):

    def assert_spawn_ready(self, value):
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        self.assertEqual(result["assignment"]["objective"], value["assignment_draft_semantics"]["objective"])
        return result

    def test_representative_software_research_and_verification(self):
        cases = [
            bundle(),
            bundle("research", "execute_research_work", "machine-only-execution"),
            bundle("verification", "verify_completion_claim", "exact-evidence-verification"),
        ]
        attach_research_admission(cases[1])
        cases[2]["assignment_compilation_draft"]["evidence_requirements"] = [
            action("verification-evidence", capabilities=["python_runtime"], obligation_class="local_evidence")]
        for value in cases:
            with self.subTest(engine=value["decision"]["engine_id"]):
                self.assert_spawn_ready(value)

    def test_research_requires_structured_machine_only_admission(self):
        value = bundle("research", "execute_research_work", "machine-only-execution")
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "RESEARCH_ADMISSION_REQUIRED"))
        self.assertNotIn("assignment", result)

    def test_compilation_rejected_escalates_without_assignment(self):
        value = bundle(); value["assignment_compilation_draft"]["mandatory_actions"][0]["claim_ref"] = "missing"
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "COMPILE_REJECTED"))
        self.assertNotIn("assignment", result)

    def test_missing_capability_waits_with_subset_details(self):
        value = bundle(); value["assignment_compilation_draft"]["mandatory_actions"][0]["required_capabilities"].append("database_access")
        value["assignment_compilation_draft"]["authorized_required_capabilities"].append("database_access")
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "ASSIGNMENT_NOT_ADMISSIBLE"))
        self.assertEqual(result["missing_capabilities"], ["database_access"])
        self.assertNotIn("assignment", result)

    def test_control_obligation_capability_does_not_expand_executor_destination(self):
        value = bundle()
        value["assignment_compilation_draft"]["authorized_claims"].append(
            claim("control-outcome", responsibility="CONTROL")
        )
        value["assignment_compilation_draft"]["mandatory_actions"].append(
            action("owner-check", claim_ref="control-outcome", responsibility="CONTROL", capabilities=["owner_authority"])
        )
        result = self.assert_spawn_ready(value)
        self.assertNotIn("owner_authority", result["assignment_admissibility"]["required_capabilities"])
        self.assertFalse(any(item.get("action_id") == "owner-check" for item in result["assignment_admissibility"]["mandatory_actions"]))

    def test_stale_profile_waits_but_malformed_profile_escalates(self):
        stale = bundle(); profile = stale["artifacts"][2]
        profile["freshness_boundary"]["observed_at"] = "2024-01-01T00:00:00Z"
        profile["freshness_boundary"]["valid_until"] = "2025-01-01T00:00:00Z"
        profile["evidence_artifacts"][0]["observed_at"] = "2024-01-01T00:00:00Z"
        profile["evidence_artifacts"][0]["valid_until"] = "2025-01-01T00:00:00Z"
        stale["artifacts"][1]["observed_at"] = "2024-01-01T00:00:00Z"
        stale["artifacts"][1]["valid_until"] = "2025-01-01T00:00:00Z"
        result = resolve_spawn(stale)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "CAPABILITY_PROFILE_STALE"))
        malformed = bundle(); del malformed["artifacts"][2]["destination_id"]
        result = resolve_spawn(malformed)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "MALFORMED_CAPABILITY_PROFILE"))

    def test_route_profile_destination_mismatch_escalates(self):
        value = bundle(); value["artifacts"][3]["segments"][1]["destination_id"] = "other"
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "EXECUTION_ROUTE_INVALID"))

    def test_prerequisite_action_is_accounted_and_bare_capability_is_rejected(self):
        value = bundle(); value["selected_prerequisite_actions"] = [{"action_id": "render", "required_capabilities": ["shell"], "evidence_path": "render-check"}]
        result = self.assert_spawn_ready(value)
        self.assertIn("render-check", result["assignment_admissibility"]["mandatory_evidence_paths"])
        value = bundle(); value["additional_required_capabilities"] = ["outbound_network"]
        result = resolve_spawn(value)
        self.assertEqual(result["reason"], "UNACCOUNTED_CAPABILITY_EXPANSION")

    def test_non_materialized_engine_and_terminal_batons(self):
        value = bundle("canon", "reconcile_canon", "none"); value["decision"]["engine_status"] = "not_materialized"
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "ENGINE_NOT_MATERIALIZED"))
        for state in ("WAIT", "ESCALATE", "COMPLETE"):
            value = bundle(); value["decision"]["control_state"] = state
            result = resolve_spawn(value)
            self.assertEqual((result["control_state"], result["status"]), (state, state))
            self.assertNotIn("assignment", result)

    def test_missing_semantics_fail_closed(self):
        value = bundle(); del value["assignment_draft_semantics"]["objective"]
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "MISSING_ASSIGNMENT_SEMANTICS"), result)

    def test_duplicate_action_identity_fails_closed(self):
        value = bundle(); value["selected_prerequisite_actions"] = [{"action_id": "test", "required_capabilities": ["shell"], "evidence_path": None}]
        result = resolve_spawn(value)
        self.assertEqual(result["reason"], "CONTRADICTORY_CONTROL_ARTIFACTS")

    def test_malformed_profile_or_route_ref_escalates_without_exception(self):
        for field, bad_value in (("capability_profile_ref", []), ("route_ref", {})):
            with self.subTest(field=field):
                value = bundle(); value[field] = bad_value
                result = resolve_spawn(value)
                self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "MALFORMED_CONTROL_ARTIFACT"))
                self.assertNotIn("assignment", result)

    def test_duplicate_artifact_identity_fails_closed(self):
        value = bundle(); value["artifacts"].append(deepcopy(value["artifacts"][2]))
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "CONTRADICTORY_CONTROL_ARTIFACTS"))
        self.assertTrue(any("duplicate artifact_id" in error for error in result["errors"]))

    def test_compiled_capability_drop_is_caught_by_full_proof(self):
        value = bundle()
        real_compile = resolver_spawn.compile_assignment

        def compile_with_extra_capability(*args, **kwargs):
            compiled = real_compile(*args, **kwargs)
            compiled["authorized_required_capabilities"] = sorted(set(compiled["authorized_required_capabilities"]) | {"database_access"})
            return compiled

        with patch.object(resolver_spawn, "compile_assignment", side_effect=compile_with_extra_capability), \
             patch.object(resolver_spawn, "validate_compiled_assignment", return_value=[]):
            result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "FINAL_ASSIGNMENT_PROOF_FAILED"))
        self.assertTrue(any("drops compiled assignment capabilities" in error for error in result["errors"]))

    def test_final_assignment_ref_mismatch_is_caught_by_full_proof(self):
        value = bundle()
        real_proof = resolver_spawn.validate_assignment_execution_contract

        def validate_with_bad_ref(assignment, *args, **kwargs):
            mutated = deepcopy(assignment)
            mutated["execution_contract"]["admissibility_ref"] = "ADM-WRONG"
            return real_proof(mutated, *args, **kwargs)

        with patch.object(resolver_spawn, "validate_assignment_execution_contract", side_effect=validate_with_bad_ref):
            result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "FINAL_ASSIGNMENT_PROOF_FAILED"))
        self.assertTrue(any("admissibility_ref mismatch" in error for error in result["errors"]))

    def test_malformed_final_capability_entry_escalates_without_exception(self):
        value = bundle()
        value["assignment_compilation_draft"]["mandatory_actions"][0]["required_capabilities"] = [5]
        value["assignment_compilation_draft"]["authorized_required_capabilities"] = []
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "MALFORMED_MANDATORY_ACTION"))
        self.assertNotIn("assignment", result)

    def test_cli_reads_only_local_json_and_emits_json(self):
        value = bundle()
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as handle:
            json.dump(value, handle); handle.flush()
            completed = subprocess.run([sys.executable, str(ROOT / "tools/resolver_spawn.py"), handle.name], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(completed.stdout)["status"], "SPAWN_READY")

    def test_legacy_and_governed_happy_path(self):
        legacy=resolve_spawn(bundle()); self.assertEqual(legacy["status"],"SPAWN_READY"); self.assertNotIn("resource_admission",legacy)
        with tempfile.TemporaryDirectory() as td:
            ledger=ResourceLedger(Path(td)/"ledger.sqlite3"); ledger.initialize(); value=bundle(); est,grant=attach_resource_governance(value,ledger); result=resolve_spawn(value,resource_state_reader=ledger,now=RG_NOW)
        self.assertEqual(result["status"],"SPAWN_READY"); self.assertEqual(result["assignment_admissibility"]["status"],"ADMISSIBLE"); self.assertEqual(result["resource_admission"]["status"],"ADMISSIBLE")
        contract=result["assignment"]["execution_contract"]; self.assertEqual(contract["resource_admission_ref"],"RA-ASSIGN-1"); self.assertEqual(contract["resource_estimate_ref"],est["artifact_id"]); self.assertEqual(contract["resource_grant_ref"],grant["artifact_id"])
        self.assertEqual(result["assignment"]["provenance"],sorted(["ADM-RESOLVED","RA-ASSIGN-1"]))

    def test_authority_insufficiency_missing_and_malformed_estimate_block(self):
        with tempfile.TemporaryDirectory() as td:
            ledger=ResourceLedger(Path(td)/"ledger.sqlite3"); ledger.initialize(); value=bundle(); attach_resource_governance(value,ledger); value["artifacts"]=[a for a in value["artifacts"] if a.get("artifact_id")!=RG_OWNER_AUTHORITY_REF]
            r=resolve_spawn(value,resource_state_reader=ledger,now=RG_NOW); self.assertEqual(r["reason"],"RESOURCE_NOT_ADMISSIBLE"); self.assertEqual(r["resource_admission"]["blocking_reasons"],["AUTHORITY_SOURCE_UNRESOLVED"]); self.assertEqual(r["resource_admission"]["unknown_resource_state"],"KNOWN"); self.assertNotIn("assignment",r)
        with tempfile.TemporaryDirectory() as td:
            ledger=ResourceLedger(Path(td)/"ledger.sqlite3"); ledger.initialize(); value=bundle(); attach_resource_governance(value,ledger,ordinary=Decimal("1"),upper=Decimal("2")); r=resolve_spawn(value,resource_state_reader=ledger,now=RG_NOW); self.assertEqual((r["status"],r["reason"]),("WAIT","RESOURCE_NOT_ADMISSIBLE")); self.assertNotIn("assignment",r)
        for missing in ("estimate","grant"):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as td:
                ledger=ResourceLedger(Path(td)/"ledger.sqlite3"); ledger.initialize(); value=bundle(); e,g=attach_resource_governance(value,ledger); ref=e["artifact_id"] if missing=="estimate" else g["artifact_id"]; value["artifacts"]=[a for a in value["artifacts"] if a.get("artifact_id")!=ref]; r=resolve_spawn(value,resource_state_reader=ledger,now=RG_NOW); self.assertNotEqual(r["status"],"SPAWN_READY"); self.assertNotIn("assignment",r)
        with tempfile.TemporaryDirectory() as td:
            ledger=ResourceLedger(Path(td)/"ledger.sqlite3"); ledger.initialize(); value=bundle(); e,_=attach_resource_governance(value,ledger); e["estimates"][0].pop("point_estimate"); r=resolve_spawn(value,resource_state_reader=ledger,now=RG_NOW); self.assertIn("OTHER_CONTRACT_BLOCK",r["resource_admission"]["blocking_reasons"]); self.assertNotIn("assignment",r)

    def test_unknown_observation_side_effect_and_reader_validation(self):
        with tempfile.TemporaryDirectory() as td:
            ledger=ResourceLedger(Path(td)/"ledger.sqlite3"); ledger.initialize(); value=bundle(); attach_resource_governance(value,ledger,unknown=True); r=resolve_spawn(value,resource_state_reader=ledger,now=RG_NOW); self.assertIn("UNKNOWN_REQUIRED_RESOURCE",r["resource_admission"]["blocking_reasons"])
        with tempfile.TemporaryDirectory() as td:
            ledger=ResourceLedger(Path(td)/"ledger.sqlite3"); ledger.initialize(); value=bundle(); attach_resource_governance(value,ledger,mode="OBSERVATION_ONLY",unknown=True); self.assertEqual(resolve_spawn(value,resource_state_reader=ledger,now=RG_NOW)["status"],"SPAWN_READY")
        with tempfile.TemporaryDirectory() as td:
            ledger=ResourceLedger(Path(td)/"ledger.sqlite3"); ledger.initialize(); value=bundle(); attach_resource_governance(value,ledger,side_effect_refs=["surface:x"]); r=resolve_spawn(value,resource_state_reader=ledger,now=RG_NOW); self.assertIn("UNCLASSIFIED_METERED_SIDE_EFFECT",r["resource_admission"]["blocking_reasons"])
        with tempfile.TemporaryDirectory() as td:
            ledger=ResourceLedger(Path(td)/"ledger.sqlite3"); ledger.initialize(); value=bundle(); attach_resource_governance(value,ledger); self.assertEqual(resolve_spawn(value,now=RG_NOW)["reason"],"RESOURCE_ADMISSION_INVALID"); value["resource_governance"]["required"]=False; self.assertEqual(resolve_spawn(value,resource_state_reader=ledger,now=RG_NOW)["reason"],"RESOURCE_ADMISSION_INVALID")

    def test_assignment_and_research_axes_precede_resource_admission(self):
        value=bundle(); value["resource_governance"]={"malformed":True}; value["assignment_compilation_draft"]["mandatory_actions"][0]["required_capabilities"].append("database_access"); value["assignment_compilation_draft"]["authorized_required_capabilities"].append("database_access"); r=resolve_spawn(value); self.assertEqual(r["reason"],"ASSIGNMENT_NOT_ADMISSIBLE"); self.assertNotIn("resource_admission",r)
        value=bundle("research","execute_research_work","machine-only-execution"); value["resource_governance"]={"malformed":True}; self.assertEqual(resolve_spawn(value)["reason"],"RESEARCH_ADMISSION_REQUIRED")
        with tempfile.TemporaryDirectory() as td:
            ledger=ResourceLedger(Path(td)/"ledger.sqlite3"); ledger.initialize(); value=bundle("research","execute_research_work","machine-only-execution"); attach_research_admission(value); attach_resource_governance(value,ledger); r=resolve_spawn(value,resource_state_reader=ledger,now=RG_NOW); self.assertEqual(r["status"],"SPAWN_READY"); self.assertEqual(r["resource_admission"]["status"],"ADMISSIBLE")

    def test_governed_spawn_ready_requires_admissible_resource_admission(self):
        for ordinary,expected in ((Decimal("5"),"SPAWN_READY"),(Decimal("1"),"WAIT")):
            with self.subTest(ordinary=ordinary), tempfile.TemporaryDirectory() as td:
                ledger=ResourceLedger(Path(td)/"ledger.sqlite3"); ledger.initialize(); value=bundle(); attach_resource_governance(value,ledger,ordinary=ordinary,upper=Decimal("2")); r=resolve_spawn(value,resource_state_reader=ledger,now=RG_NOW); self.assertEqual(r["status"],expected); self.assertTrue(r["status"]!="SPAWN_READY" or r["resource_admission"]["status"]=="ADMISSIBLE")

    def test_cli_exact_decimal_and_missing_ledger_no_create(self):
        with tempfile.TemporaryDirectory() as td:
            ledger_path=Path(td)/"ledger.sqlite3"; ledger=ResourceLedger(ledger_path); ledger.initialize(); value=bundle(); available=Decimal("1.0000000000000000000000000000"); required=Decimal("1.0000000000000000000000000001"); attach_resource_governance(value,ledger,ordinary=available,upper=required); path=Path(td)/"bundle.json"; path.write_text(resolver_spawn._json_exact(value)+"\n",encoding="utf-8")
            p=subprocess.run([sys.executable,str(ROOT/"tools/resolver_spawn.py"),str(path),"--resource-ledger",str(ledger_path)],check=True,text=True,capture_output=True); r=json.loads(p.stdout,parse_float=Decimal); ev=r["resource_admission"]["evaluations"][0]; self.assertEqual((ev["estimated_requirement"],ev["available_amount"]),(required,available))
            missing=Path(td)/"missing.sqlite3"; p=subprocess.run([sys.executable,str(ROOT/"tools/resolver_spawn.py"),str(path),"--resource-ledger",str(missing)],check=True,text=True,capture_output=True); r=json.loads(p.stdout); self.assertFalse(missing.exists()); self.assertEqual(r["reason"],"RESOURCE_ADMISSION_INVALID")


if __name__=="__main__": unittest.main()
