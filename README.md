# Codex Playbook

This repository contains a practical Codex playbook focused on safe code changes, branch integrity, handoffs, checkpoints, durable project context, and reusable design contracts for agent-driven UI work.

## Structure

- `AGENTS.md` - root operating rules for Codex
- `.agents/skills/` - on-demand skills for recurring workflows
- `templates/` - reusable state, evidence, and design contract templates
- `.codex/` - local Codex config placeholders

## Goals

- reduce accidental code overwrite
- preserve branch provenance
- make merge drift visible
- require evidence before declaring work complete
- keep durable session handoffs and project history
- prevent random UI styling by using explicit `DESIGN.md` contracts

## Initial skills

- proof loop verification
- git branch integrity
- session handoff
- project chronicle
- merge preview check
- design system authoring

Adapt per repository instead of dumping everything into one giant prompt.
