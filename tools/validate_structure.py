#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]

ROOT_REQUIRED = [
    "AGENTS.md",
    "README.md",
    "SYSTEM_MANIFEST.yaml",
    "ROUTER.md",
    "ARCHITECTURE_MIGRATION_MAP.md",
    "kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md",
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

RESEARCH_ENFORCEMENT_SURFACES = [
    "kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md",
    "engines/research/MANIFEST.yaml",
    "engines/research/RESEARCH_CONTROL_CONTRACT.md",
    "engines/research/ROLES.md",
    "engines/research/workflows/default-machine-research.md",
    "engines/research/bootstrap/DEFAULT_MACHINE_ONLY_BOOTSTRAP.yaml",
    "engines/research/templates/research-question.yaml",
    "engines/research/templates/research-work-package.yaml",
    "engines/research/templates/machine-experiment.yaml",
    "schemas/research-question.schema.json",
    "schemas/research-work-package.schema.json",
    "schemas/research-source.schema.json",
    "schemas/machine-experiment.schema.json",
    "schemas/research-method-freeze.schema.json",
    "schemas/human-research-authorization.schema.json",
    "schemas/owner-decision-record.schema.json",
    "tools/research_policy.py",
    "tools/validate_structure.py",
    "tests/test_research_machine_only.py",
    "tests/test_structure.py",
]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def manifest_path_values(text: str) -> set[str]:
    # Extract repository-relative md/yaml/json/py paths from simple manifests.
    return set(re.findall(r"(?:^|\s)([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.(?:md|yaml|json|py))\s*$", text, flags=re.MULTILINE))


def _load_schema(root: Path, rel: str) -> dict:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def validate_research_machine_only_gate(
    root: Path = ROOT,
    regression_runner: Callable[[], list[str]] | None = None,
) -> list[str]:
    """Normal bounded Research gate: active-surface lint + deterministic policy regressions."""
    errors: list[str] = []
    try:
        import sys
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from tools.research_policy import lint_active_repository, run_machine_only_regressions

        for err in lint_active_repository(root):
            fail(errors, f"research machine-only policy: {err}")
        runner = regression_runner or run_machine_only_regressions
        for err in runner():
            fail(errors, f"research machine-only regression: {err}")
    except Exception as exc:
        fail(errors, f"research machine-only policy/regression validator unavailable: {exc}")
    return errors


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
    if "research_machine_only: kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md" not in system_manifest:
        fail(errors, "root manifest does not register the machine-only Research constitution")
    if "engine_id: research" not in system_manifest or "status: available" not in system_manifest:
        fail(errors, "Research Engine is not materialized as an available engine")

    router = (ROOT / "ROUTER.md").read_text(encoding="utf-8")
    for forbidden in [".agents/skills", "archive/legacy-codex/SKILLS_INDEX.md"]:
        if forbidden in router:
            fail(errors, f"router points to forbidden global/legacy discovery surface: {forbidden}")
    if "kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md" not in router:
        fail(errors, "router does not apply Research machine-only constitutional precedence")

    engine_manifests = [
        ROOT / "engines/production/software/MANIFEST.yaml",
        ROOT / "engines/verification/MANIFEST.yaml",
        ROOT / "engines/research/MANIFEST.yaml",
    ]
    for manifest in engine_manifests:
        if not manifest.is_file():
            fail(errors, f"missing engine manifest: {manifest.relative_to(ROOT)}")
            continue
        text = manifest.read_text(encoding="utf-8")
        for rel in manifest_path_values(text):
            if not (ROOT / rel).exists():
                fail(errors, f"{manifest.relative_to(ROOT)} references missing path: {rel}")

    research_manifest = (ROOT / "engines/research/MANIFEST.yaml").read_text(encoding="utf-8")
    for required in [
        "default_research_mode: MACHINE_ONLY",
        "constitutional_authority: kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md",
        "third_party_human_research: true",
        "owner_manual_research_labor: true",
        "reachable_from_default_workflow: false",
        "question: validate_question",
        "work_package: validate_work_package",
        "source: validate_source",
        "experiment: validate_experiment",
        "method_freeze: validate_method_freeze",
        "separate_human_research_authorization: validate_human_research_authorization",
        "structural_regression_gate: tools/validate_structure.py",
    ]:
        if required not in research_manifest:
            fail(errors, f"Research manifest missing machine-only control: {required}")

    for rel in RESEARCH_ENFORCEMENT_SURFACES:
        if not (ROOT / rel).is_file():
            fail(errors, f"missing active Research enforcement surface: {rel}")

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
        except Exception as exc:
            fail(errors, f"invalid JSON schema syntax {schema.relative_to(ROOT)}: {exc}")

    required_research_schemas = [
        "schemas/research-question.schema.json",
        "schemas/research-work-package.schema.json",
        "schemas/machine-experiment.schema.json",
        "schemas/research-method-freeze.schema.json",
        "schemas/research-source.schema.json",
        "schemas/human-research-authorization.schema.json",
        "schemas/owner-decision-record.schema.json",
    ]
    for rel in required_research_schemas:
        if not (ROOT / rel).is_file():
            fail(errors, f"missing Research Engine schema: {rel}")

    if len(list((ROOT / "schemas").glob("*.schema.json"))) < 5:
        fail(errors, "fewer than five required role-native schemas are materialized")

    # Schema/validator closure and required-field contracts must not drift apart.
    try:
        import sys
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from tools.research_policy import (
            HUMAN_AUTH_FIELDS,
            MACHINE_EXPERIMENT_REQUIRED,
            METHOD_FREEZE_REQUIRED,
            QUESTION_REQUIRED_FIELDS,
            SOURCE_REQUIRED_FIELDS,
            WORK_PACKAGE_REQUIRED_FIELDS,
        )
        schema_contracts = [
            ("schemas/research-question.schema.json", QUESTION_REQUIRED_FIELDS),
            ("schemas/research-work-package.schema.json", WORK_PACKAGE_REQUIRED_FIELDS),
            ("schemas/research-source.schema.json", SOURCE_REQUIRED_FIELDS),
            ("schemas/machine-experiment.schema.json", MACHINE_EXPERIMENT_REQUIRED),
            ("schemas/research-method-freeze.schema.json", METHOD_FREEZE_REQUIRED),
            ("schemas/human-research-authorization.schema.json", HUMAN_AUTH_FIELDS),
        ]
        for rel, policy_required in schema_contracts:
            schema = _load_schema(ROOT, rel)
            if schema.get("additionalProperties") is not False:
                fail(errors, f"Research schema is not closed: {rel}")
            schema_required = set(schema.get("required", []))
            if schema_required != set(policy_required):
                fail(errors, f"schema/policy required-field drift: {rel}")
    except Exception as exc:
        fail(errors, f"Research schema/policy contract comparison unavailable: {exc}")

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

    errors.extend(validate_research_machine_only_gate(ROOT))
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
