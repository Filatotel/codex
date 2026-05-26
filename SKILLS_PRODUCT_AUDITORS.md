# Product Audit Skills

Use these skills before broad pre-merge review when a product PR touches data contracts, admin mutations, production-like previews, Cloudflare/D1 runtime, diagnostics tools, or React admin UI.

Recommended selection:

- `contract-drift-auditor` for DB, API, UI, export, preview, or diagnostic shape drift.
- `production-path-parity-auditor` for preview, test, send, retry, smoke, delivery, template, or automation parity.
- `admin-mutation-integrity-auditor` for admin CRUD, settings, enable/disable, primary/default, and nested resource mutations.
- `cloudflare-d1-readiness` for Workers, D1, Wrangler, bindings, routes, public runtime, and deployment assumptions.
- `diagnostics-tools-ux-auditor` for tools, health pages, smoke runners, timing views, and operational diagnostics.
- `admin-ui-resilience-auditor` for React admin UI resilience, forms, loading/error states, and partial data.
- `codex-pr-workflow-guard` for PR body accuracy, mergeability, checks, review thread state, and same-branch follow-up decisions.

Use only the specific skill needed for the current phase. Do not load all product audit skills by default.
