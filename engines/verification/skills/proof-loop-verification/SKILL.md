# Proof Loop Verification

## Purpose

Use this skill when work is close to complete and you need to decide whether the task is actually done.

## Principle

Completion is not a statement. Completion is a claim backed by evidence for the exact candidate being accepted.

This skill applies the evidence model from `evidence-and-authority` to task/workstream completion. It does not grant release authority unless the project explicitly assigns that authority to this gate.

## Inputs

- task/workstream objective;
- frozen scope and non-goals;
- acceptance criteria and gates;
- current exact candidate state;
- changed files/artifacts;
- available tests, QA, reviews, audits, and approvals;
- known risks, blockers, and deferred findings.

## Required outputs

Produce or update a task evidence artifact containing:

- intended outcome;
- exact scope checked;
- exact candidate identity;
- acceptance criteria matrix;
- evidence by class;
- declared observation/search universe for negative claims where relevant;
- state-transition coverage matrix for important stateful contracts where relevant;
- unresolved issues;
- deferred out-of-scope findings;
- authority decision status where applicable;
- final verdict: PASS, PARTIAL, BLOCKED, or FAIL.

## Procedure

### 1. Restate the acceptance criteria as claims

Turn each criterion into something observable or reviewable.

Example:

```text
Criterion: stale clients must not overwrite newer state.
Claim to prove: a stale revision is rejected or reconciled by the declared conflict rule.
```

### 2. Confirm exact candidate state

Before collecting final evidence, identify the exact artifact/HEAD/build/schema/release being claimed complete.

If the candidate moves after verification, use `exact-state-verification` to decide what evidence became stale.

### 3. Check actual diff/scope

Verify:

- changed files/artifacts match frozen scope;
- no hidden feature expansion entered the workstream;
- blockers were not disguised as unrelated cleanup;
- deferred findings remain deferred unless they directly blocked correctness/security.

### 4. Attach evidence by class

Use `evidence-and-authority`:

#### Mechanical evidence

Examples:

- tests;
- compiler/typecheck;
- schema checks;
- migration replay;
- static analysis;
- exact diff/path checks.

#### Engineering / semantic evidence

Examples:

- code/architecture review;
- browser/manual QA;
- accessibility or UX pass;
- authority/ownership audit;
- risk analysis.

#### Authority decision

Where project policy requires explicit acceptance, record whether it has actually occurred.

Do not convert mechanical PASS into an authority decision by wording.

### 5. Use the strongest relevant verification

Do not choose the easiest check merely because it is green.

Verify the failure modes and boundaries that define the task, not only the happy path.

For a negative acceptance criterion such as `no X remains` or `A must not depend on B`, record the observation/search universe and prove the forbidden condition would be detected there. Absence from one grep or one file class is not global absence.

### 6. Cover supported starting states for important stateful contracts

Endpoint/action coverage can miss legitimate alternate starting states.

For important state machines or lifecycle mutations, derive verification from a bounded matrix such as:

```text
starting state
× action
× material failure point
→ expected authoritative state
→ expected projection / user-visible result
```

Include only states/failure points relevant to the accepted contract. Typical risk states can include:

- no persisted row yet / baseline-only state;
- active/current state;
- stale revision;
- partial migration/legacy state;
- repeated action/retry;
- terminal/closed state;
- concurrency where materially possible.

This is a verification heuristic, not a requirement to exhaust every combinatorial state in every project.

### 7. Preserve negative evidence

Record:

- failed checks;
- unresolved warnings;
- unavailable QA;
- contradictory review findings;
- assumptions not yet proven.

A stronger unrelated check does not erase negative evidence.

### 8. Apply verdict rules

#### PASS

All required acceptance criteria have sufficient current evidence and any required acceptance authority has been exercised.

#### PARTIAL

Meaningful work is correct/usable, but one or more non-blocking required evidence items or criteria remain incomplete.

#### BLOCKED

Completion cannot be established because a required dependency, authority decision, environment, or evidence path is unavailable.

#### FAIL

Current candidate contradicts an acceptance criterion or required verification fails.

### 9. Do not repair inside proof silently

If proof reveals a defect:

- return to the active workstream;
- respect `anti-loop-execution` stop conditions;
- fix only inside frozen scope or explicitly replan;
- then rerun proof on the new exact candidate.

The proof step itself should not silently broaden the implementation.

## Decision rules

- Completion belongs to the current exact candidate, not a branch name or prior state.
- Evidence must map to acceptance claims.
- Green automation does not prove unencoded semantic/product criteria.
- Negative evidence is scoped to the declared observation/search universe.
- Important stateful acceptance should cover the supported starting states that materially change semantics, not only one convenient setup path.
- Human/semantic review does not override a deterministic failed contract without an explicit contract change/acceptance decision.
- Missing evidence downgrades the verdict.
- Required authority decisions must be visible.
- Deferred non-blocking findings do not automatically block completion, but they must not disappear from the record.

## Anti-patterns

Avoid:

- "done in theory";
- "CI green" with no acceptance mapping;
- quoting tests from an older HEAD;
- `grep found nothing` with no declared search universe when absence is an acceptance claim;
- testing one stateful happy path and treating it as proof for every supported starting state;
- hiding unavailable manual/semantic checks;
- changing implementation while writing final proof without reopening execution;
- treating reviewer confidence as release authority;
- treating a failed criterion as a warning merely to preserve a PASS verdict.

## Minimal verdict format

```md
## Proof loop

- Status: PASS / PARTIAL / BLOCKED / FAIL
- Exact candidate:
- Scope checked:
- Acceptance criteria:
- Mechanical evidence:
- Engineering/semantic evidence:
- Negative-claim observation universe (if applicable):
- Stateful transition coverage (if applicable):
- Authority status:
- Negative findings / residual risk:
- Deferred findings:
- Next action:
```

## Pair with

- `evidence-and-authority` for evidence classes, derived claims, and negative-evidence scope;
- `exact-state-verification` for candidate identity;
- `pre-merge-review` for risk-focused review;
- `anti-loop-execution` when proof reveals a stop condition;
- `merge-preview-check` for integration risk before merge.
