from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from pathlib import Path
import tempfile
import unittest

from tools.resource_admission import evaluate_resource_admission
from tools.resource_ledger import ResourceLedger

NOW = datetime(2026, 9, 20, 4, 0, tzinfo=timezone.utc)
ODR = "ODR-RG04"


def root(
    gid="G-LEAF", *, ordinary=5, final=0, mode="RESERVABLE_LIMIT",
    authority_type="OWNER_APPROVED_RESOURCE_AUTHORITY", authority_ref=ODR,
):
    capacities = (None, None) if mode == "OBSERVATION_ONLY" else (ordinary, final)
    return {
        "artifact_type": "RESOURCE_GRANT", "artifact_id": gid, "produced_by_role": "control-director",
        "assignment_id": "A-1", "input_state_ref": "STATE-1", "status": "AUTHORIZED",
        "provenance": ["owner:resource-authority"], "related_artifacts": [], "issued_by": "control-director",
        "authority_source": {"authority_type": authority_type, "authority_ref": authority_ref},
        "parent_grant_ref": None,
        "scope": {"scope_ref": "assignment:A-1", "candidate_ref": "candidate:1", "route_ref": "ROUTE-1",
                  "resource_classes": ["MODEL_INFERENCE"]},
        "limits": [{"resource_class": "MODEL_INFERENCE", "dimension": "TOKENS", "limit_mode": mode,
                    "ordinary_limit": capacities[0], "finalization_reserve": capacities[1]}],
        "attempt_limit": 3, "valid_until": "2030-01-01T00:00:00Z",
        "finalization_policy": {"protected": True, "allowed_purposes": ["FINAL_ACCOUNTING"]},
    }


def rich_root(gid="G-LEAF"):
    g = root(gid)
    g["scope"]["resource_classes"] = ["MODEL_INFERENCE", "REMOTE_CI"]
    g["limits"].append({"resource_class": "MODEL_INFERENCE", "dimension": "MODEL_CALLS",
                        "limit_mode": "HARD_LIMIT", "ordinary_limit": 7, "finalization_reserve": 1})
    g["finalization_policy"]["allowed_purposes"] = ["FINAL_ACCOUNTING", "CONTROL_HANDOFF"]
    return g


def child(parent, gid="G-LEAF", *, ordinary=5, final=0):
    g = deepcopy(parent)
    g["artifact_id"] = gid
    g["authority_source"] = {"authority_type": "PARENT_RESOURCE_GRANT", "authority_ref": parent["artifact_id"]}
    g["parent_grant_ref"] = parent["artifact_id"]
    g["provenance"] = [parent["artifact_id"]]
    g["limits"] = [{"resource_class": "MODEL_INFERENCE", "dimension": "TOKENS", "limit_mode": "RESERVABLE_LIMIT",
                    "ordinary_limit": ordinary, "finalization_reserve": final}]
    g["scope"]["resource_classes"] = ["MODEL_INFERENCE"]
    return g


def decision(g=None, **kw):
    g = deepcopy(g or root())
    value = {
        "artifact_type": "OWNER_DECISION_RECORD", "artifact_id": ODR, "produced_by_role": "owner-interface",
        "assignment_id": g["assignment_id"], "input_state_ref": g["input_state_ref"], "status": "RECORDED",
        "provenance": ["OWNER/K0", "decision:resource-authority"], "related_artifacts": [g["artifact_id"]],
        "question_ref": "Q-RG04-RESOURCE-AUTHORITY",
        "options_presented": ["AUTHORIZE_RESOURCE_AUTHORITY", "DO_NOT_AUTHORIZE_RESOURCE_AUTHORITY", "DEFER"],
        "selected_option": "AUTHORIZE_RESOURCE_AUTHORITY", "owner_constraints": [],
        "consequences_acknowledged": ["finite-resource-authority"], "authority_role": "OWNER_K0",
        "decision_kind": "OWNER_APPROVED_RESOURCE_AUTHORITY",
        "authorized_resource_grant_ref": g["artifact_id"], "authorized_scope": g["scope"]["scope_ref"],
        "authorized_candidate_ref": g["scope"]["candidate_ref"], "authorized_route_ref": g["scope"]["route_ref"],
        "authorized_resource_classes": deepcopy(g["scope"]["resource_classes"]),
        "authorized_resource_limits": deepcopy(g["limits"]), "authorized_attempt_limit": g["attempt_limit"],
        "authorized_valid_until": g["valid_until"],
        "authorized_finalization_policy": deepcopy(g["finalization_policy"]), "non_transitive": True,
    }
    value.update(kw)
    return value


