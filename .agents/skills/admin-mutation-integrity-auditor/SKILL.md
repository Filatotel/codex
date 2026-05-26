# Admin Mutation Integrity Auditor

## Purpose

Use this skill when a change adds or edits admin create, update, enable, disable, archive, duplicate, reorder, or settings endpoints.

## Goal

Prevent false success, orphan rows, inconsistent final state, and unsafe admin controls. Admin mutation endpoints must prove the target exists, the parent exists, the requested change is allowed, and the final state still satisfies business invariants.

## When to use

Use this skill when a task touches:

- settings pages or manager UIs
- admin CRUD endpoints
- enable, disable, archive, or restore actions
- primary or default selection logic
- nested resources such as site, app, and origin
- template, routing, provider, user, task, lead, queue, or automation settings
- audit logging for admin actions

## Inputs

Collect:

- mutation routes
- target tables or records
- parent-child relationships
- unique or primary/default constraints
- immutable fields
- final-state invariants
- audit requirements
- validation error shape

## Integrity checklist

| Area | Required check |
|---|---|
| Target existence | PATCH or disable must not return success for a missing row. |
| Parent existence | Child create must verify parent exists. |
| Row effect | No false success on no-op updates unless no-op is explicit. |
| Immutable fields | Keys, IDs, owner fields, and source fields are not casually mutable. |
| Uniqueness | Unique conflicts return validation errors, not raw SQL. |
| Final state | Disabled primary, duplicate default, or orphan state cannot remain. |
| Retained records | Prefer archive or disable; hard removal needs explicit approval. |
| Audit | Sensitive changes are logged without blocking unless required. |
| Error shape | User receives field-level validation, not stack traces. |

## Procedure

1. List every mutation endpoint changed by the PR.
2. For each create route, verify parent existence and uniqueness checks.
3. For each patch route, verify target existence before update.
4. For each enable or disable route, verify final-state invariants.
5. For each default or primary route, verify previous defaults are unset.
6. For each immutable field, verify it is rejected or ignored by contract with clear behavior.
7. Verify update helpers can distinguish not found from successful update.
8. Verify user-facing errors are mapped to stable field keys.
9. Verify audit logging exists for operationally meaningful changes.
10. Check UI copy: use Disable or Archive when records are retained.

## Common failures

- PATCH returns success for a missing ID.
- child create inserts with a typoed parent ID.
- disabling a primary item leaves it primary.
- setting a new default does not unset the old default.
- duplicate key raises a raw SQL error.
- UI sends immutable fields copied from a detail DTO.
- audit logs claim a change happened when no row changed.

## Blockers

Treat these as blocking:

- mutation can create orphan records
- mutation can report success when the target does not exist
- final state can violate primary, default, unique, or ownership invariants
- retained-record policy is bypassed without explicit product approval
- raw backend exception can reach admin UI for normal validation failure

## Required output

```md
## Admin mutation integrity audit

- Status: pass / partial / fail
- Routes checked:
- Parent checks:
- Target checks:
- Final-state invariants:
- Immutable fields:
- Validation shape:
- Audit behavior:
- Required fixes:
- Regression test or smoke suggestion:
```

## Pair with

- `contract-drift-auditor`
- `admin-ui-resilience-auditor`
- `codex-pr-workflow-guard`
