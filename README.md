# Codex Playbook

This repository contains a practical Codex playbook focused on safe code changes, branch integrity, handoffs, checkpoints, durable project context, reusable design contracts, systematic debugging, and review workflows for agent-driven software work.

## Structure

- `AGENTS.md` - root operating rules for Codex
- `SKILLS_INDEX.md` - progressive skill discovery layer
- `.agents/skills/` - on-demand skills for recurring workflows
- `templates/` - reusable state, evidence, QA, spike, and design templates
- `.codex/` - local Codex config placeholders

## Goals

- reduce accidental code overwrite
- preserve branch provenance
- make merge drift visible
- require evidence before declaring work complete
- keep durable session handoffs and project history
- prevent random UI styling by using explicit `DESIGN.md` contracts
- debug from root cause instead of guess-and-patch workflows
- separate spikes from production implementation
- make QA and merge review operational instead of performative

## Core skills

- proof loop verification
- git branch integrity
- session handoff
- project chronicle
- merge preview check
- design system authoring

## Hermes-inspired additions

- skill authoring
- systematic debugging
- pre-merge review
- spike prototyping
- webapp dogfood QA
- implementation planning

## Important design rule

Do not load the whole playbook into every task.

Use:

1. `SKILLS_INDEX.md`
2. the smallest useful skill
3. supporting templates only when required

This keeps context small and workflows explicit.

Adapt per repository instead of dumping everything into one giant prompt.
