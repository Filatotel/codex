# Product Repository Rules

Copy or adapt these rules into the real product repository.

## Workflow infrastructure protection

Treat workflow files as project infrastructure, not disposable task output.
Do not delete, rename, or rewrite workflow files unless the task explicitly targets playbook maintenance.

This includes:

- `AGENTS.md`
- files under `.agents/skills/`
- workflow scripts under `scripts/`
- durable templates kept for active project use

Before removing any workflow or state file, explain whether it is:

- durable infrastructure
- temporary task state
- finished evidence no longer needed

## Product repository rules block

You can paste this directly into a product repo `AGENTS.md`:

```md
Treat workflow files as project infrastructure, not disposable task output.
Do not delete, rename, or rewrite workflow files unless the task explicitly targets playbook maintenance.
This includes AGENTS.md, files under .agents/skills/, workflow scripts under scripts/, and durable templates kept for active project use.
Before removing any workflow or state file, explain whether it is durable infrastructure, temporary task state, or finished evidence no longer needed.
The product repository is the single source of truth.
```