def item(state="ESTIMATED", *, upper=Decimal("2"), dim="TOKENS"):
    if state == "UNKNOWN":
        return {
            "resource_class": "MODEL_INFERENCE", "dimension": dim, "estimate_state": "UNKNOWN",
            "point_estimate": None, "quantiles": [], "upper_bound": None, "confidence": "UNKNOWN",
            "historical_sample_count": None, "unknown_resource_state": "ESTIMATE_UNKNOWN",
        }
    return {
        "resource_class": "MODEL_INFERENCE", "dimension": dim, "estimate_state": "ESTIMATED",
        "point_estimate": upper, "quantiles": [], "upper_bound": upper, "confidence": "HIGH",
        "historical_sample_count": 9, "unknown_resource_state": "KNOWN",
    }


def estimate(*items, status=None, **kw):
    items = list(items or [item()])
    states = [entry["estimate_state"] for entry in items]
    status = status or (
        "ESTIMATED" if all(entry == "ESTIMATED" for entry in states)
        else "UNKNOWN" if all(entry == "UNKNOWN" for entry in states)
        else "PARTIAL"
    )
    value = {
        "artifact_type": "RESOURCE_ESTIMATE", "artifact_id": "RE-1", "produced_by_role": "resource-estimator",
        "assignment_id": "A-1", "input_state_ref": "STATE-1", "status": status, "provenance": ["basis:1"],
        "related_artifacts": [], "subject_ref": "CA-1", "route_ref": "ROUTE-1",
        "estimator_revision_ref": "rg02:merged", "basis_refs": ["basis:1"], "estimates": deepcopy(items),
    }
    value.update(kw)
    return value


class Reader:
    def __init__(self, grants, available=None, *, fail_grants=(), fail_states=()):
        self.grants = deepcopy(grants)
        self.available = dict(available or {})
        self.fail_grants = set(fail_grants)
        self.fail_states = set(fail_states)
        self.calls = []

    def get_grant(self, gid):
        self.calls.append(("get_grant", gid))
        if gid in self.fail_grants:
            raise OSError("backend")
        return deepcopy(self.grants.get(gid))

    def get_resource_state(self, gid, resource_class, dimension):
        self.calls.append(("get_resource_state", gid, resource_class, dimension))
        if (gid, resource_class, dimension) in self.fail_states:
            raise OSError("backend")
        available = Decimal(str(self.available[(gid, resource_class, dimension)]))
        mode = next(
            entry["limit_mode"] for entry in self.grants[gid]["limits"]
            if (entry["resource_class"], entry["dimension"]) == (resource_class, dimension)
        )
        return {
            "grant_id": gid, "resource_class": resource_class, "dimension": dimension, "limit_mode": mode,
            "spend_authority": True,
            "ordinary": {"authorized": available, "reserved": Decimal(0), "committed": Decimal(0), "available": available},
            "finalization": {"authorized": Decimal(0), "reserved": Decimal(0), "committed": Decimal(0), "available": Decimal(0)},
            "exhaustion_state": "NOT_EXHAUSTED", "grant_expired": False,
        }

    def register_grant(self, *args, **kwargs):
        raise AssertionError("resource admission attempted mutation")

    register_child_grant = reserve = commit = release = claim_attempt = register_grant


def reader(g=None, available=5):
    g = g or root()
    states = {
        (g["artifact_id"], entry["resource_class"], entry["dimension"]): available
        for entry in g["limits"] if entry["limit_mode"] != "OBSERVATION_ONLY"
    }
    return Reader({g["artifact_id"]: g}, states)


