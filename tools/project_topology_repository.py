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

from tools.project_topology import (TopologyAdmission, TopologyError, _canonical_bytes,
                                   resolve_address, verify_bootstrap, materialize_project_payload)
from tools.durable_artifact_port import DurableArtifactPort


MANIFEST_NAME = "TOPOLOGY_MANIFEST.json"
CURRENT_NAME = "TOPOLOGY_CURRENT.json"


def _root_index_bytes(admission: TopologyAdmission) -> bytes:
    return (
        "# Project Index\n\n"
        f"Project: {admission.project_id}\n\n"
        f"Topology manifest: {MANIFEST_NAME}\n\n"
        f"Current topology: {CURRENT_NAME}\n\n"
        f"Topology durable ref: {admission.bootstrap_ref}\n\n"
        "Current Canon: NOT_SET (Owner gate not executed)\n\n"
        "Read the topology manifest to navigate semantic namespaces.\n"
    ).encode("utf-8")


def _namespace_index_bytes(entry: dict) -> bytes:
    return (
        f"# {entry['artifact_class']}\n\n"
        f"Namespace: {entry['prefix']}\n\n"
        f"Scope key: {entry['scope_key'] or 'NONE'}\n\n"
        "Current entries (JSON):\n"
        "[]\n"
    ).encode("utf-8")


