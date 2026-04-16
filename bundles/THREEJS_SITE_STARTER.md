# Three.js Site Starter Bundle

Use this bundle for a new visual-heavy site such as OneMoreBar.

## Copy these files first

### Always copy

- `AGENTS.md`
- `.agents/skills/git-branch-integrity/SKILL.md`
- `.agents/skills/proof-loop-verification/SKILL.md`
- `.agents/skills/session-handoff/SKILL.md`
- `templates/BRANCH_STATE.md`
- `templates/HANDOFF.md`
- `templates/TASK_EVIDENCE.md`
- `PRODUCT_REPO_RULES.md`

### Copy for longer or riskier projects

- `.agents/skills/project-chronicle/SKILL.md`
- `.agents/skills/merge-preview-check/SKILL.md`
- `templates/PROJECT_CHRONICLE.md`
- `templates/MERGE_PREVIEW.md`
- `scripts/validate_state.py`
- `scripts/check_branch_integrity.py`

## Why this bundle fits Three.js sites

Three.js or animation-heavy sites often have:

- many iterative visual changes
- easy accidental regressions
- bigger diffs than expected
- moving assumptions about assets, performance, and interaction

This bundle helps keep:

- change scope visible
- handoff state durable
- branch drift visible
- completion tied to evidence instead of visual optimism

## Practical note

Do not copy the entire playbook blindly.
Start with the minimum set, then add chronicle and merge-preview support if the project becomes long-running or multi-session.
