# Contract Drift Auditor

## Purpose

Use this skill when a change touches data contracts across database rows, API responses, frontend types, forms, exports, previews, or diagnostics.

## Goal

Prevent silent drift between the source of truth and the surfaces that consume it.

## When to use

Use this skill when a task touches:

- migrations, SQL joins, selected columns, or aliases
- presenters, serializers, resources, or DTOs
- frontend API clients or TypeScript interfaces
- admin list, detail, settings, or manager pages
- form payloads, PATCH bodies, CSV exports, bulk actions, previews, smoke tests, or diagnostic payloads
- enum values, status names, source names, provider names, or template keys

Skip only for pure copy or styling changes with no data shape impact.

## Inputs

Collect:

- changed files
- endpoint or route names
- source data shape
- consumer data shape
- changed enum values
- one real response or fixture when available

## Surfaces to check

| Surface | Question |
|---|---|
| Database | Are columns fully named and aliased? |
| Presenter | Is raw shape normalized once? |
| API response | Does runtime output match the documented names? |
| Frontend type | Does it match runtime output? |
| Form payload | Does it send only mutable fields? |
| Export | Did new filters and fields propagate? |
| Preview | Does it use the same normalized shape as production? |
| Smoke | Does it assert body semantics, not only status? |

## Procedure

1. Identify the source of truth for each changed field.
2. Trace the path from source to every consumer.
3. Compare names, nullability, enum values, date formats, numeric formats, and nested structures.
4. Look for raw database rows used where a presenter or DTO is expected.
5. Check joins for alias collisions and ambiguous columns.
6. Check forms for immutable fields sent back to update endpoints.
7. Check UI rendering for raw objects, nullable dates, missing arrays, and literal undefined query parameters.
8. Check previews, exports, smoke tests, and diagnostics for stale assumptions.
9. Require a fixture, type check, smoke check, or explicit manual evidence for the highest-risk path.

## Common failures

- snake_case values are read as camelCase.
- a backend alias changes but the UI type stays unchanged.
- an object is rendered where a string or array is expected.
- UI submits immutable identifiers during update.
- enum spelling differs between backend and UI.
- list filters are updated but CSV export keeps old filters.
- diagnostic preview uses a raw row while production uses normalized context.

## Blockers

Treat these as blocking:

- raw database shape reaches a consumer that expects DTO shape
- endpoint reports success with a malformed or semantically failed body
- enum rename without compatibility or migration plan
- form submits immutable fields that backend rejects or ignores ambiguously
- new API field has no consumer contract where required

## Required output

```md
## Contract drift audit

- Status: pass / partial / fail
- Contract surfaces checked:
- Source of truth:
- Consumers checked:
- Drift findings:
- Required fixes:
- Regression test or smoke suggestion:
- Residual risk:
```

## Pair with

- `production-path-parity-auditor`
- `admin-ui-resilience-auditor`
- `admin-mutation-integrity-auditor`
