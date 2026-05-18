# Quickstart

## 1. Use this repo as a pattern library

Do not paste everything into one permanent prompt.
Copy only the layers you actually need.

Start with:

1. `AGENTS.md`
2. `SKILLS_INDEX.md`
3. only the smallest useful skill for the current phase

## 2. Minimum recommended setup in a working project

- copy `AGENTS.md` and adapt it to the repository
- copy one or more skills from `.agents/skills/`
- copy templates you want to maintain in-project
- adapt `.codex/hooks.example.json` into local Codex hooks

## 3. Best first skills to adopt

- git-branch-integrity
- proof-loop-verification
- session-handoff

For debugging-heavy projects, also adopt:

- systematic-debugging
- pre-merge-review

For UI-heavy projects, also adopt:

- design-system-authoring
- webapp-dogfood-qa

For experimental or architecture-heavy projects, also adopt:

- spike-prototyping
- implementation-planning

## 4. Best first templates to adopt

- BRANCH_STATE.md
- HANDOFF.md
- TASK_EVIDENCE.md

For UI-heavy projects:

- DESIGN.md
- QA_REPORT.md

For architecture experiments:

- SPIKE_REPORT.md

## 5. Recommended workflow

### Before implementation

- git-branch-integrity
- implementation-planning if scope is non-trivial

### During debugging

- systematic-debugging

### Before merge

- pre-merge-review
- merge-preview-check
- proof-loop-verification

### Before calling UI done

- webapp-dogfood-qa

## 6. Important rule

This repository is not the source of truth for a product codebase.
Each product repository should keep its own AGENTS.md and its own current state files.
Each UI-heavy product repository should keep its own project-specific DESIGN.md.