def _expected_files(admission: TopologyAdmission) -> dict[str, bytes]:
    if admission.manifest.get("storage_mode") not in {"REPO_ONLY", "DRIVE_THEN_REPO"}:
        raise TopologyError("REPOSITORY_MODE_NOT_SELECTED")
    files = {
        admission.manifest["root_index"]: _root_index_bytes(admission),
        MANIFEST_NAME: _canonical_bytes(admission.manifest),
        CURRENT_NAME: _canonical_bytes({
            "project_id": admission.project_id,
            "topology_ref": admission.bootstrap_ref,
            "content_digest": admission.digest,
            "manifest": MANIFEST_NAME,
        }),
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
    current_line = f"Current topology: {CURRENT_NAME}".encode("utf-8")
    if manifest_line not in index_data or current_line not in index_data:
        raise TopologyError("COLD_START_TOPOLOGY_LINK_MISSING")
    try:
        current = json.loads((root / CURRENT_NAME).read_bytes())
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise TopologyError("COLD_START_CURRENT_POINTER_INVALID") from exc
    if current != json.loads(expected[CURRENT_NAME]):
        raise TopologyError("TOPOLOGY_CURRENT_REF_STALE")
    try:
        manifest = json.loads((root / MANIFEST_NAME).read_bytes())
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise TopologyError("COLD_START_MANIFEST_INVALID") from exc
    if manifest != admission.manifest:
        raise TopologyError("COLD_START_MANIFEST_MISMATCH")
    observed_indexes = {}
    for entry in manifest["namespaces"]:
        rel = entry["index"]
        try:
            actual = (root / rel).read_bytes()
        except OSError as exc:
            raise TopologyError("COLD_START_NAMESPACE_MISSING") from exc
        prefix = expected[rel][:-3]  # Preserve the declared navigation contract, replace only [].
        if not actual.startswith(prefix):
            raise TopologyError("COLD_START_NAMESPACE_INVALID")
        try:
            items = json.loads(actual[len(prefix):])
        except (UnicodeDecodeError, ValueError) as exc:
            raise TopologyError("COLD_START_NAMESPACE_INVALID") from exc
        if not isinstance(items, list):
            raise TopologyError("COLD_START_NAMESPACE_INVALID")
        seen = set()
        for item in items:
            if not isinstance(item, dict) or set(item) != {"artifact_id", "scope", "canonical_address", "digest", "artifact_ref"}:
                raise TopologyError("COLD_START_NAMESPACE_INVALID")
            if item["artifact_id"] in seen:
                raise TopologyError("COLD_START_NAMESPACE_INVALID")
            seen.add(item["artifact_id"])
            scope = {} if entry["scope_key"] is None else {entry["scope_key"]: item["scope"]}
            try:
                address = resolve_address(admission, entry["artifact_class"], item["artifact_id"], scope)
            except TopologyError as exc:
                raise TopologyError("COLD_START_NAMESPACE_INVALID") from exc
            if address != item["canonical_address"]:
                raise TopologyError("COLD_START_NAMESPACE_INVALID")
            try:
                payload = (root / address).read_bytes()
            except OSError as exc:
                raise TopologyError("COLD_START_PAYLOAD_MISSING") from exc
            if hashlib.sha256(payload).hexdigest() != item["digest"]:
                raise TopologyError("COLD_START_PAYLOAD_DIGEST_MISMATCH")
            if not isinstance(item["artifact_ref"], str) or not item["artifact_ref"].strip():
                raise TopologyError("COLD_START_NAMESPACE_INVALID")
        observed_indexes[rel] = actual
    digest = hashlib.sha256(b"".join(
        rel.encode("utf-8") + b"\x00" + (observed_indexes.get(rel) or expected[rel])
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


def materialize_repository_payload(
    root: str | Path,
    port: DurableArtifactPort,
    system_of_record_ref: str,
    bootstrap_ref: str,
    artifact_class: str,
    artifact_id: str,
    payload: bytes,
    *,
    scope: dict[str, str] | None = None,
) -> dict:
    """Materialize one project payload at its admitted physical semantic address.

    Existing canonical carriers are never overwritten by this create-only path.
    A separately authorized update-in-place operation is required for mutations.
    The namespace index is the final visibility boundary: unindexed staged bytes
    cannot be mistaken for a current, cold-start navigable project result.
    """
    admission = verify_bootstrap(port, system_of_record_ref, bootstrap_ref)
    root = Path(root)
    verify_repository_shell(root, admission)  # proves this *current* topology pointer
    address = resolve_address(admission, artifact_class, artifact_id, scope)
    target = root / address
    if target.exists() or target.is_symlink():
        raise TopologyError("CANONICAL_ADDRESS_ALREADY_EXISTS")
    entry = next(e for e in admission.manifest["namespaces"] if e["artifact_class"] == artifact_class)
    index_path = root / entry["index"]
    prefix = _namespace_index_bytes(entry)[:-3]
    index_bytes = index_path.read_bytes()
    items = json.loads(index_bytes[len(prefix):])
    if any(item["artifact_id"] == artifact_id for item in items):
        raise TopologyError("CANONICAL_ADDRESS_ALREADY_EXISTS")
    # Use the existing system-of-record durable port, not a new artifact manager.
    materialized = materialize_project_payload(
        port, system_of_record_ref, bootstrap_ref,
        artifact_class, artifact_id, payload, scope=scope,
    )
    item = {
        "artifact_id": artifact_id,
        "scope": None if entry["scope_key"] is None else scope[entry["scope_key"]],
        "canonical_address": address,
        "digest": hashlib.sha256(payload).hexdigest(),
        "artifact_ref": materialized["artifact_ref"],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name("." + target.name + ".staged")
    index_temporary = index_path.with_name("." + index_path.name + ".staged")
    try:
        with temporary.open("xb") as out:
            out.write(payload)
        # Publish the physical content first, then the index.
        os.replace(temporary, target)
        with index_temporary.open("xb") as out:
            out.write(prefix + json.dumps(items + [item], sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")
        os.replace(index_temporary, index_path)
    except OSError as exc:
        raise TopologyError("REPOSITORY_PAYLOAD_WRITE_FAILED") from exc
    finally:
        temporary.unlink(missing_ok=True)
        index_temporary.unlink(missing_ok=True)
    readback = verify_repository_shell(root, admission)
    return {**materialized, "physical_readback": readback["status"],
            "physical_digest": readback["physical_digest"]}
