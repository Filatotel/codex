#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_REQUIRED_TRUE = {
    "MACHINE_EXECUTABLE",
    "CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS",
    "OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS",
}
DEFAULT_REQUIRED_FALSE = {
    "REQUIRES_THIRD_PARTY_HUMAN",
    "REQUIRES_OWNER_MANUAL_RESEARCH",
    "REQUIRES_EXTERNAL_HUMAN_REVIEW",
    "REQUIRES_HUMAN_DATA_COLLECTION",
}
WP_REQUIRED_FALSE = DEFAULT_REQUIRED_FALSE | {"REQUIRES_EXTERNAL_REVIEWER", "REQUIRES_NEW_HUMAN_DATA"}

AMBIGUOUS_OWNER_TERMS = (
    "human gate", "human scope gate", "human research pass", "human pass",
    "human review", "human validation", "human approval", "human decision",
)
ACTIVE_PATTERNS = (
    r"\brecruit(?:ment|ing|ed)?\b",
    r"\bsurvey(?:ing|ed)?\b",
    r"\binterview(?:ing|ed|s)?\b",
    r"\bfocus[\s-]?group(?:s)?\b",
    r"\bnative[\s-]?speaker(?:s)?\b",
    r"\bexternal[\s-]?reviewer(?:s)?\b",
    r"\bexpert[\s-]?(?:reviewer|review|consultation|consult)(?:s|ed|ing)?\b",
    r"\bhuman[\s-]?(?:annotator|rater|reviewer|coder|participant|subject)(?:s)?\b",
    r"\bparticipant(?:s| cohort)?\b",
    r"\brespondent(?:s)?\b",
    r"\bconsent\b",
    r"\bfieldwork\b",
    r"\bcrowdsourc(?:e|ed|ing)\b",
    r"\bstakeholder[\s-]?interview(?:s)?\b",
    r"\buser[\s-]?testing\b",
    r"\busability[\s-]?participant(?:s)?\b",
    r"\bhuman[\s-]?in[\s-]?the[\s-]?loop\b",
    r"\bstakeholder[\s-]?(?:validation|review|consultation)\b",
    r"\bcommunity[\s-]?(?:review|validation|consultation|liaison)\b",
    r"\bcollection[\s-]?surface\b",
    r"\bperformer[\s-]?(?:review|rating|panel)\b",
    r"\brapper[\s-]?rating(?:s)?\b",
    r"\bpanel[\s-]?(?:review|rating|member|coordinator)\b",
    r"\bask\s+(?:an?\s+|[0-9]+\s+)?(?:expert|speaker|listener|participant|respondent)",
    r"\bhave\s+(?:humans?|experts?|speakers?|listeners?)\s+(?:check|review|rate|validate|annotate)",
    r"\bget\s+(?:community|expert|speaker|listener)\s+feedback\b",
    r"\btest\s+(?:this|it|the\s+\w+)?\s*with\s+(?:listeners?|speakers?|users?|participants?)\b",
    r"\bfind\s+(?:several\s+|[0-9]+\s+)?(?:speakers?|participants?|experts?|listeners?)\b",
    r"\bowner(?:/k0)?\b.{0,60}\b(?:manually\s+)?collect\b.{0,40}\b(?:urls?|sources?|data|responses?)\b",
    r"\bowner(?:/k0)?\b.{0,60}\bsearch\b.{0,40}\b(?:sources?|web|literature)\b",
    r"\bowner(?:/k0)?\b.{0,60}\b(?:annotate|code|rate)\b.{0,40}\b(?:dataset|items?|responses?|samples?)\b",
)

STATIC_SOURCE_CUES = (
    "published study", "published paper", "archived interview", "recorded speech corpus",
    "existing survey", "externally conducted survey", "survey respondents", "public dataset",
    "existing human annotation", "existing expert judgment", "pre-existing", "preexisting",
    "external pre-existing", "external_preexisting_human_data", "historical corpus",
)
HISTORICAL_CUES = ("historical", "legacy", "archived", "preserved lineage", "retired compatibility")
PROHIBITION_CUES = ("prohibited", "forbidden", "must not", "do not ", "no third-party", "default deny", "default-deny", "there is no", "cannot", "never", "invalid", "not allowed", "must be zero", "are all zero", "requirements are all zero")
OWNER_CUES = ("owner/k0", "owner ", "owner_", "owner chooses", "owner accepts", "owner rejects", "owner adjudicat")
OWNER_DECISION_CUES = ("choose", "chooses", "accept", "reject", "defer", "decision", "adjudicat", "gate")
SIMULATED_HUMAN_OVERCLAIM = (
    r"\b(?:llm|model|simulat(?:ed|ion)|synthetic)\b.{0,80}\bhuman responses?\b",
    r"\bhuman responses?\b.{0,80}\b(?:llm|model|simulat(?:ed|ion)|synthetic)\b",
)

