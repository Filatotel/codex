# Implementation Planning

## Purpose

Use this skill before multi-step implementation, risky refactors, migrations, integrations, or delegated execution.

## Goal

Create a bounded, verifiable workstream that can be frozen before implementation and executed without hidden scope expansion.

This skill owns **planning the workstream**. `anti-loop-execution` owns execution mode and stop-condition behavior after the plan is frozen.

## When to use

Use when:

- a feature touches multiple files or systems;
- deployment or migration risk exists;
- UI, API, data, infrastructure, or external services interact;
- another agent or future session will continue the work;
- the implementation path has meaningful dependencies;
- a task needs explicit acceptance/release gates.

Do not use this skill for tiny single-file edits where ownership, dependency, and rollback questions are trivial.

## Inputs

- requested outcome;
- current repository/system state;
- relevant contracts and existing implementation;
- likely dependencies and owners;
- known risks;
- available verification paths.

## Required outputs

A plan should include:

- objective;
- owner;
- scope;
- non-goals;
- dependencies and dependency type;
- likely files/systems touched;
- high-risk areas;
- implementation phases;
- acceptance criteria;
- gates;
- stop conditions;
- verification commands/checks;
- rollback/recovery notes where relevant;
- deferred-findings location.

## Procedure

### 1. Define the objective

One or two sentences describing the observable outcome.

Do not encode an implementation choice as the objective unless the implementation itself is the requirement.

### 2. Assign ownership

Record the workstream owner and any shared decision surfaces it consumes from other owners.

If ownership is ambiguous, resolve it or use `dependency-ownership` before implementation.

### 3. Define scope and non-goals

List:

- systems touched;
- files/directories likely touched;
- contracts that may change;
- what explicitly must not change.

Non-goals are especially important when adjacent architecture is tempting to clean up.

### 4. Map dependencies

Classify meaningful dependencies as:

- hard implementation;
- contract;
- release;
- verification;
- informational.

Do not block work on a downstream implementation when a stable provider contract/fixture is sufficient.

### 5. Identify risks

Examples:

- merge drift;
- shared-schema ownership;
- external provider dependency;
- irreversible side effect;
- compatibility with persisted state;
- concurrency/stale-client behavior;
- deployment/config mismatch;
- mobile/accessibility regression;
- generated-artifact drift.

Use project-specific risks rather than copying this list mechanically.

### 6. Split into bounded phases

Good phase boundaries correspond to independently understandable outputs or proof gates.

Examples:

- contract/discovery;
- implementation slice;
- migration/data transition;
- integration;
- verification;
- deployment;
- human/operational QA.

Avoid giant phases such as "implement everything".

### 7. Define acceptance criteria

Use observable outcomes.

Bad:

```text
Architecture improved.
```

Good:

```text
Every writer preserves fields it does not own and stale revisions are rejected by the declared conflict rule.
```

### 8. Define gates

A gate is evidence or authority required before the workstream may advance or close.

Examples:

- contract/schema accepted;
- exact candidate tests green;
- migration replay verified;
- browser/device QA complete;
- upstream dependency accepted;
- release authority explicitly granted.

Do not make green CI the universal gate for semantic/product decisions.

### 9. Define stop conditions

A plan without stop conditions encourages loops.

Include conditions such as:

- same-class corrections repeatedly fail;
- authoritative state becomes ambiguous;
- required scope crosses a non-goal;
- dependency contract is contradictory;
- irreversible effect cannot be recovered safely;
- exact tested/reviewed state diverges from working state.

Execution behavior after a stop condition is owned by `anti-loop-execution`.

### 10. Define verification

Prefer exact commands/checks where known, plus concrete manual/semantic checks where machines cannot prove the criterion.

Tie important evidence to the exact candidate using `exact-state-verification`.

### 11. Freeze the plan

Before substantial implementation, record the plan as the current workstream contract.

If scope must change later, explicitly replan/refreeze rather than letting implementation silently redefine the task.

### 12. Record deferred findings

Choose where non-blocking discoveries go: issue, backlog, audit note, TODO registry, or another durable artifact.

Do not fix them inside the frozen workstream merely because they were noticed.

## Anti-patterns

Avoid:

- vague architecture plans;
- scope defined only by a list of files;
- no owner for shared state/contracts;
- every relationship marked as a hard dependency;
- giant rewrite phases;
- hidden scope expansion during implementation;
- no rollback/recovery notes for irreversible changes;
- plans that assume chat-only context;
- verification that depends only on confidence;
- no explicit point at which implementation must stop and audit assumptions.

## Minimal plan structure

```md
# Objective
# Owner
# Scope
# Non-goals
# Dependencies
# Risks
# Phases
# Acceptance criteria
# Gates
# Stop conditions
# Verification
# Rollback / recovery
# Deferred findings
```

## Pair with

- `dependency-ownership` for multi-workstream DAGs;
- `authority-mapping` for shared decision ownership;
- `anti-loop-execution` after the plan is frozen;
- `irreversible-boundary-reasoning` for non-repeatable effects;
- `proof-loop-verification` for completion.