def run(r, *, g=None, e=None, auth=None, **kw):
    g = root() if g is None else g
    args = dict(
        artifact_id="RA-1", assignment_id="A-1", input_state_ref="STATE-1",
        compiled_assignment={"artifact_id": "CA-1"},
        assignment_admissibility={"artifact_type": "ASSIGNMENT_ADMISSIBILITY", "artifact_id": "AA-1", "status": "ADMISSIBLE"},
        route_ref="ROUTE-1", state_identity="candidate:1", resource_estimate_ref="RE-1",
        resource_estimate=estimate() if e is None else e, resource_grant_ref="G-LEAF", resource_grant=g,
        resource_state_reader=r, authority_resolver=({ODR: decision(g)} if auth is None else auth).get,
        availability_evidence_refs=(), unclassified_metered_side_effect_refs=(), now=NOW,
    )
    args.update(kw)
    return evaluate_resource_admission(**args)


def assert_owner_block(testcase, g, d=None, *, auth=None, reason="AUTHORITY_SOURCE_UNRESOLVED"):
    authority_map = auth if auth is not None else {ODR: (decision(g) if d is None else d)}
    out = run(reader(g), g=g, auth=authority_map)
    testcase.assertIn(reason, out["blocking_reasons"])
    testcase.assertEqual(out["unknown_resource_state"], "KNOWN")
    return out


