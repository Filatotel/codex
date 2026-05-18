# Systematic Debugging

## Purpose

Use this skill for technical issues where guessing would create churn: build failures, runtime bugs, API problems, deployment failures, UI regressions, analytics gaps, and integration issues.

## Goal

Find the root cause before changing code. The output should identify the failing layer, the evidence, the smallest safe fix, and the verification result.

## When to use

Use this skill when:

- tests fail
- builds fail
- forms or APIs behave unexpectedly
- Cloudflare deploys or bindings fail
- UI works on one screen but breaks on another
- PostHog, CRM email, routing, or environment behavior is wrong
- two or more quick fixes have already failed

Do not use this skill for planned feature work without a bug or unknown failure.

## Iron rule

No fixes before root cause evidence.

A hypothesis is allowed.
A blind patch is not.

## Debugging layers

| Layer | Evidence to collect |
|---|---|
| Browser/UI | console errors, network requests, viewport, broken layout, user steps |
| Astro/Vite | exact build error, file path, line number, recent imports |
| Worker/API | request payload, response status, logs, env access, CORS behavior |
| Cloudflare config | `wrangler` config, bindings, routes, custom domain, secrets |
| CRM/email | generated payload, required fields, delivery response, parser assumptions |
| Analytics | event name, distinct id, payload, host/page metadata, network result |
| DNS/domain | record type, target, proxy status, certificate/custom domain state |
| Data/state | KV keys, migrations, local storage, cache, stale preview deploys |

## Procedure

### 1. Restate the failure

Capture:

- expected behavior
- actual behavior
- exact command, route, URL, or user action
- first known bad state
- environment: local, preview, production, Worker, Pages, or CI

### 2. Read the exact error

Do not summarize from memory.
Use the real error text, status code, stack trace, or console message.

If no error exists, record that explicitly and gather logs or instrumentation.

### 3. Reproduce or bound the failure

Try to answer:

- Does it happen every time?
- Does it happen locally?
- Does it happen on Cloudflare preview?
- Does it happen in production?
- Does it depend on device, route, env, or input?

If reproduction is impossible, downgrade confidence and collect the best available evidence.

### 4. Check recent changes and scope

Inspect:

- current branch
- recent commits
- diff against target branch
- changed config files
- changed dependency files
- changed env or binding names

### 5. Isolate the failing layer

Trace the flow from user action to final effect.
For forms and lead systems, trace:

```text
UI input -> client validation -> API request -> Worker handler -> email/CRM payload -> response -> analytics event
```

For UI regressions, trace:

```text
component -> layout wrapper -> token/class source -> responsive breakpoint -> rendered viewport
```

### 6. Form one hypothesis

Write:

```text
Hypothesis: X is failing because Y.
Evidence: A, B, C.
Minimal test: Z.
```

Only test one variable at a time.

### 7. Apply the smallest fix

Fix the source, not the symptom.
Do not combine with unrelated cleanup.
Do not rewrite architecture unless three focused fixes have failed and the architecture is likely wrong.

### 8. Verify

Use the strongest available check:

- failing test now passes
- `npm run build`
- `npm run lint --if-present`
- `npm run typecheck --if-present`
- `wrangler deploy --dry-run` or relevant Cloudflare check
- browser/manual repro steps
- endpoint status and response body
- analytics or CRM payload evidence

## Rule of three

After three failed fix attempts, stop patching.
Escalate to architecture or assumption review.

## Anti-patterns

Avoid:

- changing code before reading the exact error
- fixing only the visible symptom
- stacking multiple fixes before testing
- ignoring Cloudflare env/binding differences
- assuming local success means production success
- hiding partial verification behind confident language
- deleting workflow files to make a task pass

## Required output

- Failure restated
- Evidence collected
- Failing layer
- Root cause or best hypothesis
- Fix applied or recommended
- Verification performed
- Residual risk
- Verdict: pass, partial, or fail