ALLOWED_OUTCOMES = {
    "EXTERNAL_PREEXISTING_EVIDENCE", "CORPUS_PROXY", "COMPUTATIONAL_PROXY", "MODEL_PROXY",
    "MULTI_MODEL_PROXY", "SIMULATION", "STRUCTURAL_ANALYSIS", "TYPOLOGICAL_ANALYSIS",
    "SENSITIVITY_ANALYSIS", "UNKNOWN", "INSUFFICIENT_PUBLIC_EVIDENCE",
    "UNMEASURED_HUMAN_CONSTRUCT", "OWNER_JUDGMENT_REQUIRED", "PROXY_ONLY",
}

@dataclass(frozen=True)
class Finding:
    classification: str
    message: str

def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()

def classify_text(text: str) -> list[Finding]:
    """Classify human-related language. Only ACTIVE_DEPENDENCY and terminology/overclaim findings fail."""
    t = _norm(text)
    findings: list[Finding] = []

    for pattern in SIMULATED_HUMAN_OVERCLAIM:
        if re.search(pattern, t, flags=re.I | re.S):
            findings.append(Finding("PROXY_OVERCLAIM", "machine/simulated output is labeled as human responses"))

    explicit_prohibition = any(cue in t for cue in PROHIBITION_CUES)

    for term in AMBIGUOUS_OWNER_TERMS:
        if term in t and not explicit_prohibition:
            findings.append(Finding("AMBIGUOUS_HUMAN_GATE_TERMINOLOGY", f"generic authority term: {term}"))

    active_match = any(re.search(p, t, flags=re.I) for p in ACTIVE_PATTERNS)
    if not active_match:
        if any(cue in t for cue in OWNER_CUES) and any(cue in t for cue in OWNER_DECISION_CUES):
            findings.append(Finding("OWNER_AUTHORITY", "explicit Owner/K0 project authority"))
        return findings

    # Explicit denials and constitutional examples may mention forbidden methods without creating a path.
    if explicit_prohibition:
        findings.append(Finding("EXPLICIT_PROHIBITION", "human dependency appears only in a prohibition"))
        return findings

    # Static, already-existing external evidence is source provenance, not a project actor.
    if any(cue in t for cue in STATIC_SOURCE_CUES):
        findings.append(Finding("STATIC_EXTERNAL_SOURCE", "pre-existing human-derived evidence"))
        return findings

    # Retired/archived lineage is preserved but cannot become an active path.
    if any(cue in t for cue in HISTORICAL_CUES) and not re.search(r"\b(?:run|execute|resume|deploy|start|recruit|collect)\b", t):
        findings.append(Finding("HISTORICAL_REFERENCE", "historical/legacy reference"))
        return findings

    # OWNER-only decision language does not turn the Owner into research labor.
    if any(cue in t for cue in OWNER_CUES) and any(cue in t for cue in OWNER_DECISION_CUES):
        labor_terms = ("collect", "annotat", "search sources", "find urls", "survey", "interview", "rate ", "review dataset")
        if not any(term in t for term in labor_terms):
            findings.append(Finding("OWNER_AUTHORITY", "Owner/K0 authority, not research labor"))
            return findings

    findings.append(Finding("ACTIVE_DEPENDENCY", "active non-owner human research dependency"))
    return findings

def _require_fields(obj: dict[str, Any], fields: Iterable[str]) -> list[str]:
    return [f"missing required field: {name}" for name in fields if name not in obj]

