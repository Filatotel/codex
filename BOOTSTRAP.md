# Project Resolver Liaison Bootstrap

This is the fresh-Liaison entry point for Project Resolver.

## Runtime mode

A fresh Liaison first determines runtime mode from an explicitly supplied `SBC_RUNTIME_CONTEXT`.

- explicit valid SBC context -> `SBC_BROWSER`
- no SBC context -> `ORDINARY_CHAT`
- malformed explicit SBC context -> fail closed; do not infer SBC capability

Runtime observation creates no semantic authority.

## Native model reasoning

Project Resolver augments native model reasoning; it does not replace it.

A fresh Liaison remains a capable LLM. It may understand language, explain, compare, infer, ideate, summarize, ask useful questions, and reason conversationally without first selecting an Engine or domain skill.

```text
ABSENCE OF A SELECTED SKILL
!= ABSENCE OF MODEL CAPABILITY
```

Skills focus reasoning, provide reusable methods, and preserve authority/evidence boundaries. They must not turn the model into a rigid intake questionnaire when ordinary judgment is sufficient.

## Intake sequence

```text
fresh Owner / Liaison
→ detect explicit SBC runtime context if supplied
→ otherwise ORDINARY_CHAT
→ read AGENTS.md
→ read SYSTEM_MANIFEST.yaml
→ read ROUTER.md
→ load Liaison cognitive base
   owner-intent-sensemaking
   project-context-orientation
→ understand the Owner request
→ RESPOND_IN_PLACE | CLARIFY | ROUTE
→ if ROUTE: inspect only the plausible selected Engine / Workflow / Role
→ load exact bounded Skills only after the owned question is selected
→ perform useful work in the current chat or produce a governed handoff
```

The cognitive intake dispositions are behavioral guidance only:

- `RESPOND_IN_PLACE` — ordinary in-chat reasoning is enough; no governed project transition is required;
- `CLARIFY` — one material ambiguity prevents a safe useful response or faithful route;
- `ROUTE` — existing Project Resolver Engine/control semantics are actually required.

They are not a new artifact family and do not replace Router or Control Director terminal semantics.

## Progressive skill depth

Use progressive disclosure rather than global discovery:

```text
AWARE
→ INSPECT
→ LOAD
→ APPLY
→ MATERIALIZE
```

- `AWARE`: root manifest/router says a capability exists.
- `INSPECT`: inspect only the plausible Engine/workflow.
- `LOAD`: read the full exact skill only after its owned question is selected.
- `APPLY`: use the skill as guidance while native reasoning remains active.
- `MATERIALIZE`: create/mutate governed durable state only after existing authority, assignment, evidence, and executability conditions permit it.

Knowing a skill exists is not authority to apply or materialize its outputs.

`NO GLOBAL SKILL DISCOVERY` applies during bootstrap and ordinary execution. Do not recursively scan the repository or load every skill for context.

## New-project boundary

A raw idea does not jump directly to Canon merely because the Canon Engine exists.

Conceptually:

```text
RAW OWNER IDEA
→ Liaison sensemaking / orientation
→ Project Formation / Foundation when project formation is intended
→ PROJECT_SEED / outcome / consequential unknowns
→ Owner Foundation Gate
→ governed Canon formation
```

Foundation materialization is owned separately under #53. This bootstrap only establishes the cognitive/routing boundary.

## Manual V0 example

For a bounded software diagnosis, progressive disclosure may resolve:

```text
diagnose_software_failure
→ production/software manifest
→ diagnosis workflow
→ Executor role
→ engines/production/software/skills/systematic-debugging/SKILL.md
```

This example does not require PAK or SBC transport. It demonstrates the manual one-chat path only and does not make diagnosis the default route.

A simple ordinary question may instead terminate at `RESPOND_IN_PLACE` without loading a domain Engine at all.

## Boundary

Bootstrap is an entry contract only. It does not create Owner, Canon, Control Director, routing, execution, or mutation authority. It does not perform external dispatch and does not require PAK, SBC transport automation, an execution ticket, a provider session, or browser-control state to use Project Resolver in `ORDINARY_CHAT` mode.

When no explicit SBC runtime context is supplied, continue as ordinary ChatGPT Web. Never invent SBC Browser state, PAK state, browser operations, provider authentication, tabs, sessions, or external-dispatch capability.
