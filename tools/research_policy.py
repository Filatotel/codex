#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

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

QUESTION_REQUIRED_FIELDS = {
    "QUESTION_ID", "QUESTION", "TARGET_CONSTRUCT", "MACHINE_EXECUTABLE",
    "AVAILABLE_MACHINE_METHODS", "AVAILABLE_EXTERNAL_PREEXISTING_EVIDENCE",
    "REQUIRES_THIRD_PARTY_HUMAN", "REQUIRES_OWNER_MANUAL_RESEARCH",
    "REQUIRES_EXTERNAL_HUMAN_REVIEW", "REQUIRES_HUMAN_DATA_COLLECTION",
    "DIRECT_MEASUREMENT_POSSIBLE", "PROXY_MEASUREMENT_POSSIBLE",
    "EXPECTED_LIMITATION", "OWNER_DECISION_COMPONENT",
    "CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS",
    "OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS", "ADMISSION_STATUS",
}
WORK_PACKAGE_REQUIRED_FIELDS = {
    "WORK_PACKAGE_ID", "QUESTION_ID", "NAMESPACE", "EXECUTOR_ROLE", "VERIFIER_ROLE",
    "MACHINE_EXECUTABLE", "REQUIRES_THIRD_PARTY_HUMAN",
    "REQUIRES_OWNER_MANUAL_RESEARCH", "REQUIRES_EXTERNAL_REVIEWER",
    "REQUIRES_EXTERNAL_HUMAN_REVIEW", "REQUIRES_NEW_HUMAN_DATA",
    "REQUIRES_HUMAN_DATA_COLLECTION", "CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS",
    "OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS", "EXECUTION_SURFACE",
    "SOURCE_ACCESS_METHOD", "COMPUTATION_METHOD", "VERIFICATION_METHOD",
    "LIMITATIONS", "PROHIBITED_OVERCLAIMS", "OWNER_GATE_IF_ANY",
}

AMBIGUOUS_OWNER_TERMS = (
    "human gate", "human scope gate", "human research pass", "human pass",
    "human review", "human validation", "human approval", "human decision",
)

# Action-oriented patterns. They identify project actions/dependencies, not merely the
# presence of human-derived words. Static-source and prohibition semantics are tracked
# independently, so one finding can never erase another.
ACTIVE_ACTION_PATTERNS = (
    r"\brecruit(?:ing|ed)?\b.{0,50}\b(?:participants?|respondents?|speakers?|listeners?|users?|humans?|experts?|subjects?)\b",
    r"\b(?:participant|human|native[- ]speaker|speaker|respondent|user|expert)\s+recruitment\b",
    r"\brecruitment\s+(?:of|for)\s+(?:\d+\s+)?(?:new\s+)?(?:participants?|respondents?|speakers?|listeners?|users?|humans?|experts?|subjects?)\b",
    r"\bsurvey\s+(?:\d+\s+)?(?:new\s+)?(?:participants?|respondents?|speakers?|listeners?|users?|people|humans?|subjects?)\b",
    r"\bsurvey(?:ing|ed)\b.{0,35}\b(?:participants?|respondents?|speakers?|listeners?|users?|people|humans?|subjects?)\b",
    r"\binterview\s+(?:\d+\s+)?(?:new\s+)?(?:participants?|respondents?|speakers?|listeners?|users?|people|humans?|experts?|subjects?)\b",
    r"\binterviewing\b.{0,35}\b(?:participants?|respondents?|speakers?|listeners?|users?|people|humans?|experts?|subjects?)\b",
    r"\b(?:conduct|run|deploy|administer|launch|start|resume|execute|perform)\b.{0,35}\b(?:survey|questionnaire|poll|interviews?|focus[ -]?groups?)\b",
    r"\b(?:survey|questionnaire|interview|focus[ -]?group)\s+(?:deployment|administration|collection)\b",
    r"\b(?:participant|respondent|human)\s+(?:data\s+)?collection\b",
    r"\b(?:collect|gather|solicit|obtain)\b.{0,35}\b(?:human\s+data|human\s+evidence|responses?|participant\s+data|respondent\s+data|ratings?|feedback)\b",
    r"\b(?:ask|contact|consult)\b.{0,30}\b(?:experts?|speakers?|listeners?|participants?|respondents?|users?|humans?)\b",
    r"\b(?:send|give|administer)\b.{0,30}\b(?:survey|questionnaire)\b.{0,30}\b(?:participants?|respondents?|users?|speakers?|humans?)\b",
    r"\bhave\s+(?:humans?|experts?|speakers?|listeners?|participants?|respondents?)\s+(?:check|review|rate|validate|annotate|code|assess|evaluate)\b",
    r"\b(?:external\s+reviewers?|human\s+reviewers?|experts?|native[- ]speakers?|participants?|respondents?)\b.{0,30}\b(?:review|validate|rate|annotate|check|assess|evaluate)\b",
    r"\b(?:review|validation|rating|annotation|assessment|evaluation)\s+by\s+(?:external\s+)?(?:experts?|humans?|reviewers?|speakers?|participants?)\b",
    r"\bget\s+(?:community|expert|speaker|listener|participant|respondent|user)\s+(?:feedback|review|validation|ratings?)\b",
    r"\btest\b.{0,30}\bwith\s+(?:listeners?|speakers?|users?|participants?|respondents?|humans?)\b",
    r"\bfind\s+(?:several\s+|\d+\s+)?(?:speakers?|participants?|experts?|listeners?|respondents?)\b",
    r"\b(?:external|human|expert|community|stakeholder)\s+(?:human\s+)?(?:review|validation|consultation|rating|annotation|assessment|evaluation)\b",
    r"\b(?:focus[ -]?group|user[ -]?testing|human[ -]?in[ -]?the[ -]?loop|collection[ -]?surface)\b",
    r"\b(?:new|project[- ]generated)\s+(?:human|participant|respondent|speaker|user).{0,30}\b(?:survey|interviews?|data|responses?|ratings?|evidence)\b",
    r"\b(?:route|send|hand\s+off)\b.{0,30}\b(?:to\s+)?(?:humans?|participants?|external\s+reviewers?|experts?)\b",
    r"\bowner(?:/k0)?\b.{0,60}\b(?:manually\s+)?collect\b.{0,40}\b(?:urls?|sources?|data|responses?)\b",
    r"\bowner(?:/k0)?\b.{0,60}\bsearch\b.{0,40}\b(?:sources?|web|literature)\b",
    r"\bowner(?:/k0)?\b.{0,60}\b(?:annotate|code|rate)\b.{0,40}\b(?:dataset|items?|responses?|samples?)\b",
)
HUMAN_ACTION_MENTION_PATTERNS = ACTIVE_ACTION_PATTERNS + (
    r"\bhuman\s+recruitment\b",
    r"\bparticipant\s+recruitment\b",
    r"\bthird[- ]party\s+human\s+research\b",
)
STATIC_SOURCE_PATTERNS = (
    r"\bpublished\s+(?:study|paper|survey|interviews?|dataset|corpus)\b",
    r"\barchived\s+(?:public\s+)?(?:interviews?|interview\s+corpus|survey|responses?|dataset|corpus|human\s+data)\b",
    r"\brecorded\s+speech\s+corpus\b",
    r"\bexisting\s+(?:survey|human\s+annotation|expert\s+judgment|dataset|interviews?|responses?)\b",
    r"\bexternally\s+conducted\s+survey\b",
    r"\bpublic\s+dataset\b",
    r"\bpre[- ]?existing\b",
    r"\bexternal[_ -]preexisting[_ -]human[_ -]data\b",
    r"\bhistorical\s+corpus\b",
)
HISTORICAL_CUES = ("historical", "legacy", "archived", "preserved lineage", "retired compatibility")
PROHIBITION_CUES = (
    "prohibited", "forbidden", "must not", "do not", "don't", "never", "cannot",
    "can't", "not allowed", "invalid", "default deny", "default-deny", "there is no",
    "no third-party", "must be zero", "are all zero", "requirements are all zero",
)
OWNER_CUES = ("owner/k0", "owner ", "owner_", "owner chooses", "owner accepts", "owner rejects", "owner adjudicat")
OWNER_DECISION_CUES = ("choose", "chooses", "accept", "reject", "defer", "decision", "adjudicat", "gate")
SIMULATED_HUMAN_OVERCLAIM = (
    r"\b(?:llm|model|simulat(?:ed|ion)|synthetic)\b.{0,80}\bhuman responses?\b",
    r"\bhuman responses?\b.{0,80}\b(?:llm|model|simulat(?:ed|ion)|synthetic)\b",
)
FATAL_FINDINGS = {"ACTIVE_DEPENDENCY", "PROXY_OVERCLAIM", "AMBIGUOUS_HUMAN_GATE_TERMINOLOGY"}


