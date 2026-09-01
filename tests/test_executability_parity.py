from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

from tests.test_executability import governed_chain, valid_chain
from tools.executability import (
    validate_admissibility_record,
    validate_assignment_artifact,
    validate_capability_evidence_artifact,
    validate_capability_profile,
    validate_execution_route,
)

ROOT = Path(__file__).resolve().parents[1]


def schema_accepts(value: object, schema: dict) -> bool:
    """Execute only the JSON-Schema keywords used by the committed parity fixtures."""
    def valid(instance: object, rule: dict) -> bool:
        if "anyOf" in rule and not any(valid(instance, option) for option in rule["anyOf"]): return False
        kind = rule.get("type")
        kinds = kind if isinstance(kind, list) else [kind] if kind else []
        if kinds:
            checks = {"object": lambda x:isinstance(x,dict), "array":lambda x:isinstance(x,list), "string":lambda x:isinstance(x,str), "null":lambda x:x is None, "boolean":lambda x:isinstance(x,bool)}
            if not any(name in checks and checks[name](instance) for name in kinds): return False
        if "const" in rule and instance != rule["const"]: return False
        if "enum" in rule and instance not in rule["enum"]: return False
        if isinstance(instance,str):
            if len(instance) < rule.get("minLength",0): return False
            if "pattern" in rule and re.fullmatch(rule["pattern"],instance) is None: return False
        if isinstance(instance,list):
            if len(instance) < rule.get("minItems",0) or len(instance) > rule.get("maxItems",10**9): return False
            if rule.get("uniqueItems") and len({json.dumps(x,sort_keys=True) for x in instance}) != len(instance): return False
            if "items" in rule and not all(valid(x,rule["items"]) for x in instance): return False
            for condition in rule.get("allOf",[]):
                matches=sum(valid(x,condition["contains"]) for x in instance)
                if matches < condition.get("minContains",1) or matches > condition.get("maxContains",10**9): return False
        if isinstance(instance,dict):
            if any(name not in instance for name in rule.get("required",[])): return False
            props=rule.get("properties",{})
            if rule.get("additionalProperties") is False and any(name not in props for name in instance): return False
            if any(name in instance and not valid(instance[name],child) for name,child in props.items()): return False
            for condition in rule.get("allOf",[]):
                if "if" in condition and valid(instance,condition["if"]) and not valid(instance,condition.get("then",{})): return False
        return True
    return valid(value,schema)


class ExecutabilitySchemaReferenceParityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile_schema=json.loads((ROOT/'schemas/capability-profile.schema.json').read_text())
        cls.route_schema=json.loads((ROOT/'schemas/execution-route.schema.json').read_text())
        cls.record_schema=json.loads((ROOT/'schemas/assignment-admissibility.schema.json').read_text())
        cls.assignment_schema=json.loads((ROOT/'schemas/assignment.schema.json').read_text())
        cls.evidence_schema=cls.profile_schema['properties']['evidence_artifacts']['items']

    def test_capability_evidence_fixture_matrix_parity(self) -> None:
        _,_,profile=deepcopy(valid_chain()); base=profile['evidence_artifacts'][0]
        mutations=[
            lambda x:x.update(capabilities=[]), lambda x:x.update(capabilities=['shell','shell']),
            lambda x:x.update(capabilities=['']), lambda x:x.update(assignment_id=7),
            lambda x:x.update(input_state_ref={}), lambda x:x.pop('provenance'),
            lambda x:x.update(provenance=[]), lambda x:x.pop('observation_method'),
            lambda x:x.pop('created_from'), lambda x:x.update(observed_at='not-a-timestamp'),
        ]
        self.assertTrue(schema_accepts(base,self.evidence_schema)); self.assertEqual(validate_capability_evidence_artifact(base),[])
        for mutate in mutations:
            artifact=deepcopy(base); mutate(artifact)
            with self.subTest(artifact=artifact):
                self.assertFalse(schema_accepts(artifact,self.evidence_schema))
                self.assertTrue(validate_capability_evidence_artifact(artifact))

    def test_primary_artifact_happy_path_schema_reference_parity(self) -> None:
        assignment,record,profile=deepcopy(valid_chain()); resolver,route=governed_chain(assignment,record,profile)
        pairs=[(profile,self.profile_schema,validate_capability_profile(profile,resolver)),(record,self.record_schema,validate_admissibility_record(record)),(route,self.route_schema,validate_execution_route(route,{'CAP-1':profile},resolver)),(assignment,self.assignment_schema,validate_assignment_artifact(assignment))]
        for artifact,schema,errors in pairs:
            with self.subTest(type=artifact['artifact_type']): self.assertTrue(schema_accepts(artifact,schema)); self.assertEqual(errors,[])

    def test_route_structural_fixture_matrix_parity(self) -> None:
        assignment,record,profile=deepcopy(valid_chain()); resolver,base=governed_chain(assignment,record,profile); profiles={'CAP-1':profile}
        cases=[]
        missing=deepcopy(base); missing['segments']=missing['segments'][1:]; cases.append(missing)
        duplicate_role=deepcopy(base); duplicate_role['segments'][0]['route_role']='EXECUTION_VERIFICATION'; cases.append(duplicate_role)
        duplicate_id=deepcopy(base); duplicate_id['segments'][1]['segment_id']='delivery'; cases.append(duplicate_id)
        malformed=deepcopy(base); malformed['handoffs'][0].pop('same_surface'); cases.append(malformed)
        for route in cases:
            with self.subTest(route=route):
                reference_rejects=bool(validate_execution_route(route,profiles,resolver))
                schema_rejects=not schema_accepts(route,self.route_schema)
                if route is duplicate_id:
                    self.assertTrue(reference_rejects)  # JSON Schema cannot express key-projected uniqueness.
                else:
                    self.assertTrue(schema_rejects); self.assertTrue(reference_rejects)
        wrong_order=deepcopy(base); wrong_order['handoffs'][0]['to_segment']='durable'
        self.assertTrue(schema_accepts(wrong_order,self.route_schema))
        self.assertTrue(validate_execution_route(wrong_order,profiles,resolver))  # Deliberately semantic/reference-only.

    def test_assignment_route_binding_is_deliberately_semantic(self) -> None:
        assignment,record,profile=deepcopy(valid_chain())
        missing=deepcopy(assignment); missing['execution_contract'].pop('route_ref')
        self.assertFalse(schema_accepts(missing,self.assignment_schema)); self.assertTrue(validate_assignment_artifact(missing))
        # Cross-artifact identity and endpoint equality cannot be expressed by these standalone schemas.
        self.assertTrue(schema_accepts(assignment,self.assignment_schema))


if __name__ == '__main__': unittest.main()
