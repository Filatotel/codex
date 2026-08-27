# Systematic Debugging

## Purpose

Use this skill for technical issues where guessing would create churn: build failures, runtime bugs, API problems, deployment failures, UI regressions, data/state corruption, integration issues, or failing verification.

## Goal

Find the root cause before changing code. The output should identify the failing layer, the evidence, the smallest safe fix, and the verification result.

This skill owns **technical causal diagnosis**. It does not own workstream mode switching; `anti-loop-execution` decides when execution must stop and enter Causal Audit Mode.

## When to use

Use this skill when:

- tests fail;
- builds fail;
- forms or APIs behave unexpectedly;
- deployment/config/bindings fail;
- UI works in one state but breaks in another;
- data, cache, queue, analytics, or external integration behavior is wrong;
- a stop condition has moved the workstream into Causal Audit Mode.

Do not use this skill for planned feature work without a bug or unknown failure.

## Inputs

- expected behavior;
- actual behavior;
- exact error/evidence;
- current exact working state;
- environment;
- recent relevant changes;
- prior failed hypotheses/fixes if any.

## Required outputs

- Failure restated
- Exact state/environment
- Evidence collected
- Failing layer
- Root cause or best bounded hypothesis
- Minimal correction or next diagnostic experiment
- Verification performed
- Residual risk
- Verdict: pass, partial, blocked, or fail

## Iron rule

No fixes before root-cause evidence.

A hypothesis is allowed.
A blind patch is not.

## Debugging layers

Choose layers appropriate to the project. Typical examples:

| Layer | Evidence to collect |
|---|---|
| User/UI | user steps, rendered state, focus/layout, console, network |
| Application | exact stack/error, control flow, state transition, recent change |
| API/service | request, response, logs, contract/version, authorization |
| Data/state | schema, migration state, persisted revision, cache, queue, stale state |
| Build/toolchain | command, compiler output, dependency/lock state, generated files |
| Deployment/config | environment, bindings, routes, secrets/config names, artifact revision |
| External integration | accepted request identity, provider response, retry semantics |
| Observability | emitted event/log/trace, timestamp/source, gaps, sampling assumptions |

## Procedure

### 1. Restate the failure

Capture:

- expected behavior;
- actual behavior;
- exact command, route, input, or user action;
- first known bad state;
- environment;
- exact artifact/revision when relevant.

### 2. Read the exact error/evidence

Do not summarize from memory.
Use the real error text, status code, stack trace, failed assertion, log entry, or observed behavior.

If no explicit error exists, record that and gather evidence rather than inventing one.

### 3. Reproduce or bound the failure

Ask:

- deterministic or intermittent?
- local, CI, preview, production, or all?
- input/device/environment dependent?
- revision dependent?
- concurrency/timing dependent?

If reproduction is impossible, downgrade confidence.

### 4. Verify exact state before diagnosis

Confirm the state you are debugging is the state you think it is:

- current working revision;
- tested/reviewed revision where relevant;
- generated/config/schema versions;
- target environment.

Use `exact-state-verification` when identity is non-trivial.

### 5. Check recent changes and authority assumptions

Inspect:

- relevant diff/history;
- changed contracts/config/data;
- whether two components disagree about which state is authoritative;
- whether a projection/cache/log is being mistaken for source state;
- whether a retry may be crossing an irreversible boundary.

Use `authority-mapping` or `irreversible-boundary-reasoning` when those are the real questions.

### 6. Isolate the failing layer

Trace the shortest causal path from trigger to expected effect.

Do not jump directly from visible symptom to the most familiar component.

### 7. Form one falsifiable hypothesis

Write:

```text
Hypothesis: X is failing because Y.
Evidence: A, B, C.
Minimal discriminating test: Z.
```

Test one causal variable at a time when possible.

### 8. Apply the smallest source fix

After the hypothesis is supported:

- fix the source, not only the symptom;
- avoid unrelated cleanup;
- preserve frozen scope;
- add regression evidence when the failure class warrants it.

### 9. Verify the correction on the current state

Use the strongest relevant check:

- originally failing test/path;
- broader regression suite if affected;
- build/typecheck/lint;
- migration/replay check;
- browser/manual reproduction;
- API/integration evidence;
- production/preview verification where appropriate.

Bind the result to the exact state verified.

## Anti-loop handoff

Repeated same-class failed fixes are not permission for more guessing.

Default rule unless the frozen workstream defines another threshold in advance:

```text
2 sequential same-class correction failures
→ stop point-fixing
→ CAUSAL AUDIT MODE
→ re-check assumptions, authority, exact state, and failure model
```

Likewise, repeated same-class tool/process failure without new evidence should stop retries and be classified as a process/environment problem.

A materially different failure after a real state change is not automatically the same class. Classify it.

`anti-loop-execution` owns the mode transition and resumption decision.

## Anti-patterns

Avoid:

- changing code before reading the exact failure;
- fixing only the visible symptom;
- stacking multiple fixes before testing;
- retrying the same tool operation with no changed evidence;
- assuming local success means production success;
- assuming timeout means the operation did not happen;
- hiding partial verification behind confident language;
- weakening/deleting checks just to make the task green;
- starting a new branch to escape an unresolved causal model.

## Verification checklist

- [ ] Failure is stated against an exact relevant state.
- [ ] Evidence precedes code changes.
- [ ] Failing layer is bounded.
- [ ] Hypothesis is falsifiable.
- [ ] Correction is minimal and inside frozen scope.
- [ ] Original failure path is rechecked.
- [ ] Repeated same-class failures trigger Causal Audit instead of another guess.
- [ ] Residual uncertainty is explicit.

## Pair with

- `anti-loop-execution` for stop/resume discipline;
- `exact-state-verification` for provenance;
- `authority-mapping` for source-of-truth conflicts;
- `irreversible-boundary-reasoning` for post-commit/retry failures;
- `proof-loop-verification` after the correction is complete.