@dataclass(frozen=True)
class Finding:
    classification: str
    message: str


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _split_clauses(text: str) -> list[str]:
    normalized = str(text).replace("\r\n", "\n").replace("\r", "\n")
    return [part.strip() for part in re.split(r"(?:\n+|(?<=[.!?])\s+|\s*;\s*)", normalized) if part.strip()]


def _scope_after_last_contrast(prefix: str) -> str:
    parts = re.split(r"\b(?:but|however|nevertheless|nonetheless|yet|still)\b", prefix, flags=re.I)
    return parts[-1] if parts else prefix


def _action_is_negated(clause: str, match: re.Match[str]) -> bool:
    before = clause[max(0, match.start() - 120):match.start()].lower()
    after = clause[match.end():min(len(clause), match.end() + 80)].lower()
    prefix = clause[:match.start()].lower()
    scoped = _scope_after_last_contrast(prefix)

    # Direct action negation: the negative operator is immediately governing the action.
    if re.search(r"(?:do\s+not|don't|must\s+not|should\s+not|may\s+not|cannot|can't|never|forbid(?:den)?\s+to|prohibit(?:ed)?\s+to)\s+(?:ever\s+|directly\s+)?(?:\w+\s+){0,1}$", before):
        return True
    if re.search(r"\bno\s+(?:third[- ]party\s+human\s+|participant\s+|human\s+)?$", before):
        return True

    # Passive/direct suffix forms bind to the matched action itself.
    if re.search(r"^\s+(?:is|are)\s+(?:strictly\s+)?(?:prohibited|forbidden|not\s+allowed|invalid)\b", after):
        return True
    if re.search(r"^\s+(?:must|should|may)\s+(?:be\s+)?(?:prohibited|forbidden|zero|absent|false)\b", after):
        return True

    # Explicit policy labels govern the rest of the clause until a contrast cue.
    if re.match(r"^\s*(?:[-*]\s*)*(?:\*\*)?(?:prohibited|forbidden)(?:\*\*)?\s*:", scoped):
        return True
    if re.match(r"^\s*(?:[-*]\s*)*(?:\*\*)?default[- ]deny(?:\s+controls?)?(?:\*\*)?\s*:", scoped):
        return True

    # Negative governance relations may bind a list of actions rather than one adjacent verb.
    if re.search(r"\b(?:must|should|may|can)\s+not\s+(?:be\s+)?(?:assigned|include|involve|require|create|enter|route|introduce|use|perform|conduct|authorize|permit)\b.*$", scoped):
        return True
    if re.search(r"\b(?:there\s+(?:is|are)\s+no|no\s+(?:ordinary\s+)?transition)\b.*$", scoped):
        return True
    if re.search(r"\b(?:never|does\s+not|do\s+not|cannot|can't)\s+(?:create|grant|provide|confer)\s+(?:any\s+|the\s+)?(?:authority|permission)\s+to\s*$", before):
        return True
    if re.search(r"\bno\s+(?:authority|permission)\s+to\s*$", before):
        return True

    return False


def _clause_has_static_source(clause: str) -> bool:
    return any(re.search(pattern, clause, flags=re.I) for pattern in STATIC_SOURCE_PATTERNS)


