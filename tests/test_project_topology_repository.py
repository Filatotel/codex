from __future__ import annotations

import tempfile
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tests.test_project_topology import plan
from tools.durable_artifact_port import LocalFileDurableReferencePort
from tools.project_topology import TopologyError, materialize_bootstrap, verify_bootstrap
from tools.project_topology_repository import (
    materialize_repository_shell, verify_repository_shell, materialize_repository_payload, extend_repository_shell, MANIFEST_NAME
)


class RepositoryTopologyShellTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.parent = Path(directory.name)
        self.port = LocalFileDurableReferencePort(self.parent / "durable", "SOR-1")
        self.ref = materialize_bootstrap(self.port, "SOR-1", plan())
        self.admission = verify_bootstrap(self.port, "SOR-1", self.ref)
        self.root = self.parent / "project"

    def test_same_artifact_id_in_distinct_scopes_has_distinct_current_addresses(self):
        materialize_repository_shell(self.root, self.admission)
        for scope, payload in (("R-1", b"first"), ("R-2", b"second")):
            materialize_repository_payload(self.root, self.port, "SOR-1", self.ref,
                "FINDING", "F-1", payload, scope={"workstream_id": scope})
        self.assertEqual((self.root / "research/findings/R-1/F-1").read_bytes(), b"first")
        self.assertEqual((self.root / "research/findings/R-2/F-1").read_bytes(), b"second")
        self.assertEqual(verify_repository_shell(self.root, self.admission)["status"], "COLD_START_PROVEN")

    def test_control_paths_cannot_be_admitted_as_payload_namespaces(self):
        for prefix in ("INDEX.md", MANIFEST_NAME):
            with self.subTest(prefix=prefix):
                value = plan()
                value["namespaces"][0].update(prefix=prefix, index=prefix + "/INDEX.md")
                with self.assertRaises(TopologyError) as raised:
                    ref = materialize_bootstrap(self.port, "SOR-1", value)
                    materialize_repository_shell(self.root, verify_bootstrap(self.port, "SOR-1", ref))
                self.assertEqual(raised.exception.code, "TOPOLOGY_NAMESPACE_COLLISION")
                self.assertFalse(self.root.exists())

    def test_payload_cannot_replace_or_contain_namespace_navigation_index(self):
        value = plan()
        value["namespaces"][0]["index"] = "research/findings/R-1/INDEX.md"
        value["namespaces"][0]["scope_key"] = None
        ref = materialize_bootstrap(self.port, "SOR-1", value)
        admission = verify_bootstrap(self.port, "SOR-1", ref)
        materialize_repository_shell(self.root, admission)
        with self.assertRaises(TopologyError) as raised:
            materialize_repository_payload(self.root, self.port, "SOR-1", ref,
                "FINDING", "R-1", b"blocked")
        self.assertEqual(raised.exception.code, "TOPOLOGY_NAMESPACE_COLLISION")

    def test_interrupted_extension_can_retry_without_losing_existing_payload(self):
        materialize_repository_shell(self.root, self.admission)
        materialize_repository_payload(self.root, self.port, "SOR-1", self.ref,
            "CANON", "draft", b"working canon")
        changed = plan()
        changed["namespaces"].append({"artifact_class": "SOURCE", "prefix": "sources",
            "index": "sources/INDEX.md", "scope_key": None})
        import os
        replace = os.replace
        def fail_carrier(source, target):
            if Path(target) == self.root / MANIFEST_NAME:
                raise OSError("interrupted before current carrier publish")
            return replace(source, target)
        with patch("tools.project_topology_repository.os.replace", side_effect=fail_carrier):
            with self.assertRaises(TopologyError):
                extend_repository_shell(self.root, self.port, "SOR-1", self.ref, changed)
        self.assertEqual(verify_repository_shell(self.root, self.admission)["status"], "COLD_START_PROVEN")
        result = extend_repository_shell(self.root, self.port, "SOR-1", self.ref, changed)
        fresh = verify_bootstrap(self.port, "SOR-1", result["topology_ref"])
        self.assertEqual(verify_repository_shell(self.root, fresh)["status"], "COLD_START_PROVEN")
        self.assertEqual((self.root / "canon/current/draft").read_bytes(), b"working canon")

    def test_authorized_update_preserves_address_and_superseded_durable_ref(self):
        materialize_repository_shell(self.root, self.admission)
        first = materialize_repository_payload(self.root, self.port, "SOR-1", self.ref,
            "CANON", "draft", b"first working draft")
        updated = materialize_repository_payload(self.root, self.port, "SOR-1", self.ref,
            "CANON", "draft", b"revised working draft", expected_artifact_ref=first["artifact_ref"])
        self.assertEqual(updated["canonical_address"], "canon/current/draft")
        self.assertEqual((self.root / "canon/current/draft").read_bytes(), b"revised working draft")
        self.assertEqual(self.port.readback("SOR-1", first["artifact_ref"]).payload, b"first working draft")
        items = json.loads((self.root / "canon/current/INDEX.md").read_text().split("Current entries (JSON):\n")[1])
        self.assertEqual(items[0]["history_refs"], [first["artifact_ref"]])
        self.assertEqual(items[0]["artifact_ref"], updated["artifact_ref"])
        with self.assertRaises(TopologyError) as stale:
            materialize_repository_payload(self.root, self.port, "SOR-1", self.ref,
                "CANON", "draft", b"stale update", expected_artifact_ref=first["artifact_ref"])
        self.assertEqual(stale.exception.code, "PROJECT_PAYLOAD_REF_STALE")
        self.assertEqual(verify_repository_shell(self.root, self.admission)["status"], "COLD_START_PROVEN")

    def test_failed_payload_index_publish_can_retry(self):
        materialize_repository_shell(self.root, self.admission)
        import os
        replace = os.replace
        def fail_index(source, target):
            if Path(target) == self.root / "canon/current/INDEX.md":
                raise OSError("interrupted before namespace publication")
            return replace(source, target)
        with patch("tools.project_topology_repository.os.replace", side_effect=fail_index):
            with self.assertRaises(TopologyError):
                materialize_repository_payload(self.root, self.port, "SOR-1", self.ref,
                    "CANON", "draft", b"working")
        result = materialize_repository_payload(self.root, self.port, "SOR-1", self.ref,
            "CANON", "draft", b"working")
        self.assertEqual(result["physical_readback"], "COLD_START_PROVEN")

    def test_namespace_symlink_cannot_redirect_payload_outside_project(self):
        materialize_repository_shell(self.root, self.admission)
        outside = self.parent / "outside"
        (self.root / "canon/current").rename(outside)
        (self.root / "canon/current").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(TopologyError) as raised:
            materialize_repository_payload(self.root, self.port, "SOR-1", self.ref,
                "CANON", "draft", b"escaped")
        self.assertEqual(raised.exception.code, "TOPOLOGY_PHYSICAL_PATH_INVALID")
        self.assertFalse((outside / "draft").exists())

    def test_preexisting_staging_symlink_cannot_be_followed_during_update(self):
        materialize_repository_shell(self.root, self.admission)
        first = materialize_repository_payload(self.root, self.port, "SOR-1", self.ref,
            "CANON", "draft", b"old")
        outside = self.parent / "valuable"
        outside.write_bytes(b"preserve")
        (self.root / "canon/current/.draft.staged").symlink_to(outside)
        try:
            materialize_repository_payload(self.root, self.port, "SOR-1", self.ref,
                "CANON", "draft", b"new", expected_artifact_ref=first["artifact_ref"])
        except TopologyError:
            pass  # Rejecting the collision or using an owned unique stage is safe.
        self.assertEqual(outside.read_bytes(), b"preserve")
        self.assertFalse((self.root / "canon/current/draft").is_symlink())

    def test_interrupted_update_can_retry_with_exact_prior_reference(self):
        materialize_repository_shell(self.root, self.admission)
        first = materialize_repository_payload(self.root, self.port, "SOR-1", self.ref,
            "CANON", "draft", b"old")
        import os
        replace = os.replace
        def interrupt_index(source, target):
            if Path(target) == self.root / "canon/current/INDEX.md":
                raise KeyboardInterrupt("process interrupted before namespace commit")
            return replace(source, target)
        with patch("tools.project_topology_repository.os.replace", side_effect=interrupt_index):
            with self.assertRaises(KeyboardInterrupt):
                materialize_repository_payload(self.root, self.port, "SOR-1", self.ref,
                    "CANON", "draft", b"new", expected_artifact_ref=first["artifact_ref"])
        with self.assertRaises(TopologyError):
            verify_repository_shell(self.root, self.admission)
        result = materialize_repository_payload(self.root, self.port, "SOR-1", self.ref,
            "CANON", "draft", b"new", expected_artifact_ref=first["artifact_ref"])
        self.assertEqual(result["physical_readback"], "COLD_START_PROVEN")
        self.assertEqual((self.root / "canon/current/draft").read_bytes(), b"new")

    def test_fresh_project_has_real_files_and_independent_cold_start(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            port = LocalFileDurableReferencePort(parent / "durable", "SOR-1")
            ref = materialize_bootstrap(port, "SOR-1", plan())
            admission = verify_bootstrap(LocalFileDurableReferencePort(parent / "durable", "SOR-1"), "SOR-1", ref)
            project_root = parent / "new-project"
            result = materialize_repository_shell(project_root, admission)
            self.assertEqual(result["status"], "COLD_START_PROVEN")
            self.assertTrue((project_root / "INDEX.md").is_file())
            self.assertTrue((project_root / MANIFEST_NAME).is_file())
            self.assertTrue((project_root / "research/findings/INDEX.md").is_file())
            self.assertEqual(verify_repository_shell(project_root, admission), result)

    def test_conflicting_root_does_not_get_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            port = LocalFileDurableReferencePort(parent / "durable", "SOR-1")
            ref = materialize_bootstrap(port, "SOR-1", plan())
            admission = verify_bootstrap(port, "SOR-1", ref)
            root = parent / "project"
            root.mkdir()
            (root / "valuable.txt").write_text("preserve")
            with self.assertRaises(TopologyError) as ctx:
                materialize_repository_shell(root, admission)
            self.assertEqual(ctx.exception.code, "PROJECT_ROOT_ALREADY_EXISTS")
            self.assertEqual((root / "valuable.txt").read_text(), "preserve")

    def test_tampered_namespace_fails_cold_start(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            port = LocalFileDurableReferencePort(parent / "durable", "SOR-1")
            ref = materialize_bootstrap(port, "SOR-1", plan())
            admission = verify_bootstrap(port, "SOR-1", ref)
            root = parent / "project"
            materialize_repository_shell(root, admission)
            (root / "canon/current/INDEX.md").write_text("agent-invented")
            with self.assertRaises(TopologyError) as ctx:
                verify_repository_shell(root, admission)
            self.assertEqual(ctx.exception.code, "COLD_START_NAMESPACE_INVALID")

    def test_payload_updates_physical_namespace_index_and_fresh_consumer_finds_it(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            port = LocalFileDurableReferencePort(parent / "durable", "SOR-1")
            ref = materialize_bootstrap(port, "SOR-1", plan())
            admission = verify_bootstrap(port, "SOR-1", ref)
            root = parent / "project"
            materialize_repository_shell(root, admission)
            value = materialize_repository_payload(root, port, "SOR-1", ref,
                "FINDING", "F-17", b"Finding one", scope={"workstream_id": "R-017"})
            self.assertEqual(value["physical_readback"], "COLD_START_PROVEN")
            self.assertEqual((root / "research/findings/R-017/F-17").read_bytes(), b"Finding one")
            fresh = verify_repository_shell(root, admission)
            self.assertEqual(fresh["status"], "COLD_START_PROVEN")
            with self.assertRaises(TopologyError) as raised:
                materialize_repository_payload(root, port, "SOR-1", ref,
                    "FINDING", "F-17", b"overwrite", scope={"workstream_id": "R-017"})
            self.assertEqual(raised.exception.code, "CANONICAL_ADDRESS_ALREADY_EXISTS")

    def test_stale_current_topology_fails_before_payload_write(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            port = LocalFileDurableReferencePort(parent / "durable", "SOR-1")
            ref = materialize_bootstrap(port, "SOR-1", plan())
            admission = verify_bootstrap(port, "SOR-1", ref)
            root = parent / "project"
            materialize_repository_shell(root, admission)
            pointer = root / MANIFEST_NAME
            pointer.write_text('{"current_topology_ref":"superseded"}')
            with self.assertRaises(TopologyError) as raised:
                materialize_repository_payload(root, port, "SOR-1", ref,
                    "CANON", "current", b"not-written")
            self.assertEqual(raised.exception.code, "TOPOLOGY_CURRENT_REF_STALE")
            self.assertFalse((root / "canon/current/current").exists())

    def test_extension_reuses_stable_current_manifest_without_parallel_topology(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            port = LocalFileDurableReferencePort(parent / "durable", "SOR-1")
            ref = materialize_bootstrap(port, "SOR-1", plan())
            old = verify_bootstrap(port, "SOR-1", ref)
            root = parent / "project"
            materialize_repository_shell(root, old)
            changed = plan()
            changed["namespaces"].append({"artifact_class": "SOURCE",
                "prefix": "sources", "index": "sources/INDEX.md", "scope_key": None})
            result = extend_repository_shell(root, port, "SOR-1", ref, changed)
            self.assertEqual(result["extension_status"], "TOPOLOGY_EXTENSION")
            self.assertTrue((root / "sources/INDEX.md").is_file())
            self.assertFalse((root / "TOPOLOGY_CURRENT.json").exists())
            self.assertFalse((root / "TOPOLOGY_MANIFEST-2.json").exists())
            with self.assertRaises(TopologyError) as stale:
                materialize_repository_payload(root, port, "SOR-1", ref,
                    "CANON", "outdated", b"bad")
            self.assertEqual(stale.exception.code, "TOPOLOGY_CURRENT_REF_STALE")
            fresh = verify_bootstrap(port, "SOR-1", result["topology_ref"])
            self.assertEqual(verify_repository_shell(root, fresh)["status"], "COLD_START_PROVEN")
            value = materialize_repository_payload(root, port, "SOR-1", result["topology_ref"],
                "SOURCE", "S-1", b"source")
            self.assertEqual(value["physical_readback"], "COLD_START_PROVEN")

    def test_replacement_not_silently_treated_as_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            port = LocalFileDurableReferencePort(parent / "durable", "SOR-1")
            ref = materialize_bootstrap(port, "SOR-1", plan())
            old = verify_bootstrap(port, "SOR-1", ref)
            root = parent / "project"
            materialize_repository_shell(root, old)
            changed = plan()
            changed["namespaces"][0]["prefix"] = "new/findings"
            changed["namespaces"][0]["index"] = "new/findings/INDEX.md"
            with self.assertRaises(TopologyError) as blocked:
                extend_repository_shell(root, port, "SOR-1", ref, changed)
            self.assertEqual(blocked.exception.code, "TOPOLOGY_REPLACEMENT_OWNER_GATE_REQUIRED")
            self.assertEqual(verify_repository_shell(root, old)["status"], "COLD_START_PROVEN")

    def test_drive_only_is_not_misreported_as_repository_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            value = plan()
            value["storage_mode"] = "DRIVE_ONLY"
            port = LocalFileDurableReferencePort(parent / "durable", "SOR-1")
            ref = materialize_bootstrap(port, "SOR-1", value)
            admission = verify_bootstrap(port, "SOR-1", ref)
            with self.assertRaises(TopologyError) as ctx:
                materialize_repository_shell(parent / "project", admission)
            self.assertEqual(ctx.exception.code, "REPOSITORY_MODE_NOT_SELECTED")
            self.assertFalse((parent / "project").exists())


if __name__ == "__main__":
    unittest.main()
