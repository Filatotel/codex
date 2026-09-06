# Workflow: Reopen Canon

**Workflow ID:** `reopen_canon`

## Role contract

- executing_role: `roles/executor/ROLE.md`
- consuming_role: `roles/control-director/ROLE.md`
- required_skills:
  - `engines/canon/skills/reopen-canon/SKILL.md`
- optional_skills:
  - `engines/canon/skills/validate-canon/SKILL.md`

## Entry

Exact frozen Canon ref, explicit reopen authority, reason, impact scope and post-2.0 lifecycle mode when applicable are required.

## Procedure

1. Run `reopen-canon` against the exact frozen state and authority.
2. Preserve historical frozen state; create a new version lineage rather than rewriting history.
3. Record prior ref, reason/evidence, scope, downstream impact and revalidation obligations.
4. Route substantive changes through normal Canon registration/reconciliation/change-classification workflows.
5. Validate/freeze the new lineage only in a later separately authorized gate.

## Stop

No silent retcon, history rewrite, or authority inference from edit access.
