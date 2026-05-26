# Diagnostics Tools UX Auditor

## Purpose

Use this skill when a change touches tools, health pages, diagnostics, smoke tests, debug pages, timing reports, or operational dashboards.

## Goal

Make diagnostics truthful, discoverable, and useful during real operations. A diagnostic screen should not be a raw dump or a spinner that only updates after every check has completed.

## When to use

Use this skill when a task touches:

- tools index pages
- health or system diagnostic pages
- smoke test runners
- delivery, lead, route, template, or multisite diagnostic tools
- timing breakdowns or dashboard health cards
- test catalogs or grouped checks
- operational debug UI

## Inputs

Collect:

- tool routes and their purpose
- smoke test names and backend support
- current frontend rendering behavior
- expected operator role and frequency of use
- timing output and slow checks
- pages where section-specific checks should appear

## Procedure

1. Inventory every tool page.
2. For each tool, classify purpose, user role, and frequency: frequent, occasional, rare, or developer-only.
3. Identify duplicated tools and decide whether to merge, redirect, or explain the difference.
4. Verify all backend smoke checks are surfaced somewhere in the UI.
5. Prefer a catalog-driven smoke runner over hardcoded partial lists.
6. Verify long-running checks render progressively with queued, running, passed, failed, and skipped states.
7. Verify a user can rerun one check, a group, failed checks, or all checks.
8. Keep raw JSON inside collapsed details, not as the main interface.
9. Convert timing data into actionable bottleneck notes when possible.
10. Make diagnostics link to the relevant settings or detail page for fixes.

## Good diagnostics UI

- renders rows before all tests finish
- shows per-check duration and message as soon as each check completes
- groups checks by domain
- explains what each group proves
- includes clear next actions for failure
- separates operator checks from developer-only raw data
- keeps old routes working when pages are merged

## Common failures

- frontend waits for the whole smoke batch before showing results
- backend has smoke checks that the UI never exposes
- two pages run nearly identical checks without explanation
- smoke checks only show status codes and not semantic failures
- raw JSON is the main UI
- diagnostic page reports success while a business action failed
- timing breakdown is shown without identifying the slow path

## Blockers

Treat these as blocking for tool UX work:

- smoke runner hides progress until all checks finish
- a newly added smoke check is not reachable from the UI
- a tool claims to validate a workflow but does not exercise the relevant path
- a diagnostic exposes private runtime data
- a merged or removed tool route breaks existing navigation without fallback

## Required output

```md
## Diagnostics tools UX audit

- Status: pass / partial / fail
- Tools inventoried:
- Duplicate or overlapping tools:
- Smoke checks surfaced:
- Progressive rendering status:
- Raw JSON usage:
- Actionability gaps:
- Required fixes:
- Suggested grouping:
```

## Pair with

- `production-path-parity-auditor`
- `cloudflare-d1-readiness`
- `admin-ui-resilience-auditor`