def _clause_has_human_prohibition(clause: str) -> bool:
    t = _norm(clause)
    if not any(cue in t for cue in PROHIBITION_CUES):
        return False
    for pattern in HUMAN_ACTION_MENTION_PATTERNS:
        for match in re.finditer(pattern, clause, flags=re.I | re.S):
            if _action_is_negated(clause, match):
                return True
    return bool(re.search(r"\b(?:human recruitment|recruitment|human research|participant collection)\s+(?:is|are)\s+(?:prohibited|forbidden|not allowed|invalid)\b", t))


def classify_text(text: str) -> list[Finding]:
    """Return independent clause/action findings; allowable context never masks another action."""
    findings: list[Finding] = []
    for clause in _split_clauses(text):
        t = _norm(clause)

        for pattern in SIMULATED_HUMAN_OVERCLAIM:
            if re.search(pattern, clause, flags=re.I | re.S):
                findings.append(Finding("PROXY_OVERCLAIM", "machine/simulated output is labeled as human responses"))

        if _clause_has_static_source(clause):
            findings.append(Finding("STATIC_EXTERNAL_SOURCE", "pre-existing human-derived evidence"))

        prohibited_action = False
        active_action = False
        for pattern in ACTIVE_ACTION_PATTERNS:
            for match in re.finditer(pattern, clause, flags=re.I | re.S):
                if _action_is_negated(clause, match):
                    prohibited_action = True
                else:
                    active_action = True

        if prohibited_action or _clause_has_human_prohibition(clause):
            findings.append(Finding("EXPLICIT_PROHIBITION", "human action is explicitly negated/prohibited"))
        if active_action:
            findings.append(Finding("ACTIVE_DEPENDENCY", f"active prohibited human research action: {clause[:180]}"))

        historical_only = (
            any(cue in t for cue in HISTORICAL_CUES)
            and not active_action
            and not re.search(r"\b(?:run|execute|resume|deploy|start|recruit|collect)\b", t)
        )
        if historical_only and not _clause_has_static_source(clause):
            findings.append(Finding("HISTORICAL_REFERENCE", "historical/legacy reference"))

        clause_prohibits_human_term = prohibited_action or _clause_has_human_prohibition(clause)
        for term in AMBIGUOUS_OWNER_TERMS:
            if term in t and not clause_prohibits_human_term:
                findings.append(Finding("AMBIGUOUS_HUMAN_GATE_TERMINOLOGY", f"generic authority term: {term}"))

        if not active_action and any(cue in t for cue in OWNER_CUES) and any(cue in t for cue in OWNER_DECISION_CUES):
            findings.append(Finding("OWNER_AUTHORITY", "explicit Owner/K0 project authority"))

    unique: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for finding in findings:
        key = (finding.classification, finding.message)
        if key not in seen:
            seen.add(key)
            unique.append(finding)
    return unique


def _require_fields(obj: dict[str, Any], fields: Iterable[str]) -> list[str]:
    return [f"missing required field: {name}" for name in sorted(fields) if name not in obj]


def _reject_unknown_fields(obj: dict[str, Any], allowed: set[str]) -> list[str]:
    return [f"undeclared field not allowed: {name}" for name in sorted(set(obj) - allowed)]


def _validate_default_flags(obj: dict[str, Any], false_fields: set[str]) -> list[str]:
    errors = _require_fields(obj, DEFAULT_REQUIRED_TRUE | false_fields)
    for name in DEFAULT_REQUIRED_TRUE:
        if obj.get(name) is not True:
            errors.append(f"{name} must be true")
    for name in false_fields:
        if obj.get(name) is not False:
            errors.append(f"{name} must be false")
    return errors


def _iter_string_leaves(value: Any, path: str = "$") -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from _iter_string_leaves(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple, set)):
        for index, child in enumerate(value):
            yield from _iter_string_leaves(child, f"{path}[{index}]")


def _semantic_errors(value: Any, field_name: str) -> list[str]:
    errors: list[str] = []
    for path, text in _iter_string_leaves(value, field_name):
        for finding in classify_text(text):
            if finding.classification in FATAL_FINDINGS:
                errors.append(f"{path}: {finding.classification}: {finding.message}")
    return errors


QUESTION_SEMANTIC_FIELDS = {
    "QUESTION", "TARGET_CONSTRUCT", "AVAILABLE_MACHINE_METHODS",
    "AVAILABLE_EXTERNAL_PREEXISTING_EVIDENCE", "EXPECTED_LIMITATION", "OWNER_DECISION_COMPONENT",
}
WORK_PACKAGE_SEMANTIC_FIELDS = {
    "EXECUTION_SURFACE", "SOURCE_ACCESS_METHOD", "COMPUTATION_METHOD",
    "VERIFICATION_METHOD", "LIMITATIONS", "PROHIBITED_OVERCLAIMS", "OWNER_GATE_IF_ANY",
}
ALLOWED_EXECUTOR_ROLES = {
    "AI_R_MASTER", "AI_EVIDENCE_EXTRACTOR", "AI_SYNTHESIS_AGENT", "AI_R_REPAIR",
    "AI_ADVERSARIAL_VALIDATOR", "AI_RESEARCH_RELEASE_CONTROLLER",
}


def validate_question(obj: dict[str, Any]) -> list[str]:
    errors = _require_fields(obj, QUESTION_REQUIRED_FIELDS)
    errors += _reject_unknown_fields(obj, QUESTION_REQUIRED_FIELDS)
    errors += _validate_default_flags(obj, DEFAULT_REQUIRED_FALSE)
    if not obj.get("AVAILABLE_MACHINE_METHODS"):
        errors.append("AVAILABLE_MACHINE_METHODS must be non-empty")
    if obj.get("ADMISSION_STATUS") != "ADMITTED_MACHINE_RESEARCH":
        errors.append("ADMISSION_STATUS must be ADMITTED_MACHINE_RESEARCH for default execution")
    for name in QUESTION_SEMANTIC_FIELDS:
        errors += _semantic_errors(obj.get(name), name)
    return sorted(set(errors))


