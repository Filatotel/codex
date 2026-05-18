# Webapp Dogfood QA

## Purpose

Use this skill for exploratory QA of web apps, landing pages, dashboards, calculators, menu systems, and admin panels.

## Goal

Catch broken flows, mobile regressions, console errors, bad assets, weak UX, and conversion-path failures before declaring UI work complete.

## When to use

Use this skill when:

- a UI task is marked done
- a landing page changed
- a calculator or form changed
- a deployment preview exists
- responsive behavior may have changed
- analytics or conversion flow matters

This skill is especially important for:

- moving company sites
- calculators
- lead forms
- admin panels
- mobile-first landing pages
- interactive menu systems

## Inputs

Collect:

- preview URL or local URL
- changed pages/components
- expected conversion path
- target devices or viewport assumptions
- known constraints

## Core flows to test

### Navigation

- header links
- footer links
- CTA buttons
- mobile menu
- back navigation
- external review links

### Forms and calculators

- empty validation
- invalid values
- loading state
- success state
- failure state
- analytics event path
- CRM/email submission path

### UI and layout

- hero section
- sticky mobile CTA
- responsive cards/grids
- broken spacing or overflow
- inaccessible text contrast
- missing or distorted images
- placeholder assets accidentally shipped

### Technical checks

- browser console errors
- failed network requests
- incorrect API host
- Cloudflare Worker/API responses
- stale deploy or cache behavior

## Mobile-first rules

On mobile, verify:

- CTA visible without hunting
- text readable without zoom
- tap targets large enough
- no horizontal scroll
- no clipped forms or overlays
- hero content not hidden by fixed UI

## Procedure

1. Define the core user path.
2. Walk the path like a real user.
3. Intentionally try bad inputs and edge cases.
4. Check console/network behavior during interaction.
5. Inspect responsive behavior.
6. Record screenshots or notes for each issue.
7. Separate blockers from polish issues.
8. Produce a QA verdict.

## Severity levels

| Severity | Meaning |
|---|---|
| Critical | Conversion path or app functionality broken |
| High | Major UX or data problem likely affecting users |
| Medium | Visible issue with workaround |
| Low | Cosmetic or polish issue |

## Recommended evidence

- screenshots
- viewport info
- console error text
- failing request URL/status
- reproduction steps
- before/after notes

## Anti-patterns

Avoid:

- desktop-only verification
- checking visuals without trying the workflow
- claiming success without testing forms
- ignoring console errors because the UI still renders
- approving placeholder assets or broken review links
- assuming build success means UX success

## Required output

- Scope tested
- Devices/viewports checked
- Issues found by severity
- Evidence collected
- Conversion-path status
- Final verdict: pass / partial / fail
