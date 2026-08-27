# Codex Playbook

This repository contains a practical Codex playbook for safe, bounded, evidence-driven software work across different stacks and project types.

The playbook has two intentionally different knowledge layers:

1. **Core engineering principles** — architecture-neutral rules for planning, authority, dependency ownership, anti-loop execution, exact-state evidence, irreversible boundaries, and acceptance.
2. **Solution patterns** — optional implementation recipes for narrower technical problem classes. A successful pattern is never treated as the mandatory architecture for every project.

## Structure

- `AGENTS.md` — root operating rules for Codex;
- `SKILLS_INDEX.md` — progressive skill discovery layer;
- `.agents/skills/` — on-demand skills for recurring workflows;
- `templates/` — reusable state, evidence, QA, spike, and design templates;
- `.codex/` — local Codex config placeholders.

## Goals

- stop guess-and-patch execution loops;
- freeze non-trivial workstreams before implementation;
- make decision/source-of-truth ownership explicit;
- prevent accidental dependency/coordination cycles;
- preserve branch and artifact provenance;
- bind evidence to the exact state that produced it;
- reason correctly about retry/recovery around irreversible effects;
- distinguish mechanical checks, engineering judgment, and acceptance authority;
- require evidence before declaring work complete;
- keep durable session handoffs and project history;
- debug from root cause instead of repeated patching;
- separate spikes from production implementation;
- make QA and merge review operational instead of performative;
- preserve the freedom to choose different technical solutions when project assumptions differ.

## Core engineering principles

- `anti-loop-execution`
- `authority-mapping`
- `dependency-ownership`
- `exact-state-verification`
- `irreversible-boundary-reasoning`
- `evidence-and-authority`

These skills describe **how to reason and execute**, not which database, cloud, frontend framework, telemetry architecture, state model, or provider to select.

## Core execution/support skills

- `implementation-planning`
- `systematic-debugging`
- `git-branch-integrity`
- `proof-loop-verification`
- `pre-merge-review`
- `merge-preview-check`
- `session-handoff`
- `project-chronicle`

## Design, QA, audit, and documentation

- `design-system-authoring`
- `webapp-dogfood-qa`
- `playwright-dogfood-harness`
- `operational-auditing`
- `docs-assembly`
- `spike-prototyping`
- `skill-authoring`
- `laravel-contract-first`

## Core principle vs solution pattern

A core principle may say:

> Identify the irreversible boundary before designing retries.

A solution pattern may say:

> Under assumptions A/B/C, an idempotency key + durable outbox is one proven way to make retries safe.

The first is broadly applicable reasoning discipline. The second is a selectable technical design with assumptions and trade-offs.

This distinction is deliberate: the playbook should become smarter from prior projects without trapping future projects inside prior architecture.

## Important loading rule

Do not load the whole playbook into every task.

Use:

1. `SKILLS_INDEX.md`;
2. the smallest useful skill that owns the current decision;
3. paired skills only when a real boundary is crossed;
4. supporting templates only when required.

This keeps context small and workflows explicit.

Adapt the playbook per repository instead of dumping everything into one giant permanent prompt.