def validate_work_package(obj: dict[str, Any]) -> list[str]:
    errors = _require_fields(obj, WORK_PACKAGE_REQUIRED_FIELDS)
    errors += _reject_unknown_fields(obj, WORK_PACKAGE_REQUIRED_FIELDS)
    errors += _validate_default_flags(obj, WP_REQUIRED_FALSE)
    if str(obj.get("NAMESPACE", "")).startswith("human-research/"):
        errors.append("default Research Engine cannot admit human-research namespace")
    if obj.get("EXECUTOR_ROLE") not in ALLOWED_EXECUTOR_ROLES:
        errors.append("EXECUTOR_ROLE must be an allowed AI Research Engine role")
    if obj.get("VERIFIER_ROLE") != "AI_R_VERIFIER":
        errors.append("VERIFIER_ROLE must be AI_R_VERIFIER")
    gate = obj.get("OWNER_GATE_IF_ANY")
    if gate is not None and not re.fullmatch(r"OWNER_[A-Z0-9_]+", str(gate)):
        errors.append("OWNER_GATE_IF_ANY must be null or explicit OWNER_* authority term")
    for name in WORK_PACKAGE_SEMANTIC_FIELDS:
        errors += _semantic_errors(obj.get(name), name)
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
    findings: list[Finding] = []
    for name in WORK_PACKAGE_SEMANTIC_FIELDS:
        for _, text in _iter_string_leaves(obj.get(name), name):
            findings.extend(classify_text(text))
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


HUMAN_AUTH_FIELDS = {
    "AUTHORIZATION_ID", "OWNER_DECISION_RECORD_REF", "OWNER_AUTHORITY_ROLE",
    "PROJECT_ID", "QUESTION_ID", "SCOPE", "NAMESPACE", "NON_TRANSITIVE",
    "CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM", "REAL_NON_OWNER_HUMANS_MAY_PARTICIPATE",
    "DEFAULT_RESEARCH_MODE_UNCHANGED",
}
OWNER_AUTH_DECISION_KIND = "CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM"
OWNER_AUTH_SELECTED_OPTION = "AUTHORIZE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM"
OWNER_RECORD_REQUIRED = {
    "artifact_type", "artifact_id", "produced_by_role", "assignment_id", "input_state_ref",
    "status", "provenance", "related_artifacts", "question_ref", "options_presented",
    "selected_option", "owner_constraints", "consequences_acknowledged", "authority_role",
    "decision_kind", "project_id", "authorized_question_id", "authorized_scope",
    "authorized_namespace", "authorization_id", "non_transitive",
    "default_research_mode_unchanged",
}


def validate_human_research_authorization(
    auth: dict[str, Any],
    owner_decision_record: dict[str, Any] | None = None,
) -> list[str]:
    """Validate a separate opt-in authorization against a supplied durable Owner record.

    The authorization object is never authority by itself. The governed caller must resolve
    OWNER_DECISION_RECORD_REF from durable project state and pass that exact record here.
    """
    errors = _require_fields(auth, HUMAN_AUTH_FIELDS)
    errors += _reject_unknown_fields(auth, HUMAN_AUTH_FIELDS)
    for name in {
        "NON_TRANSITIVE", "CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM",
        "REAL_NON_OWNER_HUMANS_MAY_PARTICIPATE", "DEFAULT_RESEARCH_MODE_UNCHANGED",
    }:
        if auth.get(name) is not True:
            errors.append(f"{name} must be true")
    if auth.get("OWNER_AUTHORITY_ROLE") != "OWNER_K0":
        errors.append("OWNER_AUTHORITY_ROLE must be OWNER_K0")
    if not str(auth.get("NAMESPACE", "")).startswith("human-research/"):
        errors.append("human research authorization requires human-research/ namespace")
    for name in ("AUTHORIZATION_ID", "OWNER_DECISION_RECORD_REF", "PROJECT_ID", "QUESTION_ID", "SCOPE"):
        if not auth.get(name):
            errors.append(f"{name} must be non-empty")

    if owner_decision_record is None:
        errors.append("OWNER_DECISION_RECORD_REF is not resolvable to a durable Owner decision record")
        return sorted(set(errors))

    record = owner_decision_record
    errors += _require_fields(record, OWNER_RECORD_REQUIRED)
    checks = (
        (record.get("artifact_type") == "OWNER_DECISION_RECORD", "referenced record is not OWNER_DECISION_RECORD"),
        (record.get("artifact_id") == auth.get("OWNER_DECISION_RECORD_REF"), "OWNER_DECISION_RECORD_REF does not match record identity"),
        (record.get("produced_by_role") == "owner-interface", "Owner decision record is not produced by owner-interface"),
        (record.get("status") == "RECORDED", "Owner decision record is not durable RECORDED state"),
        (bool(record.get("assignment_id")), "Owner decision record lacks durable assignment provenance"),
        (bool(record.get("input_state_ref")), "Owner decision record lacks durable input-state provenance"),
        (isinstance(record.get("provenance"), list) and bool(record.get("provenance")), "Owner decision record lacks provenance entries"),
        (isinstance(record.get("related_artifacts"), list) and auth.get("AUTHORIZATION_ID") in record.get("related_artifacts", []), "Owner decision record does not bind the authorization artifact"),
        (record.get("question_ref") == auth.get("QUESTION_ID"), "Owner decision question_ref differs from authorization"),
        (isinstance(record.get("options_presented"), list) and OWNER_AUTH_SELECTED_OPTION in record.get("options_presented", []), "Owner decision did not present the human-research authorization option"),
        (record.get("authority_role") == "OWNER_K0", "Owner decision record authority is not OWNER_K0"),
        (record.get("decision_kind") == OWNER_AUTH_DECISION_KIND, "Owner decision does not authorize separate human research"),
        (record.get("selected_option") == OWNER_AUTH_SELECTED_OPTION, "Owner selected option does not authorize separate human research"),
        (record.get("project_id") == auth.get("PROJECT_ID"), "Owner decision project differs from authorization"),
        (record.get("authorized_question_id") == auth.get("QUESTION_ID"), "Owner decision question differs from authorization"),
        (record.get("authorized_scope") == auth.get("SCOPE"), "Owner decision scope does not exactly bound authorization"),
        (record.get("authorized_namespace") == auth.get("NAMESPACE"), "Owner decision namespace differs from authorization"),
        (record.get("authorization_id") == auth.get("AUTHORIZATION_ID"), "Owner decision authorization identity differs"),
        (record.get("non_transitive") is True and auth.get("NON_TRANSITIVE") is True, "human research authorization must be non-transitive"),
        (record.get("default_research_mode_unchanged") is True and auth.get("DEFAULT_RESEARCH_MODE_UNCHANGED") is True, "authorization must not modify default Research mode"),
    )
    for ok, message in checks:
        if not ok:
            errors.append(message)
    return sorted(set(errors))


