#!/usr/bin/env python3
from __future__ import annotations

import re
from tools import research_policy_legacy as _legacy
from tools.research_policy_legacy import *  # noqa: F401,F403

# RE-KERNEL-HUMAN-01-R2: bounded classifier repair layered over the merged R1
# implementation. Keep the underlying admission/validation contracts unchanged;
# only narrow false-positive action matching and add missing third-party human
# annotation/rating/coding/crowd-labor coverage.

_base_classify = _legacy.classify_text

# The R1 generic "ask/contact/consult ... human target" rule also matched normal
# control text such as "ask the user again". Contact/consult remain prohibited
# human-dependency actions; "ask" is only research labor when it assigns a
# research task.
_base_active = tuple(
    p for p in _legacy.ACTIVE_ACTION_PATTERNS
    if "(?:ask|contact|consult)" not in p
)

HUMAN_LABOR_TARGET = r"(?:human\s+)?(?:annotators?|raters?|coders?|reviewers?)|(?:external\s+)?(?:annotators?|raters?|coders?|reviewers?)|crowdworkers?"
HUMAN_LABOR_VERB = r"(?:label|annotate|rate|score|code|classify|review|validate|assess|evaluate)"

R2_ACTIVE_ACTION_PATTERNS = (
    rf"\b(?:contact|consult)\b.{{0,35}}\b{_legacy.HUMAN_TARGET}\b",
    rf"\bask\b.{{0,35}}\b(?:{_legacy.HUMAN_TARGET}|{HUMAN_LABOR_TARGET})\b.{{0,35}}\b(?:to\s+)?{HUMAN_LABOR_VERB}\b",
    rf"\b(?:hire|recruit|use|have|employ|contract)\b.{{0,45}}\b{HUMAN_LABOR_TARGET}\b.{{0,35}}\b(?:to\s+)?{HUMAN_LABOR_VERB}\b",
    rf"\b(?:send|route|outsource|hand\s+off)\b.{{0,45}}\b(?:to\s+)?{HUMAN_LABOR_TARGET}\b.{{0,35}}\b(?:for\s+|to\s+)?(?:label(?:ing)?|annotat(?:e|ion)|rat(?:e|ing)|scor(?:e|ing)|cod(?:e|ing)|classif(?:y|ication)|review(?:ing)?)\b",
    r"\bcrowdsource(?:d|s|ing)?\b.{0,45}\b(?:annotation|annotating|labeling|rating|review|coding|classification)\b",
    r"\b(?:manual\s+human\s+labeling|human\s+annotation|human\s+rating|human\s+coding)\b",
)

R2_HUMAN_ACTION_MENTIONS = (
    r"\bhuman\s+annotations?\b",
    r"\bhuman\s+ratings?\b",
    r"\bhuman\s+coding\b",
    r"\bhuman\s+annotators?\b",
    r"\bhuman\s+raters?\b",
    r"\bhuman\s+coders?\b",
    r"\bcrowdworkers?\b",
    r"\bcrowdsourc(?:e|ed|es|ing)\b",
)

R2_STATIC_SOURCE_PATTERNS = (
    r"\barchived\b.{0,40}\b(?:human\s+)?annotations?\b",
    r"\barchived\b.{0,40}\b(?:human\s+)?ratings?\b",
    r"\bpre[- ]?existing\b.{0,40}\b(?:human\s+)?(?:annotations?|ratings?|coding)\b",
)

_legacy.ACTIVE_ACTION_PATTERNS = _base_active + R2_ACTIVE_ACTION_PATTERNS
_legacy.HUMAN_ACTION_MENTION_PATTERNS = _legacy.ACTIVE_ACTION_PATTERNS + (
    r"\bhuman\s+recruitment\b",
    r"\bparticipant\s+recruitment\b",
    r"\bthird[- ]party\s+human\s+research\b",
) + R2_HUMAN_ACTION_MENTIONS
_legacy.STATIC_SOURCE_PATTERNS = _legacy.STATIC_SOURCE_PATTERNS + R2_STATIC_SOURCE_PATTERNS


def classify_text(text: str):
    findings = _base_classify(text)
    # Static/historical references may mention past human labor, but the new R2
    # action patterns intentionally require present assignment verbs. Preserve
    # mixed-text failure: an explicit prohibition/static cue never erases a
    # separate ACTIVE_DEPENDENCY emitted for another clause/action.
    return findings


# Legacy validators and repository lint resolve classify_text from their module
# globals at call time. Patch that single semantic hook so all existing public
# validators receive the R2 classifier without altering their contracts.
_legacy.classify_text = classify_text


if __name__ == "__main__":
    raise SystemExit(_legacy.main())
