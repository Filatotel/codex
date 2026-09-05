# Workflow: Manage Production-Time Canon Change

**Workflow ID:** `manage_production_canon_change`

## Role contract

- executing_role: `roles/executor/ROLE.md`
- consuming_role: `roles/control-director/ROLE.md`
- required_skills:
  - `engines/canon/skills/classify-canon-change/SKILL.md`
  - `engines/canon/skills/validate-canon/SKILL.md`

Production observations may expose a Canon gap. Software or production execution cannot self-certify Canon truth.

## Procedure

1. Lock current Canon version, production state and exact observed signal.
2. Run `classify-canon-change`.
3. Emit an envelope-compatible `CANON_CHANGE_PROPOSAL` with impacted Canon refs, evidence refs, requested authority and downstream revalidation.
4. Apply A/B/C/D gate semantics conservatively; C pauses affected production and D is a controlled authority stop.
5. No accepted mutation occurs without explicit Canon authority.
6. Run mandatory `validate-canon` on any authorized resulting Canon candidate.
7. Return exact changed/unchanged state and revalidation obligations to the Control Director.

## Stop

No class permits mutating Canon merely to match code, a bug, draft, translation, test, or convenient implementation.