def validate_separate_human_work_package(
    obj: dict[str, Any],
    auth: dict[str, Any],
    owner_decision_record: dict[str, Any] | None = None,
) -> list[str]:
    errors = validate_human_research_authorization(auth, owner_decision_record)
    if errors:
        return errors
    if obj.get("NAMESPACE") != auth.get("NAMESPACE"):
        errors.append("work package namespace differs from OWNER authorization")
    if obj.get("QUESTION_ID") != auth.get("QUESTION_ID"):
        errors.append("work package question differs from OWNER authorization")
    if obj.get("PROJECT_ID") != auth.get("PROJECT_ID"):
        errors.append("work package project differs from OWNER authorization")
    return sorted(set(errors))


SOURCE_FIELDS = {
    "SOURCE_ID", "PROVENANCE_CLASS", "ORIGIN", "HUMAN_ORIGIN",
    "PROJECT_GENERATION_PROHIBITED", "DESCRIPTION", "SOURCE_URI",
}
SOURCE_REQUIRED_FIELDS = SOURCE_FIELDS - {"SOURCE_URI"}
SOURCE_CLASSES = {
    "PRIMARY_EXTERNAL_DATA", "PUBLIC_DATASET", "CORPUS", "SCHOLARLY_ANALYSIS",
    "DICTIONARY_REFERENCE", "OFFICIAL_REFERENCE", "COMMUNITY_ARCHIVE",
    "EXTERNAL_PREEXISTING_HUMAN_DATA", "SOFTWARE_DATASET", "PROXY", "OTHER",
    "LEGACY_HUMAN_TEST",
}
SOURCE_ORIGINS = {"EXTERNAL_PREEXISTING", "PROJECT_MACHINE_GENERATED", "LEGACY_PRESERVED", "UNKNOWN"}


def validate_source(obj: dict[str, Any]) -> list[str]:
    errors = _require_fields(obj, SOURCE_REQUIRED_FIELDS)
    errors += _reject_unknown_fields(obj, SOURCE_FIELDS)
    provenance = obj.get("PROVENANCE_CLASS")
    origin = obj.get("ORIGIN")
    human_origin = obj.get("HUMAN_ORIGIN")
    prohibited = obj.get("PROJECT_GENERATION_PROHIBITED")

    if provenance not in SOURCE_CLASSES:
        errors.append("PROVENANCE_CLASS is not recognized")
    if origin not in SOURCE_ORIGINS:
        errors.append("ORIGIN is not recognized")
    if not isinstance(human_origin, bool):
        errors.append("HUMAN_ORIGIN must be boolean")
    if not isinstance(prohibited, bool):
        errors.append("PROJECT_GENERATION_PROHIBITED must be boolean")
    if not isinstance(obj.get("DESCRIPTION"), str) or not obj.get("DESCRIPTION"):
        errors.append("DESCRIPTION must be a non-empty string")

    if human_origin is True:
        if prohibited is not True:
            errors.append("every human-origin source requires PROJECT_GENERATION_PROHIBITED=true")
        if origin not in {"EXTERNAL_PREEXISTING", "LEGACY_PRESERVED"}:
            errors.append("human-origin source must be provably external-preexisting or legacy-preserved")

    if provenance == "LEGACY_HUMAN_TEST":
        if prohibited is not True:
            errors.append("LEGACY_HUMAN_TEST requires PROJECT_GENERATION_PROHIBITED=true")
        if human_origin is not True or origin != "LEGACY_PRESERVED":
            errors.append("LEGACY_HUMAN_TEST must be HUMAN_ORIGIN=true and ORIGIN=LEGACY_PRESERVED")

    if provenance == "EXTERNAL_PREEXISTING_HUMAN_DATA":
        if prohibited is not True:
            errors.append("EXTERNAL_PREEXISTING_HUMAN_DATA requires PROJECT_GENERATION_PROHIBITED=true")
        if human_origin is not True or origin != "EXTERNAL_PREEXISTING":
            errors.append("EXTERNAL_PREEXISTING_HUMAN_DATA must prove external pre-existing human origin")

    if provenance == "OTHER" and origin == "UNKNOWN":
        errors.append("OTHER source cannot use ambiguous UNKNOWN origin")

    errors += _semantic_errors(obj.get("DESCRIPTION"), "DESCRIPTION")
    if obj.get("SOURCE_URI") is not None:
        errors += _semantic_errors(obj.get("SOURCE_URI"), "SOURCE_URI")
    return sorted(set(errors))


