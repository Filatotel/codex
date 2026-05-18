# Skills Index

Use this index before loading full skill files.
The goal is progressive disclosure: choose the smallest useful skill instead of reading the whole playbook.

## Core skills

| Skill | Use when | Main output | Pair with |
|---|---|---|---|
| `git-branch-integrity` | Starting or finishing branch work | Branch provenance and merge risk notes | `merge-preview-check` |
| `proof-loop-verification` | Claiming work is done | Task evidence and pass/partial/fail verdict | Any implementation skill |
| `session-handoff` | Ending a work session | Tactical continuation notes | `project-chronicle` |
| `project-chronicle` | Recording long-term decisions | Durable project history entry | `session-handoff` |
| `merge-preview-check` | Before merge or ready-for-review claim | Integration risk verdict | `git-branch-integrity` |
| `design-system-authoring` | UI work or DESIGN.md creation | Design contract and visual QA note | `webapp-dogfood-qa` |

## Hermes-inspired additions

| Skill | Use when | Main output | Pair with |
|---|---|---|---|
| `skill-authoring` | Creating or editing playbook skills | Well-structured SKILL.md | `proof-loop-verification` |
| `systematic-debugging` | Build, runtime, API, UI, deploy, or integration bugs | Root cause and minimal fix path | `proof-loop-verification` |
| `pre-merge-review` | Before PR, merge, or deployment | Risk-focused review verdict | `merge-preview-check` |
| `spike-prototyping` | Testing an uncertain idea before production work | Spike report with validated/partial/invalidated verdict | `implementation-planning` when promoted |
| `webapp-dogfood-qa` | Checking a web app, landing page, admin, menu, or calculator | QA report with evidence and severity | `design-system-authoring` |
| `implementation-planning` | Multi-step feature or refactor | Exact scoped implementation plan | `pre-merge-review` |

## Selection rules

1. For a bug, load `systematic-debugging` first, not implementation planning.
2. For a UI task, load `design-system-authoring` first, then `webapp-dogfood-qa` before sign-off.
3. For uncertain architecture or UX ideas, run a spike before production implementation.
4. Before merge, use `pre-merge-review`, then `merge-preview-check`, then `proof-loop-verification`.
5. When adding a new workflow, use `skill-authoring` and keep it short.

## Do not load everything

Load only the skills needed for the current task.
If a task touches code, UI, and deployment, load at most one skill per phase:

- planning phase
- implementation phase
- review phase
- handoff phase
