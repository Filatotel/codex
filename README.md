# Project Resolver

This repository is being migrated from the standalone **Codex Software Playbook** into a modular monorepo for a **Project Resolver / Agent Project Operating System**.

The system is intended to carry a project through a state graph that can include Canon Foundation, Research, reconciliation, Production Foundation, Production, Verification, final reconciliation, and post-production work. Those lifecycle stages are not all materialized yet.

## Runtime entry

A fresh Liaison starts at `BOOTSTRAP.md`. It recognizes SBC only from an explicitly supplied `SBC_RUNTIME_CONTEXT`; otherwise it continues in ordinary ChatGPT Web mode.

After bootstrap, ordinary agents use progressive disclosure:

```text
AGENTS.md
→ SYSTEM_MANIFEST.yaml
→ ROUTER.md
→ selected Engine manifest
→ selected Workflow / Role
→ bounded Skill namespace
```

Ordinary execution does not scan the whole skill library. Final SBC/PAK transport is not required for this manual bootstrap path.

## Current materialized engines

The authoritative runtime registry is `SYSTEM_MANIFEST.yaml`. On the current `main`, these engines are available:

- **Foundation** — non-authoritative project formation, working outcome/unknowns and semantic topology bootstrap under `engines/foundation/`; its workflow stops before the Owner Foundation Gate.
- **Canon** — governed Canon formation, reconciliation, validation, freeze and change management under `engines/canon/`. This does **not** grant agents Owner/Canon mutation authority.
- **Production / Software** — bounded engineering, implementation and review under `engines/production/software/`.
- **Verification** — independent claim verification with shared exact-state and evidence contracts under `engines/verification/`. A technical PASS alone does not prove alignment with the approved business outcome or target architecture.
- **Research** — machine-only research admission, execution contracts and reconciliation under `engines/research/`.

Foundation V0 and the reference Project Topology implementation were merged in [PR #98](https://github.com/Filatotel/codex/pull/98). `foundation` is registered as `available`, so route `form_project_foundation` through its manifest and workflow when project formation is actually requested. This availability does **not** prove live GitHub/Drive provider realization, concurrent-writer safety, or completion of all [Issue #53](https://github.com/Filatotel/codex/issues/53) acceptance criteria. Those claims require separate evidence. Other production-domain engines remain deferred.

To select a capability, load only the registered engine and required workflow/skills, never the full historical skill index.

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

## Historical migration boundary and ongoing work

The original Wave 1 migrated the legacy Codex Software Playbook into bounded namespaces. Later work materialized Canon, Research, independent Verification, Owner Interface and controlled execution/transition contracts. **The original Wave 1 exclusions are historical, not a description of what `main` lacks today.**

Current outstanding work is tracked in [Issue #53](https://github.com/Filatotel/codex/issues/53) (Foundation + Topology), [Issue #61](https://github.com/Filatotel/codex/issues/61) (Architecture Health; the risk-tiered target-alignment slice was merged in #101), and [Issue #77](https://github.com/Filatotel/codex/issues/77) (V0 manual operation; SBC Browser/PAK transport deferred).

`ARCHITECTURE_MIGRATION_MAP.md` and `CANON_ENGINE_MIGRATION_MAP.md` are historical migration-accounting records, **not** live routing or implementation authority. Use the current manifest, Router, applicable Issue and approved Canon/Owner decisions for active work.
