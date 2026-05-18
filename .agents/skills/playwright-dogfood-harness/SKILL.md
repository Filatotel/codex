# Playwright Dogfood Harness

## Purpose

Use this skill to give Codex and related agents a reproducible browser-based QA environment using Playwright, screenshots, console logs, traces, and reports.

## Goal

Do not depend on built-in screenshot or browser support.
Instead, make browser testing part of the repository itself.

The repository should be able to produce:

- screenshots
- traces
- console logs
- network failures
- viewport checks
- HTML reports
- CI artifacts

using repeatable commands.

## When to use

Use this skill when:

- a project has UI or browser workflows
- dogfood QA should produce evidence
- Codex cannot directly open screenshots
- Cloudflare Pages/Workers previews need validation
- forms, calculators, menus, dashboards, or landing pages exist
- mobile UX matters

## Core rule

Browser QA must not depend on the current chat environment.

The repository itself should provide:

- Playwright setup
- scripts
- reports
- artifacts
- CI integration

## Recommended structure

```text
playwright.config.ts

tests/dogfood/
  smoke.spec.ts
  mobile.spec.ts
  forms.spec.ts
  visual.spec.ts

artifacts/dogfood/
  screenshots/
  traces/
  reports/
```

## Required scripts

```json
{
  "scripts": {
    "qa:dogfood": "playwright test tests/dogfood",
    "qa:dogfood:headed": "playwright test --headed",
    "qa:dogfood:report": "playwright show-report",
    "qa:dogfood:install": "playwright install --with-deps chromium"
  }
}
```

## Recommended checks

### Smoke

- page loads
- no fatal console errors
- no broken assets
- no failed critical network requests

### Mobile

- no horizontal overflow
- CTA visible
- tap targets usable
- overlays usable

### Forms

- validation visible
- loading state visible
- success state visible
- error state visible
- analytics event path preserved

### Cloudflare

- Worker endpoints reachable
- Pages assets resolve correctly
- custom domain assumptions valid

## Procedure

1. Detect framework and preview workflow.
2. Add minimal Playwright setup.
3. Add dogfood tests focused on real user flows.
4. Configure screenshots and traces on failure.
5. Save artifacts into deterministic directories.
6. Add CI example or GitHub Action.
7. Document how agents should use the harness.

## Browser evidence

Preferred evidence order:

1. screenshots
2. Playwright traces
3. console logs
4. network logs
5. HTML report
6. markdown QA summary

## Codex integration rule

If native browser or screenshot tools are unavailable:

- run the Playwright harness
- inspect generated artifacts
- use logs and reports as evidence
- do not claim UI verification without evidence

## Anti-patterns

Avoid:

- relying on manual screenshots only
- testing only desktop
- shipping without console/network inspection
- creating giant flaky visual snapshot suites
- depending on external hosted QA tools for core verification

## Required output

- setup added or verified
- scripts added or verified
- artifacts generated
- browser evidence collected
- QA verdict: pass / partial / fail
