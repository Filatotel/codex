# Anti-Loop Execution

## Purpose

Use this skill to keep agent-driven implementation from turning into repeated patching, scope drift, branch proliferation, or tool retries without new evidence.

## Goal

Make execution finite and auditable by freezing the workstream before implementation and allowing exactly one active mode at a time:

- **EXECUTION MODE** — implement the frozen scope;
- **CAUSAL AUDIT MODE** — stop feature work and establish why execution is failing or why the current model is wrong.

This skill governs **workstream execution**, not technical diagnosis. Pair it with `systematic-debugging` when the stop condition is a software defect.

## When to use

Use for:

- non-trivial features or refactors;
- delegated or multi-session work;
- work with CI, deployment, migration, integration, or release gates;
- tasks where multiple agents or branches can diverge;
- any task that has already produced repeated same-class failures.

For a trivial single-edit task, the full artifact may be unnecessary, but the no-loop rules still apply.

## Do not use when

Do not use this skill to:

- decide product architecture;
- diagnose a bug in place of `systematic-debugging`;
- justify refusing a small obvious correction;
- create process ceremony with no meaningful stop condition.

## Inputs

- objective;
- scope;
- non-goals;
- acceptance criteria;
- owner;
- dependencies;
- gates;
- current authoritative working state;
- known risks and stop conditions.

## Required output

A frozen workstream record containing:

```text
objective
owner
scope
non-goals
dependencies
acceptance criteria
gates
initial authoritative state
mode
stop conditions
deferred findings
```

## Procedure

### 1. Freeze before substantial implementation

Before meaningful code changes, make the workstream explicit enough that another agent can tell what belongs and what does not.

A frozen scope is not immutable forever. It means changes to scope must be deliberate and visible rather than smuggled in through implementation.

### 2. Enter exactly one mode

#### EXECUTION MODE

Allowed:

- implement frozen scope;
- run verification;
- make corrections that directly belong to frozen correctness;
- record out-of-scope discoveries.

Not allowed:

- silently add another feature;
- redesign adjacent architecture because it looks cleaner;
- treat a new unrelated finding as permission to expand the PR;
- investigate root cause and keep speculative feature patching at the same time.

#### CAUSAL AUDIT MODE

Enter when a stop condition fires.

Allowed:

- inspect evidence;
- reproduce and isolate failure;
- compare assumptions with actual state;
- inspect branch/tool/environment divergence;
- form and test causal hypotheses;
- decide whether the frozen plan itself is invalid.

Not allowed:

- continue feature development;
- stack another point-fix without an established cause;
- start a new workaround branch to avoid understanding the current state.

### 3. Use finite stop conditions

Recommended defaults unless the project explicitly defines stricter rules before execution:

- two sequential failed correction attempts of the same class against materially comparable states;
- two repeated failures of the same tool/process operation without new evidence;
- authoritative working state diverges from intended/reviewed/tested state;
- acceptance requires changing a declared non-goal;
- a dependency contract is missing or contradictory;
- the proposed fix requires guessing which source of truth is authoritative;
- correctness or security cannot be established inside frozen scope.

A different error after a real change is not automatically the same failure class. Classify before counting.

### 4. Handle new findings without scope leakage

Classify every discovery:

```text
belongs to frozen correctness
→ fix here

directly blocks frozen correctness/security
→ record as blocker and resolve here

adjacent but non-blocking
→ record separately; do not fix here
```

Do not reward discovery with automatic scope expansion.

### 5. Resume only after the stop condition is resolved

A Causal Audit ends with one of:

- root cause established; return to Execution with a bounded correction;
- scope assumption disproved; explicitly replan/refreeze;
- dependency or upstream defect identified; stop current implementation and hand off;
- environmental/tool failure established; use a different verified execution path;
- task is blocked or invalid; record that instead of manufacturing progress.

## Decision rules

- **New evidence before new code.** Repeated code changes without changed evidence are a loop.
- **One workstream, one authoritative state.** Do not escape a confusing branch by spawning another untracked branch.
- **Scope changes are governance events.** They are not implementation details.
- **Partial completion is a valid result.** Hiding a blocker is not.
- **A stop condition is not failure.** Ignoring one is.

## Anti-patterns

Avoid:

- third/fourth/fifth point-fix because the previous fix was "close";
- rewriting tests to match accidental behavior;
- deleting checks to obtain green CI;
- creating multiple PRs for the same unresolved branch state;
- mixing root-cause investigation with speculative implementation;
- fixing every issue noticed while reading nearby code;
- declaring a tool flaky without bounding the repeated failure;
- treating a new chat/session as a reset of technical state.

## Verification checklist

- [ ] Objective and scope are explicit.
- [ ] Non-goals exist for meaningful adjacent work.
- [ ] Current mode is unambiguous.
- [ ] Stop conditions are finite.
- [ ] Repeated failures have not been converted into repeated guesses.
- [ ] Out-of-scope findings are recorded, not silently implemented.
- [ ] If Causal Audit occurred, the cause or replan decision is recorded before execution resumed.

## Pair with

- `implementation-planning` to create the frozen workstream;
- `systematic-debugging` to perform technical causal diagnosis;
- `authority-mapping` when the cause involves competing sources of truth;
- `exact-state-verification` when state/provenance divergence is suspected;
- `proof-loop-verification` before declaring the workstream complete.
