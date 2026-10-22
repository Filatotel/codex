from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tests.test_project_topology import plan
from tools.durable_artifact_port import LocalFileDurableReferencePort
from tools.project_topology import TopologyError, materialize_bootstrap, verify_bootstrap
from tools.project_topology_repository import (
    materialize_repository_shell, verify_repository_shell, materialize_repository_payload, MANIFEST_NAME, CURRENT_NAME
)


class RepositoryTopologyShellTest(unittest.TestCase):
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
            pointer = root / CURRENT_NAME
            pointer.write_text('{"topology_ref":"superseded"}')
            with self.assertRaises(TopologyError) as raised:
                materialize_repository_payload(root, port, "SOR-1", ref,
                    "CANON", "current", b"not-written")
            self.assertEqual(raised.exception.code, "TOPOLOGY_CURRENT_REF_STALE")
            self.assertFalse((root / "canon/current/current").exists())

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