def _validate_default_flags(obj: dict[str, Any], false_fields: set[str]) -> list[str]:
    errors: list[str] = []
    errors.extend(_require_fields(obj, DEFAULT_REQUIRED_TRUE | false_fields))
    for name in DEFAULT_REQUIRED_TRUE:
        if obj.get(name) is not True:
            errors.append(f"{name} must be true")
    for name in false_fields:
        if obj.get(name) is not False:
            errors.append(f"{name} must be false")
    return errors

def validate_question(obj: dict[str, Any]) -> list[str]:
    required = {
        "QUESTION_ID","QUESTION","TARGET_CONSTRUCT","AVAILABLE_MACHINE_METHODS",
        "AVAILABLE_EXTERNAL_PREEXISTING_EVIDENCE","REQUIRES_THIRD_PARTY_HUMAN",
        "REQUIRES_OWNER_MANUAL_RESEARCH","REQUIRES_HUMAN_DATA_COLLECTION",
        "REQUIRES_EXTERNAL_HUMAN_REVIEW","DIRECT_MEASUREMENT_POSSIBLE",
        "PROXY_MEASUREMENT_POSSIBLE","EXPECTED_LIMITATION","OWNER_DECISION_COMPONENT",
        "ADMISSION_STATUS",
    }
    errors = _require_fields(obj, required)
    errors += _validate_default_flags(obj, DEFAULT_REQUIRED_FALSE)
    if not obj.get("AVAILABLE_MACHINE_METHODS"):
        errors.append("AVAILABLE_MACHINE_METHODS must be non-empty")
    if obj.get("ADMISSION_STATUS") != "ADMITTED_MACHINE_RESEARCH":
        errors.append("ADMISSION_STATUS must be ADMITTED_MACHINE_RESEARCH for default execution")
    for k in ("QUESTION","TARGET_CONSTRUCT","EXPECTED_LIMITATION"):
        for finding in classify_text(str(obj.get(k, ""))):
            if finding.classification in {"ACTIVE_DEPENDENCY","PROXY_OVERCLAIM","AMBIGUOUS_HUMAN_GATE_TERMINOLOGY"}:
                errors.append(f"{finding.classification}: {finding.message}")
    return sorted(set(errors))

def validate_work_package(obj: dict[str, Any]) -> list[str]:
    required = {
        "WORK_PACKAGE_ID","QUESTION_ID","NAMESPACE","EXECUTOR_ROLE","VERIFIER_ROLE","EXECUTION_SURFACE","SOURCE_ACCESS_METHOD",
        "COMPUTATION_METHOD","VERIFICATION_METHOD","LIMITATIONS","PROHIBITED_OVERCLAIMS","OWNER_GATE_IF_ANY",
    }
    errors = _require_fields(obj, required)
    errors += _validate_default_flags(obj, WP_REQUIRED_FALSE)
    if str(obj.get("NAMESPACE","")).startswith("human-research/"):
        errors.append("default Research Engine cannot admit human-research namespace")
    if obj.get("EXECUTOR_ROLE") not in {
        "AI_R_MASTER","AI_EVIDENCE_EXTRACTOR","AI_SYNTHESIS_AGENT","AI_R_REPAIR",
        "AI_ADVERSARIAL_VALIDATOR","AI_RESEARCH_RELEASE_CONTROLLER"
    }:
        errors.append("EXECUTOR_ROLE must be an allowed AI Research Engine role")
    if obj.get("VERIFIER_ROLE") != "AI_R_VERIFIER":
        errors.append("VERIFIER_ROLE must be AI_R_VERIFIER")
    gate = obj.get("OWNER_GATE_IF_ANY")
    if gate is not None and not re.fullmatch(r"OWNER_[A-Z0-9_]+", str(gate)):
        errors.append("OWNER_GATE_IF_ANY must be null or explicit OWNER_* authority term")
    text_fields = ("EXECUTION_SURFACE","SOURCE_ACCESS_METHOD","COMPUTATION_METHOD","VERIFICATION_METHOD",
                   "LIMITATIONS","PROHIBITED_OVERCLAIMS","OWNER_GATE_IF_ANY")
    for k in text_fields:
        value = obj.get(k, "")
        values = value if isinstance(value, (list, tuple, set)) else [value]
        for part in values:
            for finding in classify_text(str(part)):
                if finding.classification in {"ACTIVE_DEPENDENCY","PROXY_OVERCLAIM","AMBIGUOUS_HUMAN_GATE_TERMINOLOGY"}:
                    errors.append(f"{finding.classification}: {finding.message}")
    return sorted(set(errors))

