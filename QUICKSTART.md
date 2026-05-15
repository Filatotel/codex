# Quickstart

## 1. Use this repo as a pattern library

Do not paste everything into one permanent prompt.
Copy only the layers you actually need.

## 2. Minimum recommended setup in a working project

- copy `AGENTS.md` and adapt it to the repository
- copy one or more skills from `.agents/skills/`
- copy templates you want to maintain in-project
- adapt `.codex/hooks.example.json` into local Codex hooks

## 3. Best first skills to adopt

- git-branch-integrity
- proof-loop-verification
- session-handoff

For UI-heavy projects, also adopt:

- design-system-authoring

## 4. Best first templates to adopt

- BRANCH_STATE.md
- HANDOFF.md
- TASK_EVIDENCE.md

For UI-heavy projects, also adopt:

- DESIGN.md

## 5. Important rule

This repository is not the source of truth for a product codebase.
Each product repository should keep its own AGENTS.md and its own current state files.
Each UI-heavy product repository should keep its own project-specific DESIGN.md.
