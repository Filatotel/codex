# Project Resolver Liaison Bootstrap

This is the fresh-Liaison entry point for Project Resolver.

## Runtime mode

A fresh Liaison first determines runtime mode from an explicitly supplied `SBC_RUNTIME_CONTEXT`.

- explicit valid SBC context -> `SBC_BROWSER`
- no SBC context -> `ORDINARY_CHAT`
- malformed explicit SBC context -> fail closed; do not infer SBC capability

Runtime observation creates no semantic authority.

## Intake sequence

```text
fresh Owner / Liaison
→ detect explicit SBC runtime context if supplied
→ otherwise ORDINARY_CHAT
→ read AGENTS.md
→ read SYSTEM_MANIFEST.yaml
→ read ROUTER.md
→ classify the Owner request
→ load only the selected Engine / Workflow / Role / bounded Skills
→ perform useful work in the current chat or produce a governed handoff
```

`NO GLOBAL SKILL DISCOVERY` applies during bootstrap and ordinary execution. Do not recursively scan the repository or load every skill for context.

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

## Boundary

Bootstrap is an entry contract only. It does not create Owner, Canon, Control Director, routing, execution, or mutation authority. It does not perform external dispatch and does not require PAK, SBC transport automation, an execution ticket, a provider session, or browser-control state to use Project Resolver in `ORDINARY_CHAT` mode.

When no explicit SBC runtime context is supplied, continue as ordinary ChatGPT Web. Never invent SBC Browser state, PAK state, browser operations, provider authentication, tabs, sessions, or external-dispatch capability.
