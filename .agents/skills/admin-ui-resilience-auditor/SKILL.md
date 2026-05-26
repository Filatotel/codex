# Admin UI Resilience Auditor

## Purpose

Use this skill when a change touches React admin UI, dashboards, settings pages, forms, diagnostic tools, tables, filters, or route state.

## Goal

Prevent runtime crashes and misleading admin screens caused by partial data, wrong shapes, async state bugs, or unsafe rendering. Admin UI should treat even internal API data as potentially incomplete.

## When to use

Use this skill when a task touches:

- React routes or components
- admin tables, cards, dashboards, or detail pages
- settings forms or manager pages
- tool and diagnostic pages
- query string state or filters
- API client DTOs used by UI
- loading, error, empty, or success states

## Inputs

Collect:

- changed routes and components
- API DTOs and example responses
- form payloads and validation errors
- loading and error paths
- key user actions
- target viewport assumptions if relevant

## Procedure

1. Check for conditional hooks, early returns before hooks, and hook calls inside branches.
2. Check rendering for raw objects, nullable dates, optional arrays, and missing nested fields.
3. Check every async action has loading, success, error, and finally behavior.
4. Check empty state and partial-data state.
5. Check forms submit only intended mutable fields.
6. Check validation errors render near fields and do not crash the route.
7. Check query params omit undefined and stale values.
8. Check destructive or retained-record actions use accurate labels such as Disable or Archive.
9. Check mobile or narrow layout when the page is operator-facing.
10. Keep raw JSON in collapsed details unless the page is explicitly developer-only.

## Common failures

- object rendered as a React child
- nullable date passed directly into formatting logic
- array method called on missing value
- loading state never clears after error
- form posts the full DTO including immutable fields
- route serializes literal undefined in query string
- manager page is only a raw JSON dump
- validation error is swallowed and page appears saved

## Blockers

Treat these as blocking:

- route can crash from a valid partial API response
- form can silently save a wrong or stale payload
- admin user sees success after failed save
- important operator workflow has no error state
- diagnostic page hides test progress until completion

## Required output

```md
## Admin UI resilience audit

- Status: pass / partial / fail
- Routes/components checked:
- Data-shape risks:
- Async-state risks:
- Form payload risks:
- Loading/error/empty state:
- Operator usability risks:
- Required fixes:
- Regression check suggestion:
```

## Pair with

- `contract-drift-auditor`
- `diagnostics-tools-ux-auditor`
- `webapp-dogfood-qa`
