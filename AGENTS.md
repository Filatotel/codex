# AGENTS.md

This repository is a reusable Codex playbook.

## Purpose

Use this repository as a source of practical operating rules for Codex-driven software work.
The priority is not verbosity. The priority is safe execution, branch integrity, durable context, and verifiable completion.

## Core operating rules

1. Never claim a task is complete without evidence.
2. Prefer small, reviewable changes over large rewrites.
3. Do not overwrite or delete unrelated code to make a local task pass.
4. Record branch provenance before major edits.
5. Treat merge drift as a first-class risk.
6. Keep durable handoff state in files, not only in chat history.
7. Separate tactical handoff from long-term project history.
8. When uncertain, preserve information rather than compressing it away.

## Branch integrity minimum

Before substantial work, capture:

- current branch
- target branch
- base commit SHA
- merge base with target branch
- intended scope
- touched files

Before final sign-off, verify:

- diff still matches intended scope
- target branch has not invalidated the work
- evidence exists for the current branch state
- merge or rebase risk has been checked

## Durable artifacts

Useful artifacts include:

- task evidence
- session handoff
- branch state
- merge preview notes
- project chronicle

Templates live in `templates/`.
Skills live in `.agents/skills/`.

## Skills in this repository

- `proof-loop-verification`
- `git-branch-integrity`
- `session-handoff`
- `project-chronicle`
- `merge-preview-check`

## Authoring guidance

Keep files concise.
Prefer checklists and decision rules over long essays.
Do not turn this repository into a giant generic prompt dump.