FORBIDDEN_EXPERIMENT_KEYS = {
    "participants","participant_id","participant_age","participant_cohort","consent","recruitment",
    "sample_recruitment","participant_compensation","human_subject_privacy","respondents",
}
MACHINE_EXPERIMENT_REQUIRED = {
    "EXPERIMENT_ID","RUN_ID","METHOD_VERSION","METHOD_STATUS","FREEZE_ID","INPUT_DATASET","INPUT_VERSION","INPUT_HASH",
    "MODEL_OR_TOOL","MODEL_OR_TOOL_VERSION","PROMPT_OR_RULESET_VERSION","RANDOM_SEED","N_RUNS","BENCHMARK_SET",
    "HOLDOUT_SET","PERTURBATION_SET","ADVERSARIAL_CASES","ERROR_METRIC","AGGREGATION_METHOD","UNCERTAINTY_METHOD",
    "CROSS_METHOD_AGREEMENT","CROSS_MODEL_DISAGREEMENT","OUTPUT_HASH","REPRODUCTION_POINTER","LIMITATIONS",
    "PROHIBITED_OVERCLAIMS",
}

def validate_experiment(obj: dict[str, Any]) -> list[str]:
    errors = _require_fields(obj, MACHINE_EXPERIMENT_REQUIRED)
    lowered = {str(k).lower() for k in obj}
    for key in sorted(FORBIDDEN_EXPERIMENT_KEYS & lowered):
        errors.append(f"default machine experiment forbids field: {key}")
    findings = classify_text(json.dumps(obj, ensure_ascii=False))
    for finding in findings:
        if finding.classification in {"ACTIVE_DEPENDENCY","PROXY_OVERCLAIM","AMBIGUOUS_HUMAN_GATE_TERMINOLOGY"}:
            errors.append(f"{finding.classification}: {finding.message}")
    return sorted(set(errors))


def admit_question(obj: dict[str, Any]) -> dict[str, Any]:
    errors = validate_question(obj)
    return {
        "ADMISSION_STATUS": "ADMITTED_MACHINE_RESEARCH" if not errors else "REJECTED_DEFAULT_RESEARCH_ARCHITECTURE",
        "ERROR_CODE": None if not errors else "METHOD_NOT_MACHINE_EXECUTABLE",
        "REQUIRE_MACHINE_REDESIGN": bool(errors),
        "ERRORS": errors,
    }

def admit_work_package(obj: dict[str, Any]) -> dict[str, Any]:
    errors = validate_work_package(obj)
    return {
        "ADMISSION_STATUS": "ADMITTED_MACHINE_RESEARCH" if not errors else "REJECT_METHOD",
        "ERROR_CODE": None if not errors else "METHOD_NOT_MACHINE_EXECUTABLE",
        "REQUIRE_MACHINE_REDESIGN": bool(errors),
        "ERRORS": errors,
    }

def verify_machine_invariant(obj: dict[str, Any]) -> dict[str, Any]:
    errors = validate_work_package(obj)
    text = " ".join(str(obj.get(k, "")) for k in (
        "EXECUTION_SURFACE","SOURCE_ACCESS_METHOD","COMPUTATION_METHOD","VERIFICATION_METHOD","LIMITATIONS","OWNER_GATE_IF_ANY"
    ))
    findings = classify_text(text)
    active = sum(f.classification == "ACTIVE_DEPENDENCY" for f in findings)
    ambiguous = sum(f.classification == "AMBIGUOUS_HUMAN_GATE_TERMINOLOGY" for f in findings)
    external_review = int(obj.get("REQUIRES_EXTERNAL_HUMAN_REVIEW") is not False or obj.get("REQUIRES_EXTERNAL_REVIEWER") is not False)
    owner_labor = int(obj.get("REQUIRES_OWNER_MANUAL_RESEARCH") is not False)
    human_collection = int(obj.get("REQUIRES_HUMAN_DATA_COLLECTION") is not False or obj.get("REQUIRES_NEW_HUMAN_DATA") is not False)
    third_party = int(obj.get("REQUIRES_THIRD_PARTY_HUMAN") is not False) + active
    return {
        "STATUS": "PASS" if not errors else "FAIL",
        "MACHINE_EXECUTABLE": "PASS" if not errors else "FAIL",
        "THIRD_PARTY_HUMAN_DEPENDENCY": third_party,
        "OWNER_MANUAL_RESEARCH_DEPENDENCY": owner_labor,
        "EXTERNAL_HUMAN_REVIEW_DEPENDENCY": external_review,
        "HUMAN_COLLECTION_PATH": human_collection,
        "AMBIGUOUS_HUMAN_GATE_TERMINOLOGY": ambiguous,
        "ERRORS": errors,
    }

