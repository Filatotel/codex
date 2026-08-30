#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROOT_REQUIRED = [
    "AGENTS.md",
    "README.md",
    "SYSTEM_MANIFEST.yaml",
    "ROUTER.md",
    "ARCHITECTURE_MIGRATION_MAP.md",
]

ROLE_REQUIRED_SECTIONS = [
    "## PURPOSE",
    "## RESPONSIBILITY",
    "## AUTHORITY",
    "## DOES_NOT_OWN",
    "## CONTEXT CONTRACT",
    "## REQUIRED INPUTS",
    "## OPTIONAL INPUTS",
    "## FORBIDDEN / UNNECESSARY CONTEXT",
    "## PROCEDURE",
    "## ARTIFACT POLICY",
    "## OUTPUTS",
    "## HANDOFF",
    "## STOP / ESCALATION",
    "## FAILURE MODES",
]

ACTIVE_SKILL_NAMESPACES = [
    ROOT / "kernel/skills",
    ROOT / "protocols/skills",
    ROOT / "engines/verification/skills",
    ROOT / "engines/production/software/skills",
    ROOT / "engines/production/software/patterns",
    ROOT / "library/skills",
]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def manifest_path_values(text: str) -> set[str]:
    # Extract repository-relative md/yaml/json paths from simple Wave-1 YAML manifests.
    return set(re.findall(r"(?:^|\s)([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.(?:md|yaml|json))\s*$", text, flags=re.MULTILINE))


def validate() -> list[str]:
    errors: list[str] = []

    for rel in ROOT_REQUIRED:
        if not (ROOT / rel).is_file():
            fail(errors, f"missing root control file: {rel}")

    # Old global runtime discovery surfaces must be gone from the active root.
    for rel in [".agents", ".codex", "SKILLS_INDEX.md"]:
        if (ROOT / rel).exists():
            fail(errors, f"legacy ordinary runtime surface still active at root: {rel}")

    system_manifest = (ROOT / "SYSTEM_MANIFEST.yaml").read_text(encoding="utf-8")
    for rel in re.findall(r"manifest_path:\s*([^\s]+)", system_manifest):
        if not (ROOT / rel).is_file():
            fail(errors, f"root manifest references missing engine manifest: {rel}")

    if "global_skill_discovery: forbidden_during_ordinary_execution" not in system_manifest:
        fail(errors, "root manifest does not explicitly forbid ordinary global skill discovery")

    router = (ROOT / "ROUTER.md").read_text(encoding="utf-8")
    for forbidden in [".agents/skills", "archive/legacy-codex/SKILLS_INDEX.md"]:
        if forbidden in router:
            fail(errors, f"router points to forbidden global/legacy discovery surface: {forbidden}")

    engine_manifests = [
        ROOT / "engines/production/software/MANIFEST.yaml",
        ROOT / "engines/verification/MANIFEST.yaml",
    ]
    for manifest in engine_manifests:
        if not manifest.is_file():
            fail(errors, f"missing engine manifest: {manifest.relative_to(ROOT)}")
            continue
        text = manifest.read_text(encoding="utf-8")
        for rel in manifest_path_values(text):
            if not (ROOT / rel).exists():
                fail(errors, f"{manifest.relative_to(ROOT)} references missing path: {rel}")

    role_paths = [
        ROOT / "roles/control-director/ROLE.md",
        ROOT / "roles/control-verifier/ROLE.md",
        ROOT / "roles/executor/ROLE.md",
        ROOT / "roles/owner-interface/ROLE.md",
    ]
    for role in role_paths:
        if not role.is_file():
            fail(errors, f"missing role contract: {role.relative_to(ROOT)}")
            continue
        text = role.read_text(encoding="utf-8")
        for section in ROLE_REQUIRED_SECTIONS:
            if section not in text:
                fail(errors, f"{role.relative_to(ROOT)} missing section {section}")

    director = (ROOT / "roles/control-director/ROLE.md").read_text(encoding="utf-8")
    if "EXECUTOR_RESULT" not in director or "VERIFICATION_RESULT" not in director:
        fail(errors, "Control Director contract does not explicitly consume both role-native results")
    for state in ["ASSIGN", "WAIT", "ESCALATE", "COMPLETE"]:
        if state not in director:
            fail(errors, f"Control Director missing terminal control state: {state}")

    owner = (ROOT / "roles/owner-interface/ROLE.md").read_text(encoding="utf-8")
    if "OWNER_DECISION_RECORD" not in owner:
        fail(errors, "Owner Interface does not materialize durable Owner decisions")

    for schema in sorted((ROOT / "schemas").glob("*.schema.json")):
        try:
            json.loads(schema.read_text(encoding="utf-8"))
        except Exception as exc:  # deterministic syntax gate, no external validator dependency
            fail(errors, f"invalid JSON schema syntax {schema.relative_to(ROOT)}: {exc}")
    if len(list((ROOT / "schemas").glob("*.schema.json"))) < 5:
        fail(errors, "fewer than five required role-native schemas are materialized")

    seen: dict[str, str] = {}
    for namespace in ACTIVE_SKILL_NAMESPACES:
        if not namespace.is_dir():
            fail(errors, f"missing active skill namespace: {namespace.relative_to(ROOT)}")
            continue
        for child in sorted(p for p in namespace.iterdir() if p.is_dir()):
            skill_id = child.name
            prior = seen.get(skill_id)
            if prior:
                fail(errors, f"duplicate active skill id {skill_id}: {prior} and {child.relative_to(ROOT)}")
            else:
                seen[skill_id] = str(child.relative_to(ROOT))
            if not (child / "SKILL.md").is_file():
                fail(errors, f"skill directory has no SKILL.md: {child.relative_to(ROOT)}")

    patterns = ROOT / "engines/production/software/patterns"
    if patterns.is_dir():
        for pattern in sorted(p for p in patterns.iterdir() if p.is_dir()):
            text = (pattern / "SKILL.md").read_text(encoding="utf-8").lower()
            if "solution pattern" not in text or "optional" not in text:
                fail(errors, f"pattern lost optional Solution Pattern classification: {pattern.name}")

    software_index = ROOT / "engines/production/software/SKILLS_INDEX.md"
    if not software_index.is_file():
        fail(errors, "missing engine-local Software skill index")

    legacy_factory = ROOT / "archive/legacy-codex/LOCALFLOW_FACTORY.md"
    if not legacy_factory.is_file():
        fail(errors, "legacy LOCALFLOW_FACTORY.md was not preserved in archive")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Project Resolver structural validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Project Resolver structural validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
