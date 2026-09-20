from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Context, Decimal, ROUND_DOWN, ROUND_UP, localcontext
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from tools.resource_ledger import (
    AuthorityViolation,
    GrantExpired,
    IdempotencyConflict,
    InsufficientCapacity,
    InvalidGrant,
    InvalidReservationTransition,
    ResourceLedger,
    ResourceLedgerError,
)

UTC = timezone.utc
T0 = datetime(2026, 9, 20, 0, 0, tzinfo=UTC)
T1 = datetime(2026, 9, 20, 1, 0, tzinfo=UTC)
T2 = datetime(2026, 9, 20, 2, 0, tzinfo=UTC)
FUTURE = "2030-01-01T00:00:00Z"
PURPOSES = ["RESULT_RECONCILIATION", "DURABLE_PARTIAL_OUTPUT", "FINAL_ACCOUNTING", "CONTROL_HANDOFF"]


def grant(
    grant_id: str = "G-ROOT",
    *,
    ordinary=5,
    final=2,
    mode="RESERVABLE_LIMIT",
    attempts=10,
    valid_until=FUTURE,
    scope_ref="project:p",
    candidate_ref=None,
    route_ref=None,
    purposes=None,
    resource_classes=None,
    limits=None,
):
    classes = resource_classes or ["MODEL_INFERENCE"]
    if limits is None:
        if mode == "OBSERVATION_ONLY":
            limits = [{
                "resource_class": "MODEL_INFERENCE", "dimension": "TOKENS", "limit_mode": mode,
                "ordinary_limit": None, "finalization_reserve": None,
            }]
        else:
            limits = [{
                "resource_class": "MODEL_INFERENCE", "dimension": "TOKENS", "limit_mode": mode,
                "ordinary_limit": ordinary, "finalization_reserve": final,
            }]
    return {
        "artifact_type": "RESOURCE_GRANT",
        "artifact_id": grant_id,
        "produced_by_role": "control-director",
        "assignment_id": "A-1",
        "input_state_ref": "STATE-1",
        "status": "AUTHORIZED",
        "provenance": ["owner:approval"],
        "related_artifacts": [],
        "issued_by": "control-director",
        "authority_source": {
            "authority_type": "OWNER_APPROVED_RESOURCE_AUTHORITY",
            "authority_ref": "authority:owner-1",
        },
        "parent_grant_ref": None,
        "scope": {
            "scope_ref": scope_ref,
            "candidate_ref": candidate_ref,
            "route_ref": route_ref,
            "resource_classes": classes,
        },
        "limits": limits,
        "attempt_limit": attempts,
        "valid_until": valid_until,
        "finalization_policy": {"protected": True, "allowed_purposes": purposes or PURPOSES[:]},
    }


def child(parent, child_id="G-CHILD", **changes):
    c = deepcopy(parent)
    c["artifact_id"] = child_id
    c["provenance"] = ["parent:delegation"]
    c["authority_source"] = {
        "authority_type": "PARENT_RESOURCE_GRANT",
        "authority_ref": parent["artifact_id"],
    }
    c["parent_grant_ref"] = parent["artifact_id"]
    for key, value in changes.items():
        if key in {"scope_ref", "candidate_ref", "route_ref", "resource_classes"}:
            c["scope"][key] = value
        elif key == "purposes":
            c["finalization_policy"]["allowed_purposes"] = value
        else:
            c[key] = value
    return c


def evidence(child_scope="task:t", parent_scope="project:p", ref="scope-proof:123"):
    return {
        "child_scope_ref": child_scope,
        "parent_scope_ref": parent_scope,
        "evidence_ref": ref,
    }


class ResourceLedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "shared.sqlite3")
        self.ledger = ResourceLedger(self.db)
        self.ledger.initialize()

    def tearDown(self):
        self.tmp.cleanup()

    def register(self, g=None):
        g = g or grant()
        self.ledger.register_grant(g)
        return g

    def reserve(self, *, gid="G-ROOT", qty=1, rid="R-1", op="OP-1", key="idem-r1", pool="ORDINARY", purpose=None, expires=None, now=T0):
        return self.ledger.reserve(
            gid, "MODEL_INFERENCE", "TOKENS", qty, rid, op, key,
            pool=pool, purpose=purpose, expires_at=expires, now=now,
        )

    def test_01_shared_file_ledger_initializes(self):
        self.assertTrue(Path(self.db).exists())
        self.ledger.initialize()

    def test_02_memory_authority_backend_is_rejected(self):
        for path in [":memory:", "file::memory:?cache=shared", "file:ledger?mode=memory&cache=shared"]:
            with self.subTest(path=path), self.assertRaises(ResourceLedgerError):
                ResourceLedger(path)

    def test_03_valid_root_grant_registers_and_reads_back(self):
        self.register()
        self.assertEqual(self.ledger.get_grant("G-ROOT")["limits"][0]["ordinary_limit"], Decimal("5"))

    def test_04_same_semantic_root_registration_is_idempotent(self):
        g = self.register()
        reordered = dict(reversed(list(g.items())))
        self.ledger.register_grant(reordered)
        self.assertEqual(self.ledger.get_grant("G-ROOT")["artifact_id"], "G-ROOT")

    def test_05_conflicting_same_grant_id_fails(self):
        g = self.register()
        conflict = deepcopy(g)
        conflict["limits"][0]["ordinary_limit"] = 6
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_grant(conflict)

    def test_06_equal_scope_child_passes_without_evidence(self):
        p = self.register()
        self.ledger.register_child_grant(child(p))
        self.assertIsNone(self.ledger.get_scope_relation_evidence("G-CHILD"))

    def test_07_different_scope_without_evidence_fails(self):
        p = self.register()
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, scope_ref="task:t"))

    def test_08_different_scope_bare_tuple_relation_fails(self):
        p = self.register()
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, scope_ref="task:t"), {("task:t", "project:p")})

    def test_09_different_scope_matching_durable_evidence_passes(self):
        p = self.register()
        self.ledger.register_child_grant(child(p, scope_ref="task:t"), evidence())
        self.assertEqual(self.ledger.get_scope_relation_evidence("G-CHILD")["evidence_ref"], "scope-proof:123")

    def test_10_scope_evidence_mismatched_refs_fail(self):
        p = self.register()
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(
                child(p, scope_ref="task:t"), evidence(child_scope="task:other")
            )

    def test_11_scope_evidence_survives_reopen(self):
        p = self.register()
        self.ledger.register_child_grant(child(p, scope_ref="task:t"), evidence())
        reopened = ResourceLedger(self.db)
        self.assertEqual(reopened.get_scope_relation_evidence("G-CHILD"), evidence())

    def test_12_conflicting_scope_evidence_reregistration_fails(self):
        p = self.register()
        c = child(p, scope_ref="task:t")
        self.ledger.register_child_grant(c, evidence())
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c, evidence(ref="scope-proof:other"))

    def test_13_get_grant_does_not_expose_scope_evidence_metadata(self):
        p = self.register()
        self.ledger.register_child_grant(child(p, scope_ref="task:t"), evidence())
        out = self.ledger.get_grant("G-CHILD")
        self.assertNotIn("scope_relation_evidence", out)
        self.assertNotIn("evidence_ref", repr(out))

    def test_14_root_scope_evidence_readback_is_null(self):
        self.register()
        self.assertIsNone(self.ledger.get_scope_relation_evidence("G-ROOT"))

    def test_15_resource_class_expansion_fails(self):
        p = self.register()
        c = child(p, resource_classes=["MODEL_INFERENCE", "REMOTE_CI"])
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c)

    def test_16_candidate_binding_expansion_fails(self):
        p = grant(candidate_ref="candidate:c")
        self.register(p)
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, candidate_ref="candidate:other"))

    def test_17_route_binding_expansion_fails(self):
        p = grant(route_ref="route:r")
        self.register(p)
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, route_ref=None))

    def test_18_child_attempt_expansion_fails(self):
        p = grant(attempts=3)
        self.register(p)
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, attempt_limit=4))

    def test_19_child_validity_expansion_fails(self):
        p = grant(valid_until="2026-09-20T02:00:00Z")
        self.register(p)
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, valid_until="2026-09-20T03:00:00Z"))

    def test_20_hard_to_reservable_narrowing_passes(self):
        p = grant(mode="HARD_LIMIT")
        self.register(p)
        c = child(p)
        c["limits"][0]["limit_mode"] = "RESERVABLE_LIMIT"
        self.ledger.register_child_grant(c)

    def test_21_reservable_to_hard_expansion_fails(self):
        p = self.register()
        c = child(p)
        c["limits"][0]["limit_mode"] = "HARD_LIMIT"
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c)

    def test_22_observation_parent_to_spend_authority_fails(self):
        p = grant(mode="OBSERVATION_ONLY")
        self.register(p)
        c = child(p)
        c["limits"][0].update(limit_mode="RESERVABLE_LIMIT", ordinary_limit=1, finalization_reserve=0)
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c)

    def test_23_child_ordinary_expansion_fails(self):
        p = self.register()
        c = child(p)
        c["limits"][0]["ordinary_limit"] = 6
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c)

    def test_24_child_finalization_expansion_fails(self):
        p = self.register()
        c = child(p)
        c["limits"][0]["finalization_reserve"] = 3
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c)

    def test_25_child_finalization_purpose_expansion_fails(self):
        p = grant(purposes=["FINAL_ACCOUNTING"])
        self.register(p)
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, purposes=["FINAL_ACCOUNTING", "CONTROL_HANDOFF"]))

    def test_26_child_purpose_subset_passes(self):
        p = self.register()
        self.ledger.register_child_grant(child(p, purposes=["FINAL_ACCOUNTING"]))

    def test_27_ordinary_reserve_succeeds(self):
        self.register()
        result = self.reserve(qty=2)
        self.assertEqual(result["status"], "RESERVED")
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["reserved"], Decimal("2"))

    def test_28_ordinary_cannot_borrow_finalization_capacity(self):
        self.register(grant(ordinary=1, final=9))
        self.reserve(qty=1)
        with self.assertRaises(InsufficientCapacity):
            self.reserve(qty=1, rid="R-2", op="OP-2", key="K-2")

    def test_29_finalization_requires_purpose(self):
        self.register()
        with self.assertRaises(AuthorityViolation):
            self.reserve(pool="FINALIZATION")

    def test_30_unauthorized_finalization_purpose_fails(self):
        self.register(grant(purposes=["FINAL_ACCOUNTING"]))
        with self.assertRaises(AuthorityViolation):
            self.reserve(pool="FINALIZATION", purpose="CONTROL_HANDOFF")

    def test_31_finalization_is_ancestor_bounded(self):
        p = grant(final=1)
        self.register(p)
        c = child(p)
        self.ledger.register_child_grant(c)
        self.reserve(gid="G-CHILD", pool="FINALIZATION", purpose="FINAL_ACCOUNTING")
        with self.assertRaises(InsufficientCapacity):
            self.reserve(gid="G-CHILD", rid="R-2", op="O-2", key="K-2", pool="FINALIZATION", purpose="FINAL_ACCOUNTING")

    def test_32_same_reserve_retry_is_idempotent(self):
        self.register()
        first = self.reserve()
        second = self.ledger.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 1, "R-1", "OP-1", "idem-r1", now=T1)
        self.assertEqual(first, second)

    def test_33_conflicting_idempotency_key_fails(self):
        self.register()
        self.reserve()
        with self.assertRaises(IdempotencyConflict):
            self.ledger.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 2, "R-2", "OP-2", "idem-r1", now=T0)

    def test_34_conflicting_reservation_id_fails(self):
        self.register()
        self.reserve()
        with self.assertRaises(IdempotencyConflict):
            self.ledger.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 2, "R-1", "OP-X", "K-X", now=T0)

    def test_35_commit_converts_reserved_to_committed(self):
        self.register()
        self.reserve(qty=3)
        out = self.ledger.commit("R-1", 3, "C-1", now=T1)
        self.assertEqual(out["status"], "COMMITTED")
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]
        self.assertEqual((state["reserved"], state["committed"]), (Decimal("0"), Decimal("3")))

    def test_36_commit_smaller_releases_remainder(self):
        self.register()
        self.reserve(qty=4)
        self.ledger.commit("R-1", 1, "C-1", now=T1)
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"], Decimal("4"))

    def test_37_commit_greater_than_reserved_fails(self):
        self.register()
        self.reserve(qty=1)
        with self.assertRaises(InvalidReservationTransition):
            self.ledger.commit("R-1", 2, "C-1", now=T1)

    def test_38_duplicate_commit_is_idempotent(self):
        self.register()
        self.reserve(qty=2)
        first = self.ledger.commit("R-1", 1, "C-1", now=T1)
        second = self.ledger.commit("R-1", 1, "C-1", now=T2)
        self.assertEqual(first, second)

    def test_39_release_restores_availability(self):
        self.register()
        self.reserve(qty=3)
        self.ledger.release("R-1", "REL-1")
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"], Decimal("5"))

    def test_40_duplicate_release_is_idempotent(self):
        self.register()
        self.reserve()
        first = self.ledger.release("R-1", "REL-1")
        second = self.ledger.release("R-1", "REL-1")
        self.assertEqual(first, second)

    def test_41_commit_after_release_fails(self):
        self.register()
        self.reserve()
        self.ledger.release("R-1", "REL-1")
        with self.assertRaises(InvalidReservationTransition):
            self.ledger.commit("R-1", 1, "C-1", now=T1)

    def test_42_expiry_restores_availability(self):
        self.register()
        self.reserve(qty=4, expires=T1)
        self.assertEqual(self.ledger.expire_reservations(T1), ["R-1"])
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"], Decimal("5"))

    def test_43_fractional_expiry_not_due_at_whole_second(self):
        self.register()
        half = T1 + timedelta(microseconds=500000)
        self.reserve(expires=half)
        self.assertEqual(self.ledger.expire_reservations(T1), [])
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["reserved"], Decimal("1"))

    def test_44_fractional_expiry_due_at_exact_instant(self):
        self.register()
        half = T1 + timedelta(microseconds=500000)
        self.reserve(expires=half)
        self.assertEqual(self.ledger.expire_reservations(half), ["R-1"])

    def test_45_mixed_fractional_expiry_only_due_row_expires(self):
        self.register()
        half = T1 + timedelta(microseconds=500000)
        self.reserve(rid="R-1", op="O-1", key="K-1", expires=T1)
        self.reserve(rid="R-2", op="O-2", key="K-2", expires=half)
        self.assertEqual(self.ledger.expire_reservations(T1), ["R-1"])
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["reserved"], Decimal("1"))

    def test_46_timezone_offset_expiry_is_chronological(self):
        self.register()
        self.reserve(expires="2026-09-20T08:00:00+07:00")
        self.assertEqual(self.ledger.expire_reservations("2026-09-20T01:00:00Z"), ["R-1"])

    def test_47_persisted_timestamp_has_fixed_microsecond_utc_format(self):
        self.register()
        out = self.reserve(expires=T1)
        self.assertEqual(out["created_at"], "2026-09-20T00:00:00.000000Z")
        self.assertEqual(out["expires_at"], "2026-09-20T01:00:00.000000Z")

    def test_48_malformed_stored_expiry_fails_closed_and_rolls_back(self):
        self.register()
        self.reserve(rid="R-1", op="O-1", key="K-1", expires=T1)
        self.reserve(rid="R-2", op="O-2", key="K-2", expires=T1)
        conn = sqlite3.connect(self.db)
        try:
            conn.execute("UPDATE reservations SET expires_at='bad-timestamp' WHERE reservation_id='R-2'")
            conn.commit()
        finally:
            conn.close()
        with self.assertRaises(ResourceLedgerError):
            self.ledger.expire_reservations(T1)
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]
        self.assertEqual(state["reserved"], Decimal("2"))

    def test_49_committed_usage_does_not_expire(self):
        self.register()
        self.reserve(qty=2, expires=T2)
        self.ledger.commit("R-1", 2, "C-1", now=T1)
        self.assertEqual(self.ledger.expire_reservations(T2), [])

    def test_50_expired_grant_rejects_new_reserve(self):
        self.register(grant(valid_until="2026-09-20T01:00:00Z"))
        with self.assertRaises(GrantExpired):
            self.reserve(now=T1)

    def test_51_pre_expiry_reservation_may_commit_after_grant_expiry(self):
        self.register(grant(valid_until="2026-09-20T01:00:00Z"))
        self.reserve(now=T0)
        self.assertEqual(self.ledger.commit("R-1", 1, "C-1", now=T2)["status"], "COMMITTED")

    def test_52_ten_concurrent_reservations_exactly_five_succeed(self):
        self.register(grant(ordinary=5, final=0))
        barrier = threading.Barrier(10)
        def worker(i):
            local = ResourceLedger(self.db)
            barrier.wait()
            try:
                local.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 1, f"R-{i}", f"O-{i}", f"K-{i}", now=T0)
                return "ok"
            except InsufficientCapacity:
                return "capacity"
        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(worker, range(10)))
        self.assertEqual(results.count("ok"), 5)
        self.assertEqual(results.count("capacity"), 5)
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]
        self.assertEqual((state["reserved"], state["committed"], state["available"]), (Decimal("5"), Decimal("0"), Decimal("0")))

    def test_53_sibling_children_cannot_overspend_shared_parent(self):
        p = grant(ordinary=5, final=0)
        self.register(p)
        self.ledger.register_child_grant(child(p, "C-1"))
        self.ledger.register_child_grant(child(p, "C-2"))
        barrier = threading.Barrier(10)
        def worker(i):
            gid = "C-1" if i % 2 == 0 else "C-2"
            local = ResourceLedger(self.db)
            barrier.wait()
            try:
                local.reserve(gid, "MODEL_INFERENCE", "TOKENS", 1, f"SR-{i}", f"SO-{i}", f"SK-{i}", now=T0)
                return True
            except InsufficientCapacity:
                return False
        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(worker, range(10)))
        self.assertEqual(sum(results), 5)
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["reserved"], Decimal("5"))

    def test_54_atomic_attempt_limit_works(self):
        self.register(grant(attempts=5))
        barrier = threading.Barrier(10)
        def worker(i):
            local = ResourceLedger(self.db)
            barrier.wait()
            try:
                local.claim_attempt("G-ROOT", f"O-{i}", f"K-{i}", now=T0)
                return True
            except InsufficientCapacity:
                return False
        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(worker, range(10)))
        self.assertEqual(sum(results), 5)

    def test_55_sibling_attempts_cannot_exceed_parent(self):
        p = grant(attempts=4)
        self.register(p)
        self.ledger.register_child_grant(child(p, "C-1", attempt_limit=4))
        self.ledger.register_child_grant(child(p, "C-2", attempt_limit=4))
        barrier = threading.Barrier(8)
        def worker(i):
            gid = "C-1" if i % 2 == 0 else "C-2"
            local = ResourceLedger(self.db)
            barrier.wait()
            try:
                local.claim_attempt(gid, f"O-{i}", f"K-{i}", now=T0)
                return True
            except InsufficientCapacity:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(worker, range(8)))
        self.assertEqual(sum(results), 4)

    def test_56_duplicate_attempt_is_idempotent(self):
        self.register(grant(attempts=1))
        first = self.ledger.claim_attempt("G-ROOT", "O-1", "K-1", now=T0)
        second = self.ledger.claim_attempt("G-ROOT", "O-1", "K-1", now=T1)
        self.assertEqual(first, second)

    def test_57_observation_only_reserve_fails(self):
        self.register(grant(mode="OBSERVATION_ONLY"))
        with self.assertRaises(AuthorityViolation):
            self.reserve()

    def test_58_read_model_exhaustion_states(self):
        self.register(grant(ordinary=1, final=1))
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["exhaustion_state"], "NOT_EXHAUSTED")
        self.reserve(qty=1)
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["exhaustion_state"], "ORDINARY_LIMIT_EXHAUSTED_FINALIZATION_ONLY")
        self.reserve(rid="RF", op="OF", key="KF", pool="FINALIZATION", purpose="FINAL_ACCOUNTING")
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["exhaustion_state"], "EXHAUSTED")

    def test_59_high_precision_grant_round_trips_exactly(self):
        value = Decimal("99999999999999999999999999999")
        self.register(grant(ordinary=value))
        self.assertEqual(self.ledger.get_grant("G-ROOT")["limits"][0]["ordinary_limit"], value)

    def test_60_high_precision_distinct_grants_have_distinct_fingerprints_low_context(self):
        g1 = grant(ordinary=Decimal("99999999999999999999999999999"))
        g2 = grant(ordinary=Decimal("100000000000000000000000000000"))
        with localcontext(Context(prec=5, rounding=ROUND_DOWN)):
            _, fp1 = ResourceLedger._validate_grant(g1)
            _, fp2 = ResourceLedger._validate_grant(g2)
        self.assertNotEqual(fp1, fp2)

    def test_61_full_limit_plus_one_e_minus_28_is_rejected(self):
        self.register(grant(ordinary=Decimal("1"), final=0))
        self.reserve(qty=Decimal("1"))
        with self.assertRaises(InsufficientCapacity):
            self.reserve(qty=Decimal("1E-28"), rid="R-2", op="O-2", key="K-2")

    def test_62_one_e_minus_28_reservation_exact_available(self):
        self.register(grant(ordinary=Decimal("1"), final=0))
        self.reserve(qty=Decimal("1E-28"))
        available = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"]
        self.assertEqual(available, Decimal("0.9999999999999999999999999999"))

    def test_63_decimal_context_precision_5_round_down_cannot_hide_overspend(self):
        with localcontext(Context(prec=5, rounding=ROUND_DOWN)):
            self.register(grant(ordinary=Decimal("1"), final=0))
            self.reserve(qty=Decimal("1"))
            with self.assertRaises(InsufficientCapacity):
                self.reserve(qty=Decimal("1E-28"), rid="R-2", op="O-2", key="K-2")

    def test_64_decimal_context_precision_50_round_up_same_semantics(self):
        with localcontext(Context(prec=50, rounding=ROUND_UP)):
            self.register(grant(ordinary=Decimal("1"), final=0))
            self.reserve(qty=Decimal("1E-28"))
            available = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"]
        self.assertEqual(available, Decimal("0.9999999999999999999999999999"))

    def test_65_decimal_canonicalization_1_2300(self):
        self.assertEqual(ResourceLedger._decimal_text(Decimal("1.2300")), "1.23")

    def test_66_decimal_canonicalization_1e3(self):
        self.assertEqual(ResourceLedger._decimal_text(Decimal("1E+3")), "1000")

    def test_67_decimal_canonicalization_1e_minus_28(self):
        self.assertEqual(ResourceLedger._decimal_text(Decimal("1E-28")), "0.0000000000000000000000000001")

    def test_68_decimal_canonicalization_large_integer_no_rounding(self):
        text = "99999999999999999999999999999"
        with localcontext(Context(prec=5, rounding=ROUND_UP)):
            self.assertEqual(ResourceLedger._decimal_text(Decimal(text)), text)

    def test_69_commit_zero_releases_all(self):
        self.register()
        self.reserve(qty=2)
        out = self.ledger.commit("R-1", 0, "C-0", now=T1)
        self.assertEqual(out["committed_quantity"], Decimal("0"))
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"], Decimal("5"))

    def test_70_release_after_commit_fails(self):
        self.register()
        self.reserve()
        self.ledger.commit("R-1", 1, "C-1", now=T1)
        with self.assertRaises(InvalidReservationTransition):
            self.ledger.release("R-1", "REL")

    def test_71_reservation_expired_at_commit_is_released_and_fails(self):
        self.register()
        self.reserve(qty=2, expires=T1)
        with self.assertRaises(InvalidReservationTransition):
            self.ledger.commit("R-1", 1, "C-1", now=T1)
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"], Decimal("5"))

    def test_72_bool_quantity_rejected(self):
        self.register()
        with self.assertRaises(ResourceLedgerError):
            self.reserve(qty=True)

    def test_73_nan_and_infinity_rejected(self):
        self.register()
        for value in [float("nan"), float("inf"), float("-inf")]:
            with self.subTest(value=value), self.assertRaises(ResourceLedgerError):
                self.reserve(qty=value)

    def test_74_negative_quantity_rejected(self):
        self.register()
        with self.assertRaises(ResourceLedgerError):
            self.reserve(qty=-1)

    def test_75_zero_reservation_rejected(self):
        self.register()
        with self.assertRaises(ResourceLedgerError):
            self.reserve(qty=0)

    def test_76_invalid_grant_bool_attempt_rejected(self):
        with self.assertRaises(InvalidGrant):
            self.ledger.register_grant(grant(attempts=True))

    def test_77_invalid_grant_naive_valid_until_rejected(self):
        with self.assertRaises(InvalidGrant):
            self.ledger.register_grant(grant(valid_until="2030-01-01T00:00:00"))

    def test_78_parent_unbound_candidate_can_bind_child(self):
        p = self.register()
        self.ledger.register_child_grant(child(p, candidate_ref="candidate:exact"))

    def test_79_parent_unbound_route_can_bind_child(self):
        p = self.register()
        self.ledger.register_child_grant(child(p, route_ref="route:exact"))

    def test_80_finalization_does_not_change_ordinary_pool(self):
        self.register(grant(ordinary=5, final=2))
        self.reserve(qty=2, pool="FINALIZATION", purpose="FINAL_ACCOUNTING")
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertEqual(state["ordinary"]["available"], Decimal("5"))
        self.assertEqual(state["finalization"]["available"], Decimal("0"))

    def test_81_observation_read_model_has_no_spend_authority(self):
        self.register(grant(mode="OBSERVATION_ONLY"))
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertFalse(state["spend_authority"])
        self.assertEqual(state["ordinary"]["authorized"], Decimal("0"))

    def test_82_conflicting_commit_idempotency_key_fails(self):
        self.register()
        self.reserve(qty=2)
        self.ledger.commit("R-1", 1, "CK", now=T1)
        with self.assertRaises(IdempotencyConflict):
            self.ledger.commit("R-1", 2, "CK", now=T2)

    def test_83_conflicting_attempt_idempotency_key_fails(self):
        self.register(grant(attempts=3))
        self.ledger.claim_attempt("G-ROOT", "O-1", "AK", now=T0)
        with self.assertRaises(IdempotencyConflict):
            self.ledger.claim_attempt("G-ROOT", "O-2", "AK", now=T1)

    def test_84_scope_evidence_registration_is_atomic_with_grant(self):
        p = self.register()
        c = child(p, scope_ref="task:t")
        bad = evidence(ref="")
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c, bad)
        with self.assertRaises(AuthorityViolation):
            self.ledger.get_grant("G-CHILD")

    def test_85_scope_evidence_conflict_does_not_mutate_preserved_record(self):
        p = self.register()
        c = child(p, scope_ref="task:t")
        self.ledger.register_child_grant(c, evidence())
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c, evidence(ref="scope-proof:conflict"))
        self.assertEqual(self.ledger.get_scope_relation_evidence("G-CHILD"), evidence())

    def test_86_exact_child_capacity_comparison_independent_of_context(self):
        p = grant(ordinary=Decimal("1"))
        self.register(p)
        c = child(p)
        c["limits"][0]["ordinary_limit"] = Decimal("1.0000000000000000000000000001")
        with localcontext(Context(prec=5, rounding=ROUND_DOWN)):
            with self.assertRaises(AuthorityViolation):
                self.ledger.register_child_grant(c)

    def test_87_available_exact_after_multiple_tiny_reservations(self):
        self.register(grant(ordinary=Decimal("1"), final=0))
        for i in range(3):
            self.reserve(qty=Decimal("1E-28"), rid=f"R-{i}", op=f"O-{i}", key=f"K-{i}")
        available = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"]
        self.assertEqual(available, Decimal("0.9999999999999999999999999997"))

    def test_88_exact_committed_totals_ignore_ambient_context(self):
        self.register(grant(ordinary=Decimal("1"), final=0))
        for i in range(2):
            self.reserve(qty=Decimal("1E-28"), rid=f"R-{i}", op=f"O-{i}", key=f"K-{i}")
            self.ledger.commit(f"R-{i}", Decimal("1E-28"), f"C-{i}", now=T1)
        with localcontext(Context(prec=5, rounding=ROUND_UP)):
            state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]
        self.assertEqual(state["committed"], Decimal("2E-28"))
        self.assertEqual(state["available"], Decimal("0.9999999999999999999999999998"))

    def test_89_no_datetime_text_ordering_in_expiry_sql(self):
        source = Path(__file__).resolve().parents[1].joinpath("tools/resource_ledger.py").read_text()
        self.assertNotIn("expires_at <= ?", source)
        self.assertNotIn("expires_at < ?", source)

    def test_90_no_decimal_normalize_in_production(self):
        source = Path(__file__).resolve().parents[1].joinpath("tools/resource_ledger.py").read_text()
        self.assertNotIn(".normalize(", source)

    def test_91_same_authority_semantics_across_decimal_contexts(self):
        def run_case(name, context):
            db = str(Path(self.tmp.name) / f"{name}.sqlite3")
            ledger = ResourceLedger(db)
            ledger.initialize()
            with localcontext(context):
                ledger.register_grant(grant(ordinary=Decimal("1"), final=0))
                ledger.reserve(
                    "G-ROOT", "MODEL_INFERENCE", "TOKENS", Decimal("1E-28"),
                    "R-1", "O-1", "K-1", now=T0,
                )
                available_after_tiny = ledger.get_resource_state(
                    "G-ROOT", "MODEL_INFERENCE", "TOKENS"
                )["ordinary"]["available"]
                ledger.reserve(
                    "G-ROOT", "MODEL_INFERENCE", "TOKENS",
                    Decimal("0.9999999999999999999999999999"),
                    "R-2", "O-2", "K-2", now=T0,
                )
                with self.assertRaises(InsufficientCapacity):
                    ledger.reserve(
                        "G-ROOT", "MODEL_INFERENCE", "TOKENS", Decimal("1E-28"),
                        "R-3", "O-3", "K-3", now=T0,
                    )
                final_available = ledger.get_resource_state(
                    "G-ROOT", "MODEL_INFERENCE", "TOKENS"
                )["ordinary"]["available"]
            return available_after_tiny, final_available

        low = run_case("ctx-low", Context(prec=5, rounding=ROUND_DOWN))
        high = run_case("ctx-high", Context(prec=50, rounding=ROUND_UP))
        self.assertEqual(low, high)
        self.assertEqual(low, (Decimal("0.9999999999999999999999999999"), Decimal("0")))


if __name__ == "__main__":
    unittest.main()
