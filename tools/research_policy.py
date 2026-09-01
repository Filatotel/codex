#!/usr/bin/env python3
from __future__ import annotations

import re
from tools import research_policy_legacy as _legacy
from tools.research_policy_legacy import *  # noqa: F401,F403

_base_classify = _legacy.classify_text
_base_action_is_negated = _legacy._action_is_negated
_base_active = tuple(p for p in _legacy.ACTIVE_ACTION_PATTERNS if "(?:ask|contact|consult)" not in p)

HUMAN_LABOR_TARGET = r"(?:(?:human\s+)?(?:annotators?|raters?|coders?|reviewers?)|(?:external\s+)?(?:annotators?|raters?|coders?|reviewers?)|crowdworkers?)"
HUMAN_LABOR_VERB = r"(?:label|annotate|rate|score|code|classify|review|validate|assess|evaluate)"

R2_ACTIVE_ACTION_PATTERNS = (
    rf"\b(?:contact|consult)\b.{{0,35}}\b{_legacy.HUMAN_TARGET}\b",
    rf"\bask\b.{{0,35}}\b(?:{_legacy.HUMAN_TARGET}|{HUMAN_LABOR_TARGET})\b.{{0,35}}\b(?:to\s+)?{HUMAN_LABOR_VERB}\b",
    rf"\b(?:hire|recruit|use|have|employ|contract)\b.{{0,45}}\b{HUMAN_LABOR_TARGET}\b",
    rf"\b(?:send|route|outsource|hand\s+off)\b.{{0,45}}\b(?:to\s+)?{HUMAN_LABOR_TARGET}\b.{{0,35}}\b(?:for\s+|to\s+)?(?:label(?:ing)?|annotat(?:e|ion)|rat(?:e|ing)|scor(?:e|ing)|cod(?:e|ing)|classif(?:y|ication)|review(?:ing)?)\b",
    r"\bcrowdsource(?:d|s|ing)?\b.{0,45}\b(?:annotation|annotating|labeling|rating|review|coding|classification)\b",
    r"\b(?:manual\s+human\s+labeling|human\s+annotation|human\s+rating|human\s+coding)\b",
)
R2_HUMAN_ACTION_MENTIONS = (
    r"\bhuman\s+annotations?\b", r"\bhuman\s+ratings?\b", r"\bhuman\s+coding\b",
    r"\bhuman\s+annotators?\b", r"\bhuman\s+raters?\b", r"\bhuman\s+coders?\b",
    r"\bcrowdworkers?\b", r"\bcrowdsourc(?:e|ed|es|ing)\b",
)
R2_STATIC_SOURCE_PATTERNS = (
    r"\barchived\b.{0,40}\b(?:human\s+)?annotations?\b",
    r"\barchived\b.{0,40}\b(?:human\s+)?ratings?\b",
    r"\bpre[- ]?existing\b.{0,40}\b(?:human\s+)?(?:annotations?|ratings?|coding)\b",
)

_legacy.ACTIVE_ACTION_PATTERNS = _base_active + R2_ACTIVE_ACTION_PATTERNS
_legacy.HUMAN_ACTION_MENTION_PATTERNS = _legacy.ACTIVE_ACTION_PATTERNS + (
    r"\bhuman\s+recruitment\b", r"\bparticipant\s+recruitment\b", r"\bthird[- ]party\s+human\s+research\b",
) + R2_HUMAN_ACTION_MENTIONS
_legacy.STATIC_SOURCE_PATTERNS = _legacy.STATIC_SOURCE_PATTERNS + R2_STATIC_SOURCE_PATTERNS


def _action_is_negated(clause: str, match: re.Match[str]) -> bool:
    if _base_action_is_negated(clause, match):
        return True
    before = clause[max(0, match.start() - 140):match.start()].lower()
    return bool(re.search(
        r"\b(?:never|does\s+not|do\s+not|cannot|can't)\s+(?:creates?|grants?|provides?|confers?)\s+(?:any\s+|the\s+)?(?:authority|permission)\s+to\s*$",
        before,
    ))


_legacy._action_is_negated = _action_is_negated


def _historical_reference_only(message: str) -> bool:
    prefix = "active prohibited human research action: "
    if not message.startswith(prefix):
        return False
    clause = message[len(prefix):].lower()
    if not any(cue in clause for cue in _legacy.HISTORICAL_CUES):
        return False
    return not re.search(
        r"\b(?:run|execute|resume|restart|deploy|start|recruit|collect|interview|survey|hire|use|have|employ|contract|send|route|outsource|crowdsource|ask|contact|consult)\b",
        clause,
    )


def classify_text(text: str):
    return [
        finding for finding in _base_classify(text)
        if not (finding.classification == "ACTIVE_DEPENDENCY" and _historical_reference_only(finding.message))
    ]


_legacy.classify_text = classify_text


if __name__ == "__main__":
    raise SystemExit(_legacy.main())
