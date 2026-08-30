# Pre-Merge Review

## Purpose

Use this skill before opening a PR, marking a PR ready, merging, or deploying changes from a product repository.

## Goal

Catch project-breaking risks that generic code review often misses: secrets, env drift, Cloudflare bindings, CRM field compatibility, analytics regressions, mobile CTA regressions, asset placeholders, and unrelated rewrites.

## When to use

Use this skill when:

- a branch is ready for review
- a PR is about to merge
- a change touches API, forms, analytics, deployment, UI, or config
- an agent claims a task is done after editing 2+ files
- CI passed but product behavior may still be wrong

Skip only for trivial docs edits that do not affect workflow files.

## Inputs

Collect:

- task goal
- changed files
- diff summary
- target branch
- verification commands and results
- preview or deployment URL if available
- known product-specific constraints

## Risk checklist

| Risk area | Review question |
|---|---|
| Scope | Did the diff stay inside the requested task? |
| Secrets | Were API keys, tokens, emails, passwords, or private payloads exposed? |
| Env/config | Did env names, Wrangler bindings, routes, or secrets change? |
| Dependencies | Did package manager, lockfile, or dependency set change unexpectedly? |
| CRM/email | Were required lead fields or parser-compatible names changed? |
| Analytics | Were PostHog event names, distinct id, host/page metadata, or capture points removed? |
| Forms | Are validation, loading, error, and success states still present? |
| Cloudflare | Are Pages/Workers assumptions, routes, KV bindings, and custom domains preserved? |
| UI/mobile | Is the primary CTA obvious on mobile? Did sticky CTA or key conversion path break? |
| Assets | Were real assets replaced with placeholders or external hotlinks? |
| SEO | Did canonical, robots, sitemap, title, or service/location metadata regress? |
| Accessibility | Are labels, focus states, contrast, and tap targets still sane? |
| Workflow files | Were `AGENTS.md`, `.agents/skills/`, `templates/`, or scripts deleted or rewritten casually? |

## Procedure

1. Read the task goal and acceptance criteria.
2. List changed files and classify the change: docs, UI, API, config, deployment, analytics, data, or mixed.
3. Inspect the diff for unrelated changes.
4. Run or confirm the relevant verification commands.
5. Apply the risk checklist only to areas touched by the diff.
6. Record blockers, warnings, and non-blocking suggestions separately.
7. Produce a final verdict.

## Required verification by change type

| Change type | Minimum verification |
|---|---|
| Docs/playbook | diff review, link/path sanity |
| UI | build plus mobile/manual visual check if possible |
| Forms/API | build plus request/response or validation evidence |
| Cloudflare | build plus Wrangler/config review |
| Analytics | event capture path and payload review |
| CRM/email | payload field review and compatibility note |
| Dependency/config | install/build and reason for change |

## Blockers

Treat these as blocking unless explicitly accepted:

- hardcoded secrets
- deletion of required workflow files
- broken build
- changed CRM field names without compatibility plan
- changed Cloudflare binding names without deploy instructions
- new dependency without reason
- primary mobile CTA removed on conversion pages
- production code pointing to placeholder assets
- analytics capture removed from lead path
- broad refactor bundled into an unrelated task

## Warnings

Warnings should be called out but may not block:

- missing tests in a repo that has no test pattern
- minor visual inconsistency outside touched scope
- manual verification not possible in current environment
- lint script unavailable
- pre-existing failures not caused by the branch

## Anti-patterns

Avoid:

- saying green CI means safe to merge
- reviewing only code style while ignoring product contracts
- hiding warnings in a positive summary
- merging after only local verification when target branch moved
- accepting unrelated cleanup because it looks harmless

## Output format

```md
## Pre-merge review

- Status: pass / partial / fail
- Change type:
- Files reviewed:
- Verification:
- Blockers:
- Warnings:
- Product-specific risks:
- Recommended next action:
```

## Pair with

- `merge-preview-check` for integration drift
- `proof-loop-verification` for final evidence
- `systematic-debugging` if a blocker is a real bug
