# PAC External Execution Relay Boundary

**Status:** architecture boundary freeze; not an implementation contract

**Baseline:** `9cc81e2d2a3b7db28502a9e2270f149e28702451`

**Observed provider behavior date:** 2026-10-01

## Purpose and placement

This record freezes the missing boundary between an execution already admitted by
the public Codex control plane and its physical realization by a private Personal
Agent Console (PAC) adapter. It does not implement `TICKET-01`, a relay protocol,
or a provider adapter, and it does not authorize private PAC creation.

The PARK/external relay is a deterministic transport and execution layer. It may
parse structured transport data, materialize a prompt payload, invoke an admitted
provider operation, discover and observe the resulting remote execution, and
return normalized physical evidence. It does not decide what work should happen.

```text
PARK / RELAY
!= CONTROL DIRECTOR
!= ASSIGNMENT COMPILER
!= RESOLVER
!= EXECUTOR SEMANTIC AUTHORITY
```

The relay consumes an already-governed ticket/assignment projection. Provider
physics remain replaceable and cannot create public semantic authority.

## Required dispatch lifecycle

Future TICKET/PARK conformance must support an equivalent lifecycle:

```text
SPAWN_READY
→ EXECUTION_TICKET
→ CLAIM / REVALIDATE / RESERVE
→ DISPATCH_READY
→ create stable logical attempt/dispatch key
→ DISPATCH_REQUESTED
→ ACK_PENDING
→ DISPATCH_ACKNOWLEDGED(execution_ref)
→ RUNNING / SUSPENDED where applicable
→ COMPLETED | FAILED | CANCELLED/BLOCKED as supported
→ RESULT / EVIDENCE READBACK
→ durable reconciliation
→ return control to source Liaison
```

The following distinctions are mandatory:

```text
DISPATCH_REQUESTED != DISPATCH_ACKNOWLEDGED
ACK UNKNOWN != DISPATCH_FAILED
ACK UNKNOWN != PERMISSION TO SEND AGAIN
ONE LOGICAL ATTEMPT → AT MOST ONE PHYSICAL DISPATCH BY DEFAULT
```

A second physical send requires proven non-acceptance/failure of the first
request or a separately admitted new attempt. A slow or missing acknowledgement
must not cause duplicate external work.

## Acknowledgement and discovery capabilities

An adapter may establish acknowledgement using the strongest supported surface:

1. a direct machine response returning or deriving an execution reference;
2. machine-readable task discovery/status;
3. bounded provider-UI discovery when no stronger surface exists.

The adapter must advertise these as distinct capabilities. Submission does not
imply acknowledgement, polling, result readback, remote branch write, or pull
request creation.

As observed on 2026-10-01, Codex Cloud's experimental CLI can submit a task with
`codex cloud exec --env ENV_ID <query>` and can expose task/chat metadata through
`codex cloud list --json`. These are candidate provider-specific mechanisms, not
universal protocol semantics. The corresponding current documentation is:

- <https://learn.chatgpt.com/docs/developer-commands?surface=cli>
- <https://learn.chatgpt.com/docs/cloud>
- <https://learn.chatgpt.com/docs/third-party/github>

An observed ChatGPT UI route can also delegate coding work into another Codex
Cloud chat without giving the source conversation a reliable immediate machine
acknowledgement. A private browser adapter may retain opaque project/container
locators and discover the remote chat through provider navigation. URLs, recent
lists, window or tab identifiers, selectors, and controls remain private PAC
state. This observation is not universal public Codex law.

If a UI adapter cannot correlate concurrent submissions reliably, it must narrow
concurrency for that workspace scope—for example, to one unresolved
`ACK_PENDING` dispatch—rather than guess.

## Identity and exact target binding

```text
ASSIGNMENT REF
!= EXECUTION TICKET REF
!= LOGICAL ATTEMPT / DISPATCH KEY
!= REMOTE TASK ID
!= REMOTE CHAT URL
!= BROWSER TAB ID
```

Private PAC owns the physical mapping. Public Codex consumes only the logical and
execution references required for exact result correlation and stale-result
rejection. A remote URL is evidence/addressing, not authority.

No relay may compensate for an unproven execution target by instructing a remote
model to find, guess, or switch to a repository, pull request, branch, or commit:

```text
PROMPT-LEVEL CONTEXT GUESSING != EXECUTION-CONTEXT PROOF
```

Exact-candidate work must use a route that proves the required target identity
before dispatch or advertises a target-binding mechanism sufficient for the
claim. Otherwise the route fails closed before an external side effect.

## Durable assignment and result transport

Large assignments should normally be materialized durably under the applicable
assignment-compilation semantics. The relay may carry a short bounded instruction
and exact materialization identity. Serialization through a CLI or UI never
becomes a second source of assignment authority.

The source Owner/Liaison surface need not remain focused on a remote task. PAC may
poll/read the execution and return normalized status and result data. Status or a
summary alone does not establish completion: required results and evidence must
still satisfy the durable materialization, fresh independent readback, and exact
verification contracts. A tab/session may disappear after binding without
destroying logical continuity, provided durable correlation and result refs have
been preserved.

## Optional promotion

Execution, remote branch mutation, pull request creation, and promotion are
separate capabilities and authority decisions. A valid coding result remains
valid when pull request capability is unavailable. When pull request creation is
available and authorized, only the exact correlated result/candidate may be
routed to that action.

The Workspace Agents API is not Codex Cloud and is not a semantic substitute.
Its documented idempotency key, accepted run reference, and pollable lifecycle
are useful transport precedent only:

- <https://learn.chatgpt.com/workspace-agents/trigger-runs>

The public TICKET/PARK contract should preserve equivalent provider-neutral
properties even when a concrete adapter proves them differently.

## Fake-runtime conformance additions

The future dumb fake external runtime gate must cover at least:

| Case | Required result |
|---|---|
| Immediate acknowledgement | Submit, bind acknowledgement, complete, and read back the result. |
| Delayed acknowledgement | Discovery binds the same attempt; no duplicate dispatch occurs. |
| Unknown acknowledgement | Repeated control ticks preserve `ACK_PENDING`/reconciliation state and do not resend. |
| Proven submit failure | At most one separately governed retry/new attempt is admitted. |
| Wrong discovered execution | Correlation rejects an execution belonging to another attempt. |
| Missing durable result | Remote completion does not become semantic `COMPLETE`. |
| No PR capability | The coding result remains valid and promotion routes separately. |
| Authorized PR capability | Only the exact result/candidate routes to PR creation. |
| Lost tab/session | Bound logical execution survives loss of the physical viewing handle. |
| Unproven target | The route fails closed before dispatch. |

Conformance must visibly separate proof of admissibility from proof of effect.
Interruption after a possible external effect produces an unknown/reconciliation
state, never permission to replay a consumed ticket. Recovery uses a new admitted
attempt unless the same physical execution is proven still alive.

## Dependency direction

This boundary is implemented only through bounded downstream workstreams:

```text
#55 compiler/authority hardening
#61 architecture-health hardening
#57-B / #57-C surface selection + drift/broker completion
#58 logical attempt/instance identity
#59 autonomy + dispatch idempotency
#68 finite resource reservation/accounting
        ↓
TICKET-01 exact authorized one-attempt projection
        ↓
PARK/relay protocol conformance against dumb fake runtime
        ↓
PAC_READY
        ↓
private provider adapters
```

This record does not collapse those workstreams into a mega-change. No new public
semantic authority belongs in private PAC, and no provider-specific UI behavior
may become a required universal control-plane mechanism.