FORBIDDEN_HUMAN_KEYS = {
    "participants", "participant", "participant_id", "participant_age", "participant_cohort",
    "participant_plan", "consent", "recruitment", "sample_recruitment",
    "participant_compensation", "human_subject_privacy", "respondents", "respondent",
    "reviewers", "human_reviewers", "human_raters", "human_annotators", "interviewees",
    "survey_respondents",
}
MACHINE_EXPERIMENT_REQUIRED = {
    "EXPERIMENT_ID", "RUN_ID", "METHOD_VERSION", "METHOD_STATUS", "FREEZE_ID",
    "INPUT_DATASET", "INPUT_VERSION", "INPUT_HASH", "MODEL_OR_TOOL",
    "MODEL_OR_TOOL_VERSION", "PROMPT_OR_RULESET_VERSION", "RANDOM_SEED", "N_RUNS",
    "BENCHMARK_SET", "HOLDOUT_SET", "PERTURBATION_SET", "ADVERSARIAL_CASES",
    "ERROR_METRIC", "AGGREGATION_METHOD", "UNCERTAINTY_METHOD",
    "CROSS_METHOD_AGREEMENT", "CROSS_MODEL_DISAGREEMENT", "OUTPUT_HASH",
    "REPRODUCTION_POINTER", "LIMITATIONS", "PROHIBITED_OVERCLAIMS",
}


