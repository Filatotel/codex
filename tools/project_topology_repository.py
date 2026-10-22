"""Repository-backed physical realization of an admitted project topology.

Reference implementation for a fresh repository/project root. Uses one staged
directory publish; it does not replace the generic #56 durable port and does
not give Foundation permission to alter an existing project filesystem.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from tools.project_topology import TopologyAdmission, TopologyError, _canonical_bytes


MANIFEST_NAME = "TOPOLOGY_MANIFEST.json"


def _root_index_bytes(admission: TopologyAdmission) -> bytes:
    return (
        "# Project Index\n\n"
        f"Project: {admission.project_id}\n\n"
        f"Topology manifest: {MANIFEST_NAME}\n\n"
        f"Topology durable ref: {admission.bootstrap_ref}\n\n"
        "Current Canon: NOT_SET (Owner gate not executed)\n\n"
        "Read the topology manifest to navigate semantic namespaces.\n"
    ).encode("utf-8")


def _namespace_index_bytes(entry: dict) -> bytes:
    return (
        f"# {entry['artifact_class']}\n\n"
        f"Namespace: {entry['prefix']}\n\n"
        f"Scope key: {entry['scope_key'] or 'NONE'}\n\n"
        "Current result: NOT_SET\n\n"
        "History: NOT_SET\n"
    ).encode("utf-8")


def _expected_files(admission: TopologyAdmission) -> dict[str, bytes]:
    if admission.manifest.get("storage_mode") not in {"REPO_ONLY", "DRIVE_THEN_REPO"}:
        raise TopologyError("REPOSITORY_MODE_NOT_SELECTED")
    files = {
        admission.manifest["root_index"]: _root_index_bytes(admission),
        MANIFEST_NAME: _canonical_bytes(admission.manifest),
    }
    for entry in admission.manifest["namespaces"]:
        path = entry["index"]
        if path in files:
            raise TopologyError("TOPOLOGY_NAMESPACE_COLLISION")
        files[path] = _namespace_index_bytes(entry)
    return files


def materialize_repository_shell(root: str | Path, admission: TopologyAdmission) -> dict:
    """Publish a *new* project root atomically; never silently rewrite an old root.

    All namespace indexes and manifest exist in the staged tree before the
    single root rename. A failed staging operation cannot admit a partial root.
    """
    root = Path(root)
    if root.exists() or root.is_symlink():
        raise TopologyError("PROJECT_ROOT_ALREADY_EXISTS")
    if not root.parent.is_dir():
        raise TopologyError("PROJECT_ROOT_PARENT_MISSING")
    files = _expected_files(admission)
    staged: Path | None = None
    try:
        staged = Path(tempfile.mkdtemp(prefix=".foundation-topology-", dir=root.parent))
        for rel, payload in files.items():
            dest = staged / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(payload)
        # Validate the actual staged files before the commit boundary.
        _verify_repository_files(staged, admission)
        if root.exists() or root.is_symlink():
            raise TopologyError("PROJECT_ROOT_ALREADY_EXISTS")
        os.replace(staged, root)
        staged = None
    except (OSError, ValueError) as exc:
        if isinstance(exc, TopologyError):
            raise
        raise TopologyError("REPOSITORY_SHELL_WRITE_FAILED") from exc
    finally:
        if staged is not None:
            shutil.rmtree(staged, ignore_errors=True)
    # Fresh consumer reads published files, not the writer's staged copy.
    return verify_repository_shell(root, admission)


def _verify_repository_files(root: Path, admission: TopologyAdmission) -> dict:
    expected = _expected_files(admission)
    # Cold consumer starts at the declared root entrypoint, not directory enumeration.
    index_path = root / admission.manifest["root_index"]
    try:
        index_data = index_path.read_bytes()
    except OSError as exc:
        raise TopologyError("COLD_START_ROOT_INDEX_MISSING") from exc
    if index_data != expected[admission.manifest["root_index"]]:
        raise TopologyError("COLD_START_ROOT_INDEX_INVALID")
    manifest_line = f"Topology manifest: {MANIFEST_NAME}".encode("utf-8")
    if manifest_line not in index_data:
        raise TopologyError("COLD_START_TOPOLOGY_LINK_MISSING")
    try:
        manifest = json.loads((root / MANIFEST_NAME).read_bytes())
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise TopologyError("COLD_START_MANIFEST_INVALID") from exc
    if manifest != admission.manifest:
        raise TopologyError("COLD_START_MANIFEST_MISMATCH")
    for entry in manifest["namespaces"]:
        rel = entry["index"]
        try:
            actual = (root / rel).read_bytes()
        except OSError as exc:
            raise TopologyError("COLD_START_NAMESPACE_MISSING") from exc
        if actual != expected[rel]:
            raise TopologyError("COLD_START_NAMESPACE_INVALID")
    digest = hashlib.sha256(b"".join(
        rel.encode("utf-8") + b"\x00" + expected[rel]
        for rel in sorted(expected)
    )).hexdigest()
    return {"project_id": admission.project_id,
            "topology_ref": admission.bootstrap_ref,
            "root_index": admission.manifest["root_index"],
            "manifest": MANIFEST_NAME,
            "verified_paths": sorted(expected),
            "physical_digest": digest,
            "status": "COLD_START_PROVEN"}


def verify_repository_shell(root: str | Path, admission: TopologyAdmission) -> dict:
    """Independent durable file readback from an already-published project root."""
    root = Path(root)
    if not root.is_dir():
        raise TopologyError("PROJECT_ROOT_UNRESOLVED")
    return _verify_repository_files(root, admission)
