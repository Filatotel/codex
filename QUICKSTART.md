# Quickstart

## 1. Use this repo as a pattern library

Do not paste everything into one permanent prompt.
Copy only the layers you actually need.

Start with:

1. `AGENTS.md`;
2. `SKILLS_INDEX.md`;
3. the smallest useful skill for the current decision/work phase.

## 2. Minimum recommended setup in a working project

- copy/adapt `AGENTS.md`;
- copy the core skills your project actually needs;
- copy specialist skills/templates only when they will be maintained;
- adapt `.codex/hooks.example.json` into local Codex hooks when useful.

## 3. Best first skills to adopt

For almost any agent-driven repository:

- `implementation-planning`;
- `anti-loop-execution`;
- `git-branch-integrity`;
- `proof-loop-verification`.

Add these when the project has the corresponding complexity:

- `authority-mapping` — several components can disagree about state;
- `dependency-ownership` — multiple workstreams/providers/consumers;
- `exact-state-verification` — CI/review/release evidence depends on precise revisions;
- `irreversible-boundary-reasoning` — retries may cross non-repeatable effects;
- `evidence-and-authority` — machine checks, semantic review, and release decisions must stay distinct.

For debugging-heavy projects:

- `systematic-debugging`;
- `pre-merge-review`.

For UI-heavy projects:

- `design-system-authoring`;
- `webapp-dogfood-qa`.

For experimental or architecture-heavy projects:

- `spike-prototyping`;
- `implementation-planning`;
- `authority-mapping` as needed.

## 4. Recommended workflow

### Before non-trivial implementation

1. `implementation-planning` — define owner/scope/non-goals/dependencies/gates/stop conditions.
2. `dependency-ownership` or `authority-mapping` only if those boundaries are genuinely complex.
3. Freeze the workstream.
4. `anti-loop-execution` governs execution from this point.

### During ordinary execution

Stay in EXECUTION MODE and implement frozen scope.
Record non-blocking adjacent findings instead of fixing them automatically.

### When execution repeats the same failure class

1. Stop point-fixing.
2. Enter CAUSAL AUDIT MODE through `anti-loop-execution`.
3. Use `systematic-debugging` for the technical diagnosis.
4. Re-check exact state and authority assumptions if relevant.
5. Resume implementation only after cause/replan is established.

### Before merge

- `git-branch-integrity`;
- `exact-state-verification` when evidence/HEAD identity matters;
- `pre-merge-review`;
- `merge-preview-check`;
- `proof-loop-verification`.

### Before calling UI done

- `webapp-dogfood-qa`;
- mechanical tests plus human/semantic checks appropriate to the product;
- use `evidence-and-authority` if those checks are being used for a consequential acceptance decision.

## 5. Core principles are not architecture recipes

Do not translate a core rule into an arbitrary technology mandate.

Example:

```text
Core principle:
identify authority for a shared fact.

Not implied:
"the server must always own it."
```

Example:

```text
Core principle:
identify an irreversible boundary before retry design.

Not implied:
"every workflow must use an outbox."
```

Specific implementations belong to optional **Solution Patterns**, where assumptions, trade-offs, alternatives, and failure modes must be explicit.

## 6. Best first templates to adopt

- `BRANCH_STATE.md`;
- `HANDOFF.md`;
- `TASK_EVIDENCE.md`.

For UI-heavy projects:

- `DESIGN.md`;
- `QA_REPORT.md`.

For architecture experiments:

- `SPIKE_REPORT.md`.

## 7. Important rule

This repository is not the source of truth for a product codebase.
Each product repository keeps its own current contracts, authoritative state, plans, and evidence.
The playbook supplies reusable reasoning and workflows; the product repo decides its architecture.
