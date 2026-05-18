# Implementation Planning

## Purpose

Use this skill before multi-step implementation, risky refactors, or delegated execution.

## Goal

Create a scoped, verifiable implementation plan that reduces ambiguity and prevents random rewrites.

## When to use

Use this skill when:

- a feature touches multiple files or systems
- deployment or migration risk exists
- UI, API, analytics, and infrastructure interact together
- another agent or future session will continue the work
- the implementation path is not obvious yet

Do not use this skill for tiny single-file edits.

## Required outputs

A plan should include:

- goal
- scope
- non-goals
- likely files touched
- high-risk areas
- implementation phases
- verification commands
- rollback or recovery notes
- acceptance criteria

## Procedure

### 1. Define the goal

One or two sentences only.

### 2. Define the scope

List:

- systems touched
- files or directories likely touched
- what explicitly should not change

### 3. Identify risks

Examples:

- merge drift
- Cloudflare binding mismatch
- CRM parser compatibility
- analytics schema drift
- mobile UX regression
- stale asset paths

### 4. Split into phases

Good phases:

- discovery
- implementation
- verification
- deployment
- QA
- handoff

Avoid giant undefined tasks.

### 5. Add exact verification

Prefer:

```text
npm run build
npm run lint --if-present
npm run typecheck --if-present
```

And concrete manual checks:

```text
Submit calculator form and verify CRM payload fields.
```

### 6. Define acceptance criteria

Use observable outcomes, not feelings.

Bad:

```text
UI improved.
```

Good:

```text
Mobile CTA visible on all service pages.
```

## Anti-patterns

Avoid:

- vague architecture plans
- giant rewrite phases
- no rollback notes for risky changes
- plans that assume hidden context
- verification that depends only on confidence

## Minimal plan structure

```md
# Goal

# Scope

# Non-goals

# Risks

# Phases

# Verification

# Acceptance criteria
```
