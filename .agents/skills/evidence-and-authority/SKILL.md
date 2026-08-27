# Evidence and Authority

## Purpose

Use this skill when deciding what a test, review, observation, audit, or approval actually proves.

## Goal

Prevent one type of evidence from impersonating another and prevent green automation from silently granting acceptance or release authority.

## When to use

Use when:

- CI/test results are being used to justify completion;
- manual QA or semantic review matters;
- a release/certification decision has explicit owners;
- automated validators cover only part of correctness;
- an agent needs to report confidence without overstating proof.

## Do not use when

Do not use this skill to:

- downgrade strong machine evidence merely because it is automated;
- require human approval for every trivial change;
- replace project-specific acceptance rules;
- create vague categories that cannot be tied to claims.

## Inputs

- claim being made;
- acceptance/release criteria;
- available tests, observations, audits, reviews, and approvals;
- exact state those checks apply to;
- known gaps.

## Required output

A claim/evidence matrix:

| Claim | Evidence type | Evidence | Exact state | What it proves | What it does not prove | Authority needed |
|---|---|---|---|---|---|---|

## Evidence classes

Use three broad classes. Projects may subdivide them, but should not collapse them.

### 1. MECHANICAL EVIDENCE

Deterministic or reproducible checks over explicit conditions.

Examples:

- compiler/typecheck;
- unit/integration tests;
- schema validation;
- static analysis;
- migration replay test;
- hash/digest equality;
- exact diff/path checks.

Mechanical evidence is strongest for claims it explicitly encodes and weak outside them.

### 2. ENGINEERING / SEMANTIC EVIDENCE

Judgment about meaning, behavior, architecture, usability, risk, or fitness that is not fully reducible to a deterministic assertion.

Examples:

- code review;
- architecture/authority audit;
- UX readthrough;
- accessibility manual pass;
- visual comparison;
- interpretation that two modules do not duplicate responsibility;
- assessment that a fallback preserves intended behavior.

This evidence should still cite observations and criteria. "Looks fine" is not semantic proof.

### 3. AUTHORITY DECISION

An explicit decision by the person/process authorized to accept, merge, freeze, release, migrate, or otherwise change project status.

Examples:

- approving a design contract;
- accepting a breaking migration;
- merging a PR when project policy grants that authority;
- declaring a release candidate frozen;
- signing off a production launch.

Authority may rely on mechanical and semantic evidence, but evidence alone does not automatically create the decision unless project policy explicitly says it does.

## Procedure

### 1. Start from claims

Do not start from a list of tests and infer that "everything is good."

Write the important claims first:

```text
build is valid
migration is replay-safe
UI is usable on target devices
architecture preserves ownership
candidate is approved for release
```

Then attach evidence to each.

### 2. State what each check actually observes

A test named `release-test` may only assert file presence.
A screenshot may show layout but not keyboard behavior.
A passing request may show one path but not concurrency safety.

Read the check, not its label.

### 3. Bind evidence to exact state

Use `exact-state-verification` when the artifact can move after evidence is collected.

If code, test logic, config, generated artifacts, or environment materially changes, re-evaluate affected claims.

### 4. Mark evidence gaps explicitly

Use outcomes such as:

- PASS — required evidence is sufficient for this claim;
- PARTIAL — some evidence exists, but required coverage is missing;
- BLOCKED — required evidence is absent or contradictory;
- NOT APPLICABLE — criterion does not apply.

Do not turn PARTIAL into PASS through optimistic prose.

### 5. Keep acceptance authority explicit

For meaningful release/freeze decisions, record:

- who/what has authority;
- required evidence;
- whether authority has actually been exercised.

If project policy says green CI automatically permits a routine merge, that is an explicit authority rule. Do not assume it universally.

### 6. Preserve negative evidence

A failed check, unresolved warning, manual mismatch, or contradictory observation remains part of the evidence set until resolved or explicitly accepted as residual risk.

Do not hide it because stronger unrelated checks passed.

## Decision rules

- Evidence is scoped to a claim.
- A check proves only what it observes/encodes.
- Mechanical PASS does not imply semantic correctness outside encoded contracts.
- Semantic review does not override a deterministic mechanical failure without an explicit decision to change the contract.
- Acceptance/release authority must be explicit for consequential state changes.
- Strong conclusions require strong evidence on the exact candidate.

## Anti-patterns

Avoid:

- "CI is green, therefore production is correct";
- "human looked at it, therefore schema is valid";
- "tests fail but review says it is fine" without changing/accepting the contract;
- quietly dropping negative findings from a final summary;
- treating review comments as acceptance authority when the reviewer does not own the decision;
- calling an artifact released before the release decision happened.

## Verification checklist

- [ ] Important claims are explicit.
- [ ] Evidence is attached to claims, not just listed.
- [ ] Mechanical and semantic evidence are distinguished.
- [ ] Evidence applies to the exact relevant state.
- [ ] Gaps and negative findings are visible.
- [ ] Acceptance/release authority is explicit where needed.
- [ ] No evidence class is overclaimed.

## Pair with

- `proof-loop-verification` for task completion;
- `pre-merge-review` for risk-focused semantic evidence;
- `exact-state-verification` for evidence provenance;
- `anti-loop-execution` when missing/contradictory evidence triggers a stop condition.