def validate_human_research_authorization(auth: dict[str, Any]) -> list[str]:
    required = {
        "CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM","PROJECT_ID","QUESTION_ID",
        "REAL_NON_OWNER_HUMANS_MAY_PARTICIPATE","SCOPE","NAMESPACE",
    }
    errors = _require_fields(auth, required)
    if auth.get("CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM") is not True:
        errors.append("CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM must be true")
    if auth.get("REAL_NON_OWNER_HUMANS_MAY_PARTICIPATE") is not True:
        errors.append("REAL_NON_OWNER_HUMANS_MAY_PARTICIPATE must be true")
    if not str(auth.get("NAMESPACE","")).startswith("human-research/"):
        errors.append("human research authorization requires human-research/ namespace")
    if not auth.get("PROJECT_ID") or not auth.get("QUESTION_ID") or not auth.get("SCOPE"):
        errors.append("human research authorization must be exact and bounded")
    return sorted(set(errors))

def validate_separate_human_work_package(obj: dict[str, Any], auth: dict[str, Any]) -> list[str]:
    errors = validate_human_research_authorization(auth)
    if errors:
        return errors
    if obj.get("NAMESPACE") != auth.get("NAMESPACE"):
        errors.append("work package namespace differs from OWNER authorization")
    if obj.get("QUESTION_ID") != auth.get("QUESTION_ID"):
        errors.append("work package question differs from OWNER authorization")
    if obj.get("PROJECT_ID") != auth.get("PROJECT_ID"):
        errors.append("work package project differs from OWNER authorization")
    return sorted(set(errors))

def lint_active_repository(root: Path = ROOT) -> list[str]:
    """Lint active Research Engine/control surfaces. Archives are history and are deliberately excluded."""
    errors: list[str] = []
    active_roots = [
        root / "AGENTS.md", root / "ROUTER.md", root / "SYSTEM_MANIFEST.yaml",
        root / "README.md", root / "ARCHITECTURE_MIGRATION_MAP.md",
        root / "contracts", root / "kernel", root / "protocols", root / "roles",
        root / "schemas", root / "engines/research",
    ]
    files: list[Path] = []
    for item in active_roots:
        if item.is_file():
            files.append(item)
        elif item.is_dir():
            files.extend(p for p in item.rglob("*") if p.is_file() and p.suffix.lower() in {".md",".yaml",".yml",".json",".py"})
    for path in sorted(set(files)):
        text = path.read_text(encoding="utf-8", errors="replace")
        # Classify bounded semantic chunks so a prohibition in one paragraph cannot mask an active dependency elsewhere.
        chunks = [c.strip() for c in re.split(r"\n\s*\n", text) if c.strip()]
        chunks.extend(line.strip() for line in text.splitlines() if line.strip())
        seen_findings: set[tuple[str, str]] = set()
        for chunk in chunks:
            for finding in classify_text(chunk):
                if finding.classification in {"ACTIVE_DEPENDENCY","PROXY_OVERCLAIM","AMBIGUOUS_HUMAN_GATE_TERMINOLOGY"}:
                    key = (finding.classification, finding.message)
                    if key not in seen_findings:
                        errors.append(f"{path.relative_to(root)}: {finding.classification}: {finding.message}")
                        seen_findings.add(key)
    return errors

def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv == ["--repo"]:
        errors = lint_active_repository()
        if errors:
            print("Research machine-only policy: FAIL")
            for err in errors:
                print(f"- {err}")
            return 1
        print("Research machine-only policy: PASS")
        return 0
    print("usage: research_policy.py [--repo]", file=sys.stderr)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
