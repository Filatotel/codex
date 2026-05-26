# Cloudflare D1 Readiness

## Purpose

Use this skill when a change touches Cloudflare deployment, D1 schema, SQL, Wrangler configuration, bindings, route ordering, headers, cookies, or public runtime configuration.

## Goal

Catch platform-specific risks before merge. Local type checks can pass while D1 migrations, Worker routing, remote bindings, or response wrappers still fail in preview or production.

## When to use

Use this skill when a task touches:

- D1 migrations, schema guards, queries, joins, or indexes
- Worker routes, middleware, cookies, CORS, or response wrappers
- Wrangler config, bindings, KV, assets, routes, or environment names
- public runtime endpoints, health checks, diagnostics, or app config routes
- Cloudflare preview, production deploy, custom domain, Pages, or Workers behavior

## Inputs

Collect:

- changed SQL and migration files
- changed Worker route and middleware files
- Wrangler config and binding names
- affected public and admin routes
- target environment: local, preview, production, or remote D1
- verification commands and deploy status

## Checklist

- Remote D1 migration syntax is safe.
- Backfills preserve existing data.
- Joins use explicit column aliases.
- Joined row mapping cannot overwrite important fields.
- New filters have indexes or bounded reads.
- Specific routes are registered before broad fallbacks.
- Header and cookie behavior survives response wrappers.
- Public CORS does not break admin routes.
- Public runtime endpoints return only safe data.
- Binding and environment names match code and Wrangler config.

## Common failures

- ambiguous SQL column after a join
- joined row key collision
- migration passes locally but fails on remote D1
- production database misses a new column
- response wrapper changes cookie behavior
- broad fallback catches a specific API route
- diagnostic route returns more runtime data than intended
- code assumes database constraints that the schema does not enforce

## Blockers

Treat these as blocking:

- migration likely fails on remote D1
- route order can change auth, fallback, or cookie behavior
- runtime config route exposes private operational data
- query can create or rely on orphan state without explicit guard
- binding or environment rename lacks deploy instructions
- production path depends on a column that is not guaranteed to exist yet

## Required output

```md
## Cloudflare D1 readiness audit

- Status: pass / partial / fail
- D1 and SQL risks:
- Route and header risks:
- Bindings and deploy notes:
- Public runtime data exposure:
- Required fixes:
- Verification performed:
- Residual risk:
```

## Pair with

- `contract-drift-auditor`
- `admin-mutation-integrity-auditor`
- `production-path-parity-auditor`
