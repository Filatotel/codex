# Production Path Parity Auditor

## Purpose

Use this skill when a change adds or edits preview, test, dry-run, retry, smoke, diagnostic, provider, template, delivery, or automation behavior.

## Goal

Make every non-production path truthful. A preview or diagnostic tool is only useful if it uses the same resolver, renderer, validation, and business-success rules as the production action, while suppressing side effects when needed.

## When to use

Use this skill when a task touches:

- email, CRM, provider, notification, or delivery code
- template rendering, variable analysis, or preview tools
- quote, estimate, invoice, or confirmation sending
- smoke tests or diagnostic endpoints
- retry logic, queue processors, or background actions
- automation triggers or event hooks
- public flow plus admin tool flow for the same action

## Inputs

Collect:

- production route or worker path
- preview or dry-run route
- test route or smoke name
- retry or queue path, if any
- shared helpers used by each path
- side effects that must be suppressed in preview
- success criteria for the business action

## Path map

For each changed action, map:

```text
production path -> resolver -> renderer/validator -> side effect -> success rule
preview path    -> resolver -> renderer/validator -> no side effect -> preview output
test path       -> resolver -> renderer/validator -> controlled side effect or mock -> test assertion
retry path      -> resolver -> renderer/validator -> side effect -> success rule
smoke path      -> resolver -> minimal fixture -> semantic assertion
```

## Procedure

1. Identify the production source of truth.
2. Verify preview and test paths call the same resolver or a pure helper extracted from it.
3. Verify rendering and variable analysis use the same context.
4. Verify explicit selections are honored: provider, template, legacy key, site, app, recipient, or purpose.
5. Verify mismatch guards exist for purpose, provider, tenant, site, or app boundaries.
6. Verify preview suppresses only side effects, not validation.
7. Verify retry reports business success, not only HTTP success.
8. Verify smoke checks semantic body fields, not only status 200.
9. Add a note when parity is intentionally incomplete.

## Common failures

- preview uses a hand-built payload while production uses a normalized DTO.
- selected template or legacy key is accepted but ignored.
- test endpoint returns success when the underlying business action failed.
- smoke only checks status and misses an error body.
- retry treats transport success as delivery success.
- variable analysis uses a different context from template rendering.
- diagnostics silently falls back to a default and hides the selected path.

## Blockers

Treat these as blocking:

- preview can show a result that production would not send or accept
- test route uses a different provider, template, or resolver from production without clear labeling
- business failure is reported as success
- explicit operator selection is ignored
- tenant, site, app, or purpose mismatch is not rejected

## Required output

```md
## Production path parity audit

- Status: pass / partial / fail
- Production path:
- Preview path:
- Test or smoke path:
- Shared helpers:
- Divergence found:
- Required fixes:
- Side effects suppressed:
- Regression test or smoke suggestion:
```

## Pair with

- `contract-drift-auditor`
- `cloudflare-d1-worker-readiness`
- `diagnostics-tools-ux-auditor`