class ResourceAdmissionTest(unittest.TestCase):
    def test_happy_binding_order_independence_and_exact_decimal(self):
        g = root()
        out = run(reader(g), g=g)
        self.assertEqual(out["status"], "ADMISSIBLE")
        self.assertEqual(out["provenance"], ["AA-1", "G-LEAF", "RE-1"])
        self.assertEqual(out, run(reader(g), g=g))
        for e, reason in [
            (estimate(route_ref="X"), "ESTIMATE_ROUTE_MISMATCH"),
            (estimate(assignment_id="X"), "OTHER_CONTRACT_BLOCK"),
            (estimate(input_state_ref="X"), "OTHER_CONTRACT_BLOCK"),
            (estimate(subject_ref="X"), "OTHER_CONTRACT_BLOCK"),
        ]:
            with self.subTest(reason=reason):
                self.assertIn(reason, run(reader(g), g=g, e=e)["blocking_reasons"])

        exact = Decimal("1.0000000000000000000000000000")
        required = Decimal("1.0000000000000000000000000001")
        g = root(ordinary=exact)
        self.assertIn(
            "RESERVABLE_LIMIT_INSUFFICIENT",
            run(reader(g, exact), g=g, e=estimate(item(upper=required)))["blocking_reasons"],
        )

        g = rich_root()
        d = decision(g)
        d["authorized_resource_classes"].reverse()
        d["authorized_resource_limits"].reverse()
        d["authorized_finalization_policy"]["allowed_purposes"].reverse()
        d["authorized_valid_until"] = "2030-01-01T07:00:00+07:00"
        d["project_id"] = "PROJECT-1"
        self.assertEqual(run(reader(g), g=g, auth={ODR: d})["status"], "ADMISSIBLE")

    def test_owner_authority_negative_matrix(self):
        cases = []
        g = root(authority_ref="MISSING")
        cases.append(("authority ref missing", g, None, {}, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(authority_ref="G-LEAF")
        cases.append(("self reference", g, None, {"G-LEAF": decision(g, artifact_id="G-LEAF")}, "AUTHORITY_SOURCE_UNRESOLVED"))

        g = root()
        d = decision(g)
        d.pop("question_ref")
        cases.append(("schema invalid", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        reduced = {
            "artifact_id": ODR, "artifact_type": "OWNER_DECISION_RECORD", "produced_by_role": "owner-interface",
            "status": "RECORDED", "authority_role": "OWNER_K0", "provenance": ["OWNER/K0"],
        }
        cases.append(("reduced R1 record", root(), reduced, None, "AUTHORITY_SOURCE_UNRESOLVED"))

        for name, field, value in [
            ("wrong artifact type", "artifact_type", "RESOURCE_GRANT"),
            ("wrong producer", "produced_by_role", "control-director"),
            ("wrong status", "status", "DRAFT"),
            ("wrong authority role", "authority_role", "OWNER_K1"),
            ("wrong decision kind", "decision_kind", "CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM"),
            ("non affirmative", "selected_option", "DEFER"),
            ("nontransitive false", "non_transitive", False),
            ("target mismatch", "authorized_resource_grant_ref", "G-OTHER"),
            ("assignment mismatch", "assignment_id", "A-OTHER"),
            ("input mismatch", "input_state_ref", "STATE-OTHER"),
            ("scope mismatch", "authorized_scope", "assignment:OTHER"),
            ("candidate mismatch", "authorized_candidate_ref", "candidate:other"),
            ("route mismatch", "authorized_route_ref", "ROUTE-X"),
            ("attempt mismatch", "authorized_attempt_limit", 4),
            ("validity mismatch", "authorized_valid_until", "2030-01-02T00:00:00Z"),
        ]:
            g = root()
            d = decision(g)
            d[field] = value
            cases.append((name, g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))

        g = root(); d = decision(g); d["options_presented"] = ["DO_NOT_AUTHORIZE_RESOURCE_AUTHORITY", "DEFER"]
        cases.append(("affirmative absent", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_resource_classes"] = ["REMOTE_CI"]
        cases.append(("class set mismatch", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = rich_root(); d = decision(g); d["authorized_resource_limits"] = d["authorized_resource_limits"][:1]
        cases.append(("limit key missing", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_resource_limits"].append({
            "resource_class": "MODEL_INFERENCE", "dimension": "MODEL_CALLS", "limit_mode": "HARD_LIMIT",
            "ordinary_limit": 1, "finalization_reserve": 0,
        })
        cases.append(("extra limit key", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_resource_limits"][0]["limit_mode"] = "HARD_LIMIT"
        cases.append(("mode mismatch", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_resource_limits"][0]["ordinary_limit"] = 6
        cases.append(("ordinary mismatch", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(final=2); d = decision(g); d["authorized_resource_limits"][0]["finalization_reserve"] = 1
        cases.append(("reserve mismatch", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_resource_limits"].append(deepcopy(d["authorized_resource_limits"][0]))
        cases.append(("duplicate owner limit", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_finalization_policy"]["allowed_purposes"] = ["CONTROL_HANDOFF"]
        cases.append(("purpose mismatch", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_finalization_policy"]["protected"] = False
        cases.append(("protected mismatch", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["related_artifacts"] = ["G-OTHER"]
        cases.append(("grant absent related", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["owner_constraints"] = ["interpret me"]
        cases.append(("constraints nonempty", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["qualifications"] = ["interpret me"]
        cases.append(("qualifications nonempty", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))

        unrelated = {
            "artifact_type": "OWNER_DECISION_RECORD", "artifact_id": ODR, "produced_by_role": "owner-interface",
            "assignment_id": "A-1", "input_state_ref": "STATE-1", "status": "RECORDED",
            "provenance": ["OWNER/K0"], "related_artifacts": ["HRA-1"], "question_ref": "Q-HR",
            "options_presented": ["AUTHORIZE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM"],
            "selected_option": "AUTHORIZE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM", "owner_constraints": [],
            "consequences_acknowledged": [], "qualifications": [], "authority_role": "OWNER_K0",
            "decision_kind": "CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM", "project_id": "P-1",
            "authorized_question_id": "RQ-1", "authorized_scope": "bounded",
            "authorized_namespace": "human-research/rq-1", "authorization_id": "HRA-1",
            "non_transitive": True, "default_research_mode_unchanged": True,
        }
        cases.append(("unrelated valid owner decision", root(), unrelated, None, "AUTHORITY_SOURCE_UNRESOLVED"))

        bad_grant = root()
        bad_grant["limits"][0]["resource_class"] = "REMOTE_CI"
        bad_grant["limits"][0]["dimension"] = "RUNNER_MINUTES"
        cases.append(("grant limit outside scope", bad_grant, decision(bad_grant), None, "OTHER_CONTRACT_BLOCK"))

        parent = root("G-P")
        direct_child = child(parent)
        direct_child["authority_source"] = {"authority_type": "OWNER_APPROVED_RESOURCE_AUTHORITY", "authority_ref": ODR}
        cases.append(("child reuses root owner decision", direct_child, decision(parent), None, "OTHER_CONTRACT_BLOCK"))

        autonomy = root(authority_type="AUTONOMY_ENVELOPE", authority_ref="AE-1")
        cases.append(("unsupported autonomy envelope", autonomy, None, {"AE-1": {"artifact_type": "AUTONOMY_ENVELOPE", "artifact_id": "AE-1"}}, "AUTHORITY_SOURCE_UNRESOLVED"))
        other = root(authority_type="OTHER_DURABLE_RESOURCE_AUTHORITY", authority_ref="DA-1")
        cases.append(("unsupported other durable authority", other, None, {"DA-1": {"artifact_type": "DURABLE_RESOURCE_AUTHORITY", "artifact_id": "DA-1"}}, "AUTHORITY_SOURCE_UNRESOLVED"))

        for name, g, d, authority_map, reason in cases:
            with self.subTest(name=name):
                assert_owner_block(self, g, d, auth=authority_map, reason=reason)

    def test_parent_chain_root_owner_binding_and_shared_parent_availability(self):
        parent = root("G-P", ordinary=5, final=0)
        parent["scope"].update(candidate_ref=None, route_ref=None)
        leaf = child(parent)
        states = {
            ("G-P", "MODEL_INFERENCE", "TOKENS"): 5,
            ("G-LEAF", "MODEL_INFERENCE", "TOKENS"): 5,
        }
        r = Reader({"G-P": parent, "G-LEAF": leaf}, states)
        authority_map = {ODR: decision(parent)}
        self.assertEqual(run(r, g=leaf, auth=authority_map)["status"], "ADMISSIBLE")

        invalid_owner = decision(parent)
        invalid_owner["authorized_attempt_limit"] = 99
        out = run(r, g=leaf, auth={ODR: invalid_owner})
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", out["blocking_reasons"])

        r.available[("G-P", "MODEL_INFERENCE", "TOKENS")] = 1
        out = run(r, g=leaf, auth=authority_map, e=estimate(item(upper=2)))
        self.assertEqual(out["evaluations"][0]["available_amount"], Decimal(1))
        self.assertIn("RESERVABLE_LIMIT_INSUFFICIENT", out["blocking_reasons"])

    def test_complete_estimate_validator_and_unknown_policy(self):
        malformed = []
        for field in ("point_estimate", "quantiles", "confidence", "historical_sample_count", "upper_bound"):
            entry = item(); entry.pop(field); malformed.append(estimate(entry))
        entry = item(); entry["extra"] = 1; malformed.append(estimate(entry))
        artifact = estimate(); artifact["extra"] = 1; malformed.append(artifact)
        for quantiles in (
            [{"probability": 0, "quantity": 1}],
            [{"probability": Decimal("1.1"), "quantity": 1}],
            [{"probability": Decimal(".9"), "quantity": -1}],
        ):
            entry = item(); entry["quantiles"] = quantiles; malformed.append(estimate(entry))
        entry = item(); entry["confidence"] = "CERTAIN"; malformed.append(estimate(entry))
        for value in (Decimal("-1"), Decimal("NaN")):
            entry = item(); entry["point_estimate"] = value; malformed.append(estimate(entry))
        entry = item(); entry["unknown_resource_state"] = "ESTIMATE_UNKNOWN"; malformed.append(estimate(entry))
        for field, value in (
            ("point_estimate", 1),
            ("quantiles", [{"probability": Decimal(".9"), "quantity": 1}]),
            ("upper_bound", 1),
            ("historical_sample_count", 0),
        ):
            entry = item("UNKNOWN"); entry[field] = value; malformed.append(estimate(entry))
        malformed += [
            estimate(item(), status="UNKNOWN"),
            estimate(item("UNKNOWN"), status="ESTIMATED"),
            estimate(item(), status="PARTIAL"),
        ]
        entry = item(); malformed.append(estimate(entry, deepcopy(entry)))

        for artifact in malformed:
            with self.subTest(status=artifact.get("status")):
                g = root()
                out = run(reader(g), g=g, e=artifact)
                self.assertIn("OTHER_CONTRACT_BLOCK", out["blocking_reasons"])
                self.assertEqual(out["evaluations"], [])

        entry = item(); entry["upper_bound"] = None
        g = root()
        out = run(reader(g), g=g, e=estimate(entry))
        self.assertIn("UNKNOWN_REQUIRED_RESOURCE", out["blocking_reasons"])
        self.assertNotIn("OTHER_CONTRACT_BLOCK", out["blocking_reasons"])

    def test_availability_modes_failures_no_mutation_and_decimal_context(self):
        g = root()
        self.assertIn("GRANT_MISSING", run(Reader({}, {}), g=g)["blocking_reasons"])
        failure = run(Reader({"G-LEAF": g}, {}, fail_grants={"G-LEAF"}), g=g)
        self.assertEqual(failure["unknown_resource_state"], "AVAILABILITY_UNKNOWN")

        observation = root(mode="OBSERVATION_ONLY")
        r = Reader({"G-LEAF": observation}, {})
        self.assertEqual(run(r, g=observation, e=estimate(item("UNKNOWN")))["status"], "ADMISSIBLE")
        self.assertFalse(any(call[0] == "get_resource_state" for call in r.calls))
        self.assertIn(
            "UNCLASSIFIED_METERED_SIDE_EFFECT",
            run(reader(g), g=g, unclassified_metered_side_effect_refs=("surface:x",))["blocking_reasons"],
        )

        old_precision = getcontext().prec
        try:
            getcontext().prec = 2
            low = run(reader(g), g=g)
            getcontext().prec = 50
            high = run(reader(g), g=g)
        finally:
            getcontext().prec = old_precision
        self.assertEqual(low, high)

        r = reader(g)
        before = (deepcopy(r.grants), deepcopy(r.available))
        run(r, g=g)
        self.assertEqual(before, (r.grants, r.available))

        with tempfile.TemporaryDirectory() as td:
            ledger = ResourceLedger(Path(td) / "shared.sqlite3")
            ledger.initialize()
            parent = root("G-P", ordinary=5, final=0)
            parent["scope"].update(candidate_ref=None, route_ref=None)
            child_a = child(parent, "G-A", ordinary=5, final=0)
            child_b = child(parent, "G-LEAF", ordinary=5, final=0)
            ledger.register_grant(parent)
            ledger.register_child_grant(child_a)
            ledger.register_child_grant(child_b)
            ledger.reserve("G-A", "MODEL_INFERENCE", "TOKENS", 4, "R-A", "OP-A", "K-A", now=NOW)

            authority_map = {ODR: decision(parent)}
            blocked = run(ledger, g=child_b, auth=authority_map, e=estimate(item(upper=2)))
            self.assertEqual(blocked["evaluations"][0]["available_amount"], Decimal(1))
            self.assertIn("RESERVABLE_LIMIT_INSUFFICIENT", blocked["blocking_reasons"])

            before_state = ledger.get_resource_state("G-LEAF", "MODEL_INFERENCE", "TOKENS")
            run(ledger, g=child_b, auth=authority_map, e=estimate(item(upper=1)))
            self.assertEqual(before_state, ledger.get_resource_state("G-LEAF", "MODEL_INFERENCE", "TOKENS"))

            ledger.release("R-A", "REL-A", now=NOW)
            self.assertEqual(
                run(ledger, g=child_b, auth=authority_map, e=estimate(item(upper=2)))["status"],
                "ADMISSIBLE",
            )


if __name__ == "__main__":
    unittest.main()
