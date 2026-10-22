from __future__ import annotations

from copy import deepcopy
import tempfile
import unittest

from tools.durable_artifact_port import LocalFileDurableReferencePort
from tools.project_topology import (
    TopologyError, build_bootstrap, classify_topology_change,
    materialize_bootstrap, materialize_project_payload, resolve_address,
    verify_bootstrap,
)


def plan():
    return {
        "artifact_type": "TOPOLOGY_PLAN", "artifact_id": "TOPOLOGY-PLAN-1",
        "produced_by_role": "executor", "assignment_id": "ASSIGN-FOUNDATION-1",
        "input_state_ref": "OWNER-SEED-1", "related_artifacts": [],
        "status": "WORKING", "authoritative": False,
        "project_id": "project-1", "storage_mode": "DRIVE_THEN_REPO",
        "root_index": "INDEX.md", "provenance": ["OWNER-SEED-1"],
        "namespaces": [
            {"artifact_class": "FINDING", "prefix": "research/findings",
             "scope_key": "workstream_id", "index": "research/findings/INDEX.md"},
            {"artifact_class": "CANON", "prefix": "canon/current",
             "scope_key": None, "index": "canon/current/INDEX.md"},
        ],
    }


class ProjectTopologyTest(unittest.TestCase):
    def assert_code(self, code, fn):
        with self.assertRaises(TopologyError) as raised:
            fn()
        self.assertEqual(raised.exception.code, code)

    def test_bootstrap_is_one_durable_bundle_and_independently_navigable(self):
        with tempfile.TemporaryDirectory() as root:
            writer = LocalFileDurableReferencePort(root, "SOR-1")
            ref = materialize_bootstrap(writer, "SOR-1", plan())
            # A fresh consumer must read the actual durable object from root.
            reader = LocalFileDurableReferencePort(root, "SOR-1")
            state = verify_bootstrap(reader, "SOR-1", ref)
            self.assertEqual(state.index["topology_entry"], "TOPOLOGY_MANIFEST")
            self.assertEqual(state.index["current_canon_ref"], None)
            self.assertIn("INDEX.md", state.shell)
            self.assertEqual(
                resolve_address(state, "FINDING", "finding-1", {"workstream_id": "R-017"}),
                "research/findings/R-017/finding-1",
            )

    def test_no_bare_ref_or_unreadable_bootstrap_can_admit_payload(self):
        with tempfile.TemporaryDirectory() as root:
            port = LocalFileDurableReferencePort(root, "SOR-1")
            self.assert_code("TOPOLOGY_BOOTSTRAP_READBACK_NOT_PROVEN", lambda:
                materialize_project_payload(port, "SOR-1", "dar:v1:" + "0" * 64,
                    "CANON", "current", b"payload"))
            ref = materialize_bootstrap(port, "SOR-1", plan())
            self.assert_code("TOPOLOGY_BOOTSTRAP_READBACK_NOT_PROVEN", lambda:
                materialize_project_payload(port, "SOR-2", ref, "CANON", "current", b"payload"))

    def test_anti_entropy_before_each_payload_write(self):
        with tempfile.TemporaryDirectory() as root:
            port = LocalFileDurableReferencePort(root, "SOR-1")
            ref = materialize_bootstrap(port, "SOR-1", plan())
            value = materialize_project_payload(port, "SOR-1", ref,
                 "FINDING", "F-7", b"result", scope={"workstream_id": "R-017"})
            self.assertEqual(value["canonical_address"], "research/findings/R-017/F-7")
            self.assert_code("TOPOLOGY_ADDRESS_MISMATCH", lambda:
                materialize_project_payload(port, "SOR-1", ref, "FINDING", "F-8",
                    b"result", scope={"workstream_id": "R-017"}, proposed_address="agent-1/F-8"))
            self.assert_code("TOPOLOGY_CHANGE_REQUIRED", lambda:
                materialize_project_payload(port, "SOR-1", ref, "SOURCE", "S-1", b"source"))
            self.assert_code("TOPOLOGY_SCOPE_INVALID", lambda:
                materialize_project_payload(port, "SOR-1", ref, "FINDING", "F-9", b"result"))
            self.assert_code("TOPOLOGY_SEMANTIC_ID_INVALID", lambda:
                materialize_project_payload(port, "SOR-1", ref, "CANON", "../evil", b"bad"))

    def test_plan_disallows_parallel_or_ad_hoc_namespace(self):
        changed = plan()
        changed["namespaces"].append({"artifact_class": "SOURCE",
            "prefix": "research/findings/sub", "index": "research/findings/sub/INDEX.md",
            "scope_key": None})
        self.assert_code("TOPOLOGY_NAMESPACE_COLLISION", lambda: build_bootstrap(changed))
        changed = plan()
        changed["namespaces"][0]["prefix"] = "../out"
        self.assert_code("TOPOLOGY_PATH_INVALID", lambda: build_bootstrap(changed))
        changed = plan()
        changed["authoritative"] = True
        self.assert_code("TOPOLOGY_PLAN_AUTHORITY_INVALID", lambda: build_bootstrap(changed))

    def test_extension_vs_replacement_and_owner_gate(self):
        with tempfile.TemporaryDirectory() as root:
            port = LocalFileDurableReferencePort(root, "SOR-1")
            ref = materialize_bootstrap(port, "SOR-1", plan())
            old = verify_bootstrap(port, "SOR-1", ref)
            extended = plan()
            extended["namespaces"].append({"artifact_class": "SOURCE",
                "prefix": "sources", "index": "sources/INDEX.md", "scope_key": None})
            self.assertEqual(classify_topology_change(old, extended), "TOPOLOGY_EXTENSION")
            replaced = plan()
            replaced["namespaces"][0]["prefix"] = "knowledge/findings"
            replaced["namespaces"][0]["index"] = "knowledge/findings/INDEX.md"
            self.assert_code("TOPOLOGY_REPLACEMENT_OWNER_GATE_REQUIRED", lambda:
                classify_topology_change(old, replaced))
            self.assertEqual(classify_topology_change(old, replaced,
                owner_decision_ref="OWNER-53", replacement_strategy="PRESERVE_MIGRATE",
                migration_readback_proven=True, old_current_retired=True),
                "TOPOLOGY_REPLACEMENT_AUTHORIZED")

    def test_undeclared_current_canon_is_not_invented(self):
        output = build_bootstrap(plan())
        self.assertIsNone(output["index"]["current_canon_ref"])
        self.assertFalse(output["manifest"]["authoritative"])


if __name__ == "__main__":
    unittest.main()
