# Skill Authoring

## Purpose

Use this skill when creating or editing reusable playbook skills in `.agents/skills/`.

## Goal

Keep the playbook useful, small, and operational. A skill should teach an agent how to do one recurring workflow with evidence, not dump generic advice.

## When to use

Use this skill when:

- adding a new skill
- editing an existing skill
- deciding whether a workflow should become a skill
- creating templates or references that support a skill

Do not use this skill for one-off project notes, task evidence, or product-specific docs that do not belong in the reusable playbook.

## Skill or template

| Need | Best artifact |
|---|---|
| Reusable procedure | `SKILL.md` |
| Reusable output shape | `templates/*.md` |
| Current task state | copied template in product repo |
| Long-term project decision | project chronicle |
| Temporary experiment result | spike report |

## Required shape

Every skill should include:

- Purpose
- Goal
- When to use
- Inputs
- Required outputs
- Procedure
- Anti-patterns
- Verification checklist or minimal verdict format

Optional sections:

- Decision table
- Quick reference
- Escalation rules
- Pair with other skills
- Output template

## Naming rules

- Use lowercase directory names.
- Use hyphens between words.
- Prefer workflow names over tool names.
- Avoid broad names like `frontend`, `backend`, or `misc`.
- Do not create a new skill if an existing skill can be tightened.

Good:

- `systematic-debugging`
- `pre-merge-review`
- `webapp-dogfood-qa`

Bad:

- `coding`
- `do-better-ui`
- `everything-about-react`

## Procedure

1. Check `SKILLS_INDEX.md` to avoid duplication.
2. Read the closest existing skill for tone and structure.
3. Decide whether the workflow is reusable enough to become a skill.
4. Start from `templates/SKILL_TEMPLATE.md` when creating a new skill.
5. Keep the skill focused on procedure, decisions, evidence, and failure modes.
6. Add supporting templates only when they will actually be reused.
7. Update `SKILLS_INDEX.md`, `AGENTS.md`, `README.md`, and `QUICKSTART.md` when the new skill should be discoverable.
8. Verify the new skill does not encourage unrelated rewrites or vague completion claims.

## Good skill properties

| Property | Meaning |
|---|---|
| Triggered | The agent knows when to load it |
| Actionable | It tells the agent what to do, not just what to value |
| Bounded | It does one workflow, not every workflow |
| Evidence-based | It requires observable output or verification |
| Portable | It can be copied into product repos with minimal edits |
| Short | It avoids becoming a giant prompt dump |

## Anti-patterns

Avoid:

- copying large external skills verbatim
- adding tool-specific instructions that will go stale quickly
- mixing product strategy, implementation, and QA in one skill
- creating overlapping skills with different names
- adding scripts or templates that no one will maintain
- saying a skill is complete without updating the index

## Verification checklist

- [ ] The skill has a clear trigger.
- [ ] It does not duplicate an existing skill.
- [ ] It has required outputs.
- [ ] It has anti-patterns or failure modes.
- [ ] It is concise enough for on-demand loading.
- [ ] Related templates or index entries were updated if needed.

## Minimal verdict format

- Status
- Skill created or edited
- Why it belongs in the playbook
- Files changed
- Discovery updates
- Risks
