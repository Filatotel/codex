# Project Resolver

This repository is being migrated from the standalone **Codex Software Playbook** into a modular monorepo for a **Project Resolver / Agent Project Operating System**.

The system is intended to carry a project through a state graph that can include Canon Foundation, Research, reconciliation, Production Foundation, Production, Verification, final reconciliation, and post-production work. Those lifecycle stages are not all materialized yet.

## Runtime entry

Ordinary agents use progressive disclosure:

```text
AGENTS.md
→ SYSTEM_MANIFEST.yaml
→ ROUTER.md
→ selected Engine manifest
→ selected Workflow / Role
→ bounded Skill namespace
```

Ordinary execution does not scan the whole skill library.

## Current materialized engines

- **Production / Software** — the accepted Codex engineering knowledge, now bounded under `engines/production/software/`.
- **Verification** — independent completion-claim verification using shared exact-state and evidence contracts.

Canon, Research, Foundation, and other production-domain engines are explicitly planned but **not materialized** in this wave. The Canon Engine is expected to arrive through a separate migration wave rather than being improvised here.

## Shared system layer

- `kernel/` — cross-engine control reasoning primitives.
- `contracts/` — definitions and authority boundaries for state, roles, artifacts, evidence, assignments, gates, and mutations.
- `protocols/` — context assembly, artifacts, handoff, and controlled state-change procedures.
- `roles/` — durable role contracts. Agents are temporary instances of these roles.
- `schemas/` — lightweight machine-readable role-native artifact schemas.
- `library/` — reusable skill-library maintenance, not ordinary project execution.

## Software migration

Legacy Codex remains valuable. Accepted engineering skills and production-derived Solution Patterns are preserved rather than rewritten wholesale. Software-specific material lives under the Software Engine; cross-engine primitives are extracted to shared ownership; historical root material is retained under `archive/legacy-codex/` where its semantic value matters.

A **Core Principle is not a Solution Pattern**. Core reasoning laws stay broad; Solution Patterns remain optional, assumption-bound technical recipes with rejection conditions, alternatives, and trade-offs.

## State and evidence

Canonical project state must survive in durable artifacts, not chat history. An artifact can carry a result or claim, but `ARTIFACT != EVIDENCE`: evidence must independently support the claim. Execution and verification outputs therefore remain separate, and authority controls whether state actually changes.

## Migration scope

Wave 1 creates the structural baseline only. It does not import the Canon repository, author Research/Foundation engines, implement the proposed capability waves in issues #23/#24, build a full autonomous scheduler, rename the repository, or turn technology-specific patterns into system architecture.

See `ARCHITECTURE_MIGRATION_MAP.md` for exact legacy accounting and migration ownership.