def _normalize_key(key: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")


def _forbidden_key_errors(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if _normalize_key(key) in FORBIDDEN_HUMAN_KEYS:
                errors.append(f"forbidden human-research key at {child_path}")
            errors += _forbidden_key_errors(child, child_path)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            errors += _forbidden_key_errors(child, f"{path}[{index}]")
    return errors


def validate_experiment(obj: dict[str, Any]) -> list[str]:
    errors = _require_fields(obj, MACHINE_EXPERIMENT_REQUIRED)
    errors += _reject_unknown_fields(obj, MACHINE_EXPERIMENT_REQUIRED)
    errors += _forbidden_key_errors(obj)
    for key, value in obj.items():
        # Keys are structural only. Semantic classification applies recursively to value leaves.
        errors += _semantic_errors(value, key)
    n_runs = obj.get("N_RUNS")
    if not isinstance(n_runs, int) or isinstance(n_runs, bool) or n_runs < 1:
        errors.append("N_RUNS must be integer >= 1")
    return sorted(set(errors))


METHOD_FREEZE_REQUIRED = {
    "FREEZE_ID", "QUESTION_ID", "METHOD_VERSION", "METHOD_STATUS", "INPUT_IDENTITY",
    "METHOD", "MODEL_OR_TOOL_VERSION", "PROMPT_OR_RULESET_VERSION", "DATASET_SAMPLING",
    "RANDOM_SEED_POLICY", "METRICS", "AGGREGATION", "THRESHOLDS", "LIMITATIONS",
    "PLANNED_SENSITIVITY_ANALYSIS", "METHOD_FROZEN", "MACHINE_EXECUTABLE",
    "REQUIRES_THIRD_PARTY_HUMAN", "REQUIRES_OWNER_MANUAL_RESEARCH",
    "REQUIRES_EXTERNAL_HUMAN_REVIEW", "REQUIRES_HUMAN_DATA_COLLECTION",
}


def validate_method_freeze(obj: dict[str, Any]) -> list[str]:
    errors = _require_fields(obj, METHOD_FREEZE_REQUIRED)
    errors += _reject_unknown_fields(obj, METHOD_FREEZE_REQUIRED)
    if obj.get("METHOD_FROZEN") is not True:
        errors.append("METHOD_FROZEN must be true only after machine-only validation")
    if obj.get("MACHINE_EXECUTABLE") is not True:
        errors.append("MACHINE_EXECUTABLE must be true")
    for name in DEFAULT_REQUIRED_FALSE:
        if obj.get(name) is not False:
            errors.append(f"{name} must be false")
    errors += _forbidden_key_errors(obj)
    for key, value in obj.items():
        errors += _semantic_errors(value, key)
    return sorted(set(errors))


def lint_active_repository(root: Path = ROOT) -> list[str]:
    """Lint runtime/config/document surfaces; implementation/tests/archives are handled separately."""
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
            files.extend(
                p for p in item.rglob("*")
                if p.is_file() and p.suffix.lower() in {".md", ".yaml", ".yml", ".json"}
            )
    for path in sorted(set(files)):
        text = path.read_text(encoding="utf-8", errors="replace")
        for finding in classify_text(text):
            if finding.classification in FATAL_FINDINGS:
                errors.append(f"{path.relative_to(root)}: {finding.classification}: {finding.message}")
    return sorted(set(errors))


# Deterministic bounded regression matrix called by the ordinary structural gate.
def _base_wp() -> dict[str, Any]:
    return {
        "WORK_PACKAGE_ID": "WP-001", "QUESTION_ID": "Q-001", "NAMESPACE": "research/default",
        "EXECUTOR_ROLE": "AI_R_MASTER", "VERIFIER_ROLE": "AI_R_VERIFIER",
        "MACHINE_EXECUTABLE": True, "REQUIRES_THIRD_PARTY_HUMAN": False,
        "REQUIRES_OWNER_MANUAL_RESEARCH": False, "REQUIRES_EXTERNAL_REVIEWER": False,
        "REQUIRES_EXTERNAL_HUMAN_REVIEW": False, "REQUIRES_NEW_HUMAN_DATA": False,
        "REQUIRES_HUMAN_DATA_COLLECTION": False, "CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS": True,
        "OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS": True, "EXECUTION_SURFACE": "local machine runtime",
        "SOURCE_ACCESS_METHOD": "public machine-accessible corpus", "COMPUTATION_METHOD": "deterministic structural analysis",
        "VERIFICATION_METHOD": "automated reproducibility check", "LIMITATIONS": [],
        "PROHIBITED_OVERCLAIMS": ["Do not claim direct population measurement."], "OWNER_GATE_IF_ANY": None,
    }


def _base_question() -> dict[str, Any]:
    return {
        "QUESTION_ID": "Q-001", "QUESTION": "What structural pattern is supported?", "TARGET_CONSTRUCT": "structural pattern",
        "MACHINE_EXECUTABLE": True, "AVAILABLE_MACHINE_METHODS": ["deterministic corpus analysis"],
        "AVAILABLE_EXTERNAL_PREEXISTING_EVIDENCE": ["Published survey may be used as static evidence."],
        "REQUIRES_THIRD_PARTY_HUMAN": False, "REQUIRES_OWNER_MANUAL_RESEARCH": False,
        "REQUIRES_EXTERNAL_HUMAN_REVIEW": False, "REQUIRES_HUMAN_DATA_COLLECTION": False,
        "DIRECT_MEASUREMENT_POSSIBLE": False, "PROXY_MEASUREMENT_POSSIBLE": True,
        "EXPECTED_LIMITATION": "Direct population measurement remains unavailable.", "OWNER_DECISION_COMPONENT": None,
        "CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS": True, "OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS": True,
        "ADMISSION_STATUS": "ADMITTED_MACHINE_RESEARCH",
    }


def _owner_auth_pair() -> tuple[dict[str, Any], dict[str, Any]]:
    auth = {
        "AUTHORIZATION_ID": "HRA-001", "OWNER_DECISION_RECORD_REF": "ODR-001", "OWNER_AUTHORITY_ROLE": "OWNER_K0",
        "PROJECT_ID": "P-1", "QUESTION_ID": "Q-H1", "SCOPE": "one bounded recognition study",
        "NAMESPACE": "human-research/P-1/Q-H1", "NON_TRANSITIVE": True,
        "CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM": True, "REAL_NON_OWNER_HUMANS_MAY_PARTICIPATE": True,
        "DEFAULT_RESEARCH_MODE_UNCHANGED": True,
    }
    record = {
        "artifact_type": "OWNER_DECISION_RECORD", "artifact_id": "ODR-001", "produced_by_role": "owner-interface",
        "assignment_id": "ASG-OWNER-001", "input_state_ref": "state://P-1/owner/ODR-001", "status": "RECORDED",
        "provenance": ["OWNER_K0 explicit decision"], "related_artifacts": ["HRA-001"], "question_ref": "Q-H1",
        "options_presented": [OWNER_AUTH_SELECTED_OPTION, "REJECT_SEPARATE_HUMAN_RESEARCH_WORKSTREAM"],
        "selected_option": OWNER_AUTH_SELECTED_OPTION, "owner_constraints": ["bounded exact scope"],
        "consequences_acknowledged": ["default Research mode remains machine-only"],
        "authority_role": "OWNER_K0", "decision_kind": OWNER_AUTH_DECISION_KIND, "project_id": "P-1",
        "authorized_question_id": "Q-H1", "authorized_scope": "one bounded recognition study",
        "authorized_namespace": "human-research/P-1/Q-H1", "authorization_id": "HRA-001",
        "non_transitive": True, "default_research_mode_unchanged": True,
    }
    return auth, record


def _base_experiment() -> dict[str, Any]:
    return {
        "EXPERIMENT_ID": "EXP-1", "RUN_ID": "RUN-1", "METHOD_VERSION": "1.0", "METHOD_STATUS": "FROZEN",
        "FREEZE_ID": "FRZ-1", "INPUT_DATASET": "public machine-readable corpus", "INPUT_VERSION": "1",
        "INPUT_HASH": "sha256:input", "MODEL_OR_TOOL": "python", "MODEL_OR_TOOL_VERSION": "3",
        "PROMPT_OR_RULESET_VERSION": "rules-1", "RANDOM_SEED": 1, "N_RUNS": 1, "BENCHMARK_SET": [],
        "HOLDOUT_SET": [], "PERTURBATION_SET": [], "ADVERSARIAL_CASES": [], "ERROR_METRIC": "exact mismatch",
        "AGGREGATION_METHOD": "deterministic", "UNCERTAINTY_METHOD": "sensitivity bounds",
        "CROSS_METHOD_AGREEMENT": "not applicable", "CROSS_MODEL_DISAGREEMENT": "not applicable",
        "OUTPUT_HASH": "sha256:output", "REPRODUCTION_POINTER": "runs/RUN-1", "LIMITATIONS": ["Proxy only."],
        "PROHIBITED_OVERCLAIMS": ["Do not claim direct population recognition."],
    }


def _base_freeze() -> dict[str, Any]:
    return {
        "FREEZE_ID": "FRZ-1", "QUESTION_ID": "Q-1", "METHOD_VERSION": "1.0", "METHOD_STATUS": "FROZEN",
        "INPUT_IDENTITY": "public corpus v1", "METHOD": "deterministic computational analysis",
        "MODEL_OR_TOOL_VERSION": "python-3", "PROMPT_OR_RULESET_VERSION": "rules-1",
        "DATASET_SAMPLING": "deterministic full-corpus pass", "RANDOM_SEED_POLICY": "fixed seed",
        "METRICS": ["exact agreement"], "AGGREGATION": "mean", "THRESHOLDS": {"minimum": 0.8},
        "LIMITATIONS": ["Proxy only."], "PLANNED_SENSITIVITY_ANALYSIS": "parameter sweep", "METHOD_FROZEN": True,
        "MACHINE_EXECUTABLE": True, "REQUIRES_THIRD_PARTY_HUMAN": False, "REQUIRES_OWNER_MANUAL_RESEARCH": False,
        "REQUIRES_EXTERNAL_HUMAN_REVIEW": False, "REQUIRES_HUMAN_DATA_COLLECTION": False,
    }


def machine_only_regression_results() -> dict[str, str]:
    results: dict[str, str] = {}

    def check(case: str, condition: bool) -> None:
        results[case] = "PASS" if condition else "FAIL"

    check("T01", any(f.classification == "ACTIVE_DEPENDENCY" for f in classify_text("Recruit native speakers.")))
    check("T02", any(f.classification == "ACTIVE_DEPENDENCY" for f in classify_text("Recruit native speakers. Do not overclaim.")))

    findings = classify_text("Do not recruit native speakers.")
    check("T03", any(f.classification == "EXPLICIT_PROHIBITION" for f in findings) and not any(f.classification == "ACTIVE_DEPENDENCY" for f in findings))

    findings = classify_text("Use a published survey of 500 respondents.")
    check("T04", any(f.classification == "STATIC_EXTERNAL_SOURCE" for f in findings) and not any(f.classification == "ACTIVE_DEPENDENCY" for f in findings))

    findings = classify_text("Use a published survey, then recruit 20 respondents.")
    classes = {f.classification for f in findings}
    check("T05", "STATIC_EXTERNAL_SOURCE" in classes and "ACTIVE_DEPENDENCY" in classes)

    findings = classify_text("Analyze archived interviews and interview five new speakers.")
    classes = {f.classification for f in findings}
    check("T06", "STATIC_EXTERNAL_SOURCE" in classes and "ACTIVE_DEPENDENCY" in classes)

    wp = _base_wp(); wp["PARTICIPANT_PLAN"] = "Recruit 50 speakers."
    check("T07", bool(validate_work_package(wp)))
    wp = _base_wp(); wp["METADATA"] = {"execution": {"reviewers": "external experts"}}
    check("T08", bool(validate_work_package(wp)))

    question = _base_question(); question["AVAILABLE_MACHINE_METHODS"] = ["Recruit native speakers"]
    check("T09", bool(validate_question(question)))
    question = _base_question(); question["AVAILABLE_EXTERNAL_PREEXISTING_EVIDENCE"] = ["Published survey, then recruit 20 new respondents."]
    check("T10", bool(validate_question(question)))

    wp = _base_wp(); wp["COMPUTATION_METHOD"] = "MODEL_PROXY ensemble comparison, explicitly labeled proxy-only."
    check("T11", not validate_work_package(wp))
    wp = _base_wp(); wp["COMPUTATION_METHOD"] = "Use simulated LLM outputs as human responses."
    check("T12", bool(validate_work_package(wp)))
    wp = _base_wp(); wp["OWNER_GATE_IF_ANY"] = "OWNER_ACCEPTANCE"; wp["LIMITATIONS"] = ["Owner accepts or rejects the project decision after machine evidence."]
    check("T13", not validate_work_package(wp))
    wp = _base_wp(); wp["REQUIRES_OWNER_MANUAL_RESEARCH"] = True; wp["SOURCE_ACCESS_METHOD"] = "Owner must manually collect 100 URLs."
    check("T14", bool(validate_work_package(wp)))

    auth, owner_record = _owner_auth_pair()
    check("T15", bool(validate_human_research_authorization(auth, None)))
    fake = dict(auth); fake["OWNER_DECISION_RECORD_REF"] = "ODR-NOT-FOUND"
    check("T16", bool(validate_human_research_authorization(fake, None)))
    mismatch = True
    for field, value in (("project_id", "P-OTHER"), ("authorized_question_id", "Q-OTHER"), ("authorized_scope", "broader study")):
        bad_record = dict(owner_record); bad_record[field] = value
        mismatch = mismatch and bool(validate_human_research_authorization(auth, bad_record))
    check("T17", mismatch)

    human_wp = {"PROJECT_ID": "P-1", "QUESTION_ID": "Q-H1", "NAMESPACE": "human-research/P-1/Q-H1"}
    default_wp = _base_wp(); default_wp["NAMESPACE"] = human_wp["NAMESPACE"]
    check("T18", not validate_human_research_authorization(auth, owner_record) and not validate_separate_human_work_package(human_wp, auth, owner_record) and bool(validate_work_package(default_wp)))

    source = {"SOURCE_ID": "SRC-1", "PROVENANCE_CLASS": "EXTERNAL_PREEXISTING_HUMAN_DATA", "ORIGIN": "EXTERNAL_PREEXISTING", "HUMAN_ORIGIN": True, "PROJECT_GENERATION_PROHIBITED": False, "DESCRIPTION": "Published survey dataset."}
    check("T19", bool(validate_source(source)))
    source = {"SOURCE_ID": "SRC-2", "PROVENANCE_CLASS": "OTHER", "ORIGIN": "PROJECT_MACHINE_GENERATED", "HUMAN_ORIGIN": True, "PROJECT_GENERATION_PROHIBITED": False, "DESCRIPTION": "Recruit participants and collect new human responses."}
    check("T20", bool(validate_source(source)))

    experiment = _base_experiment(); experiment["INPUT_DATASET"] = "Recruit 20 participants and collect responses."
    check("T21", bool(validate_experiment(experiment)))
    experiment = _base_experiment(); experiment["INPUT_DATASET"] = {"metadata": {"collection_plan": {"participants": "Recruit 20 participants."}}}
    check("T22", bool(validate_experiment(experiment)))
    experiment = _base_experiment(); experiment["INPUT_DATASET"] = "Archived public interview corpus."
    check("T23", not validate_experiment(experiment))

    freeze = _base_freeze(); freeze["METHOD"] = "Recruit 50 speakers and survey them."
    check("T24", bool(validate_method_freeze(freeze)))
    check("T25", not validate_method_freeze(_base_freeze()))

    wp = _base_wp(); wp["SOURCE_ACCESS_METHOD"] = "No suitable public evidence is currently available."; wp["COMPUTATION_METHOD"] = "Return UNKNOWN / INSUFFICIENT_PUBLIC_EVIDENCE."
    check("T26", not validate_work_package(wp))

    findings = classify_text("Human recruitment is prohibited, nevertheless recruit 20 speakers.")
    classes = {f.classification for f in findings}
    check("T27", "EXPLICIT_PROHIBITION" in classes and "ACTIVE_DEPENDENCY" in classes)

    findings = classify_text("Use a published survey, then recruit 20 respondents.")
    classes = {f.classification for f in findings}
    check("T28", "STATIC_EXTERNAL_SOURCE" in classes and "ACTIVE_DEPENDENCY" in classes)

    return results


def run_machine_only_regressions() -> list[str]:
    return [
        f"{case}: machine-only regression failed"
        for case, result in machine_only_regression_results().items()
        if result != "PASS"
    ]


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv == ["--repo"]:
        errors = lint_active_repository()
        errors.extend(run_machine_only_regressions())
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
