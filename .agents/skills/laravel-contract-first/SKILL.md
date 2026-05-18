# Laravel Contract-First Development

## Purpose

Use this skill for Laravel core work where database schema, API responses, frontend UI, Filament admin, jobs, integrations, and Cloudflare edge runtime must stay consistent.

## Goal

Prevent the common failure mode where backend, database, API resources, TypeScript interfaces, Filament forms, and frontend UI are built separately and then break when connected.

Development should start from contracts:

```text
business rule
  ↓
database schema
  ↓
DTO / request / resource
  ↓
OpenAPI or typed API contract
  ↓
generated frontend types
  ↓
UI implementation
  ↓
QA and drift checks
```

## When to use

Use this skill when a task touches any of:

- Laravel migrations
- Eloquent models
- API routes/controllers/resources
- Filament resources
- billing or ledger state
- partner attribution
- permissions/roles
- Cloudflare public runtime consuming Laravel data
- frontend TypeScript interfaces
- generated API clients
- multi-tenant data boundaries

## Core rule

No independent UI interface design for server-owned data.

If Laravel owns the data, Laravel contracts own the data shape.

## Required artifacts

For non-trivial backend work, create or update:

- `DATABASE_CONTRACT.md`
- `API_CONTRACT.md`
- `UI_BINDING_CONTRACT.md`
- `SCHEMA_DRIFT_CHECK.md` when schema changed

## Contract layers

| Layer | Source of truth | Output |
|---|---|---|
| Database | migrations | tables, columns, indexes, constraints |
| Domain | services/actions/policies | business rules |
| API input | FormRequest / DTO | validation contract |
| API output | JsonResource / DTO | response contract |
| Frontend | generated types | TypeScript interfaces |
| Admin | Filament Resource | operational UI contract |
| Edge | Cloudflare runtime schema | public/cache-safe subset |

## Laravel package baseline

Use only when needed:

- Filament: admin and operations
- Spatie Permission: roles and permissions
- Spatie Activitylog: audit trail
- Laravel Sanctum: API tokens
- Laravel Horizon: queues
- Laravel Telescope: dev/staging debugging
- Laravel Pulse: production health
- Laravel Cashier: billing when Stripe/Paddle path is ready

Do not install packages just because they are popular.

## Database rules

Every important table needs:

- primary key strategy
- foreign keys where appropriate
- indexes for lookup paths
- unique constraints for business uniqueness
- nullable fields justified
- timestamps policy
- soft delete policy if needed
- tenant/org boundary if multi-tenant
- audit strategy for sensitive changes

## API rules

Every API endpoint needs:

- route name
- auth guard
- permission or policy
- request validation
- response shape
- error shape
- pagination shape if list endpoint
- idempotency rule if money or external integration is involved

## UI binding rules

Frontend must not invent server-owned interfaces manually.

Prefer one of:

- generated TypeScript from OpenAPI
- generated TypeScript from Laravel DTO/schema tooling
- explicit copied contract with drift check

If manual interfaces exist, add a drift check task before merge.

## Filament rules

Filament Resources should reflect operational reality:

- visible fields match admin workflows
- destructive actions require confirmation
- sensitive changes are audited
- roles/permissions guard actions
- money/billing changes are never casual inline edits
- payout and ledger actions use explicit workflows

## Cloudflare edge rules

Cloudflare may consume only safe public/runtime data:

- site config
- published versions
- QR/shortlink target data
- cache-safe public assets
- tracking metadata

Cloudflare must not own:

- billing ledger
- source-of-truth user/org records
- payout decisions
- permission system
- private audit trail

## Migration safety

Before merge, answer:

- Is migration reversible?
- Does it backfill existing data safely?
- Does it lock large tables?
- Does it preserve old API response compatibility?
- Does frontend consume changed fields?
- Do Filament forms/tables still work?

## Verification commands

Use relevant checks:

```bash
composer test
php artisan test
php artisan migrate:fresh --seed
php artisan route:list
php artisan config:clear
npm run build
npm run typecheck --if-present
npm run qa:dogfood
```

Use project-specific equivalents when scripts differ.

## Anti-patterns

Avoid:

- frontend interfaces created before API contracts
- migrations without indexes or constraints
- money fields as floats
- direct balance mutation
- deleting fields without compatibility plan
- Filament god-mode actions without audit trail
- Cloudflare KV as source-of-truth database
- API responses shaped casually inside controllers
- hidden tenant/org boundary assumptions

## Required output

- Contracts touched
- Schema changes
- API changes
- Generated/manual frontend type impact
- Filament/admin impact
- Cloudflare edge impact
- Verification performed
- Drift risks
- Verdict: pass / partial / fail
