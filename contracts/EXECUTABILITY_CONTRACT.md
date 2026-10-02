# Destination Executability Contract

This contract prevents Project Resolver from assigning mandatory work to a destination instance that cannot physically perform or prove it.

## Kernel law

**NO ASSIGNMENT WITHOUT EXECUTABILITY PROOF.**

Before `ASSIGN`, the Control Director MUST establish for the exact destination instance:

```text
REQUIRED_CAPABILITIES ⊆ AVAILABLE_CAPABILITIES
```

The comparison covers every mandatory action and every mandatory acceptance/evidence gate, not only the engine's semantic capability.

The requirements entering this comparison MUST come from a `COMPILED`
`COMPILED_ASSIGNMENT` under `contracts/ASSIGNMENT_COMPILATION_CONTRACT.md`,
plus mandatory prerequisites of workflows/skills selected within that authority.
Arbitrary uncompiled prompt obligations are not a required-capability source.

If the subset relation is not proven, the work is **not an executable assignment for that destination**. Return `ASSIGNMENT_NOT_ADMISSIBLE`, choose another already-authorized executable destination/mode, or escalate. Do not intentionally issue the assignment and wait for the Executor/Verifier to discover the missing runtime later.

## Three separate questions

1. **Semantic ownership:** which engine conceptually owns the transformation?
2. **Authority:** is the requested action authorized?
3. **Destination executability:** can this exact destination instance perform every mandatory action and obtain every mandatory evidence path here?

All three must pass. Semantic capability never implies runtime capability.

The execution-surface advertisement is likewise not authority:

```text
SURFACE/CAPABILITY ADVERTISEMENT != SEMANTIC AUTHORITY
SURFACE/CAPABILITY ADVERTISEMENT != ASSIGNMENT AUTHORITY
SURFACE/CAPABILITY ADVERTISEMENT != RESOURCE AUTHORITY
SURFACE/CAPABILITY ADVERTISEMENT != AUTONOMY AUTHORITY
```

## CAPABILITY_PROFILE

A `CAPABILITY_PROFILE` is the canonical, freshness-bounded advertisement/observation of one execution surface available to one exact destination instance. It is the existing executability owner and MUST be extended rather than shadowed by a second execution-surface profile artifact.

It records:

- stable profile identity in the existing `artifact_id`; there is no second `surface_id`;
- destination/runtime identity;
- provider-neutral `surface_class`;
- opaque `workspace_scope_ref` identifying the usable workspace scope without making provider/session/browser/tab IDs semantic authority;
- readiness/provisioning state in `readiness`, separate from lifecycle `status=CURRENT`;
- observed available capabilities;
- unavailable or explicitly excluded capabilities;
- provider-neutral `evidence_channels` through which factual evidence may be obtained;
- evidence/source for capability claims;
- freshness boundary and limitations.

Reference surface-class families include `CHATGPT_CHAT`, `REMOTE_DEV_ENV`, `CODEX_CLOUD`, `BROWSER_CONSOLE`, `DEPLOYMENT_RUNTIME`, and `MANUAL_OPERATOR`. The vocabulary is extensible and provider-neutral; these labels are not provider account IDs and consumers MUST NOT require a commercial provider name as a universal surface identifier.

`readiness` is one of `READY`, `DEGRADED`, `PROVISIONING_REQUIRED`, `AUTH_REQUIRED`, or `UNAVAILABLE`. `READY` and `DEGRADED` may participate in current admission only when the exact required capabilities are proven. `PROVISIONING_REQUIRED`, `AUTH_REQUIRED`, and `UNAVAILABLE` are valid advertisement states but MUST NOT satisfy current assignment admission, an `ADMISSIBLE` execution route, `SPAWN_READY`, or current-executability revalidation. Task 57-A does not select, rank, provision, authenticate, or recover a surface.

Common provider-neutral evidence-channel identifiers include `connector_result`, `terminal_stdout`, `unit_test_result`, `build_log`, `deployment_status`, `durable_artifact_ref`, and `chat_completion`. `evidence_channels` advertise where evidence can be observed; they do not themselves prove a capability or create a parallel evidence authority. Capability truth remains owned by governed `CAPABILITY_EVIDENCE` resolution.

A capability profile is evidence about a runtime, not authority to use that capability.

For deterministic admission, the profile freshness boundary contains timezone-aware
`observed_at` and `valid_until` timestamps. `valid_until` must still be in the future.
Every available capability cites a separately represented, `RESOLVED`
`CAPABILITY_EVIDENCE` artifact. An embedded copy in `evidence_artifacts` is transport/cache data only and is never authoritative by existence or self-declared status. Complete-chain validation MUST resolve the reference through an explicitly supplied governed evidence source (an offline governed bundle is valid), fail closed when resolution is absent/fails, and reject material disagreement with an embedded copy. The resolved artifact must
name the same exact `runtime_identity`, prove the cited capability, and remain valid
for the whole profile freshness boundary. It also binds common artifact identity, producer, assignment/input state, provenance and related-artifact lineage, plus a non-empty observation method and `created_from` source. This is an explicit trust boundary, not a claim of cryptographic authenticity. An arbitrary or unresolved string is not capability evidence.

Timestamps use the reference validator's strict RFC3339/Python-datetime subset: full date and seconds, optional non-empty fractional seconds, ordinary clock minutes/seconds from 00–59, and `Z` or a numeric `HH:MM` offset whose hour is 00–23 and minute is 00–59. The schema pattern enforces that shared structural subset; calendar validity and UTC-normalization overflow are reference/runtime-domain validation errors, never exceptions.

### Resource and connector boundary

Resources and connectors are not execution surfaces merely because they exist:

```text
GOOGLE DRIVE RESOURCE != EXECUTION SURFACE
GITHUB REPOSITORY != EXECUTION SURFACE
CONNECTOR/PLUGIN = CAPABILITY/EVIDENCE CHANNEL ON A SURFACE
```

A connector may expose a capability such as `connector:<name>` or provide an evidence channel, but it does not become a separate surface unless a real destination/runtime/workspace surface is independently advertised. A repository, document store, database, deployment target, or other resource remains a resource governed by its own authority model.

## End-to-end EXECUTION_ROUTE

**NO EXECUTABLE ASSIGNMENT WITHOUT AN ADMISSIBLE END-TO-END EXECUTION ROUTE.** Destination proof alone is insufficient. A schema-backed `EXECUTION_ROUTE` binds the exact assignment draft and a structured final-result endpoint, and contains exactly identified `CANDIDATE_DELIVERY`, `EXECUTION_VERIFICATION`, and `DURABLE_EVIDENCE_CONTROL` roles. Every segment binds its destination, runtime, capability profile, requirements, and mode. Profile-owned surface class, workspace scope, readiness, evidence channels, and capability facts are not duplicated into route segments when the exact `capability_profile_ref` is sufficient. Every cross-surface handoff separately proves source export/publish capabilities and target receive/read capabilities; capabilities on the wrong side cannot satisfy the edge. A same-surface handoff instead requires exact destination/runtime equivalence plus an internal-transfer capability on that runtime. All segment and directional edge requirements must be proven. The structured `final_result.segment_ref` must resolve to the durable segment and its `destination_id` must equal both that segment's destination and `ASSIGNMENT.result_to`. Missing delivery, execution, publication/readback, or final durable reachability returns `ASSIGNMENT_NOT_ADMISSIBLE`; capability loss after valid admission remains `BLOCKED_RUNTIME_DRIFT`.

## ASSIGNMENT_ADMISSIBILITY

An `ASSIGNMENT_ADMISSIBILITY` record binds an assignment draft to an exact destination and capability profile. It records:

- required capabilities derived from mandatory actions and mandatory evidence gates;
- available capabilities from the destination profile;
- unsatisfied required capabilities;
- mandatory evidence paths;
- selected execution mode/fallback, if any;
- `ADMISSIBLE` or `NOT_ADMISSIBLE`.

`ADMISSIBLE` means only **CAN EXECUTE ON THE CITED SURFACE**. It does not grant resource, semantic, claim, owner, assignment, or autonomy authority. It is valid only when the cited profile is structurally valid, fresh, currently usable, exactly bound, and the unsatisfied set is empty. The deterministic reference implementation lives at `tools/executability.py`.

An executable assignment carries `execution_contract.assignment_draft_ref` equal
to the cited admissibility record's `assignment_draft_id`, plus the same exact
`runtime_identity`. Matching destination labels alone do not establish either
binding.
It also carries `execution_contract.route_ref` equal to the exact admitted route. The route's `EXECUTION_VERIFICATION` segment must exactly equal the assignment/admissibility `destination_id`, `runtime_identity`, and `capability_profile_ref`; `ASSIGNMENT.result_to` must equal the structured durable final endpoint.

## Capability vocabulary

Capability IDs describe concrete execution surfaces, not broad claims such as "can code". The vocabulary is extensible; prefer stable snake_case IDs. Common IDs include:

- `repository_remote_read`
- `repository_remote_write`
- `repository_local_checkout`
- `git_local_worktree`
- `shell`
- `python_runtime`
- `node_runtime`
- `php_runtime`
- `package_install`
- `interactive_browser`
- `playwright_runtime`
- `outbound_network`
- `deployment_access`
- `database_access`
- `ci_trigger`
- `ci_read`
- `external_task_submit`
- `external_task_ack_or_discover`
- `external_task_status_read`
- `external_task_result_read`
- `exact_target_bind`
- `pull_request_create`
- `remote_branch_write`
- `connector:<name>`

Capabilities may be narrower when necessary, for example `database_read:staging` or `deployment_access:preview`.

Capability IDs are exact facts, not prefixes or implication rules. Read does not imply mutation, and mutation does not follow from surface presence. In particular `repository_remote_read` does not imply `repository_remote_write`, `ci_read` does not imply `ci_trigger`, and a provider/log read capability does not imply production mutation. External execution is decomposed the same way: local or remote code execution does not imply task submission; submission does not imply acknowledgement/discovery, status read, result read, exact target binding, pull-request creation, or remote-branch mutation. Consumers compare required IDs against advertised IDs exactly; they MUST NOT infer broader authority from prefixes, provider names, prompts, or prose.

For work against an exact candidate, `exact_target_bind` must be independently
advertised and evidenced when the mandatory claim requires the adapter to prove
repository, pull request, branch, commit, or workspace binding. An instruction in
a remote prompt to discover or switch context is not evidence of that binding.
Likewise, `pull_request_create` and `remote_branch_write` are optional mutation
capabilities; neither follows from an external task reaching a completed state.

### Provider adapter boundary

A provider-specific adapter may map its physical operations and observations to
these provider-neutral capability IDs. For example, a currently documented
machine CLI may provide separate task submission and machine-readable discovery
or status observations, while a browser/UI relay may provide only the observations
that its runtime can prove. Command names, project URLs, recent-task navigation,
tabs, and DOM selectors remain private adapter physics. They MUST NOT become
universal `CAPABILITY_PROFILE` fields or portable capability semantics.

An adapter advertisement records observed current reality, not a permanent fact
about the provider. Experimental commands, optional provider permissions, and
provider support for opening a pull request or writing a branch must each be
freshly evidenced before the corresponding exact capability can participate in
admission.

Non-normative current example (2026-10-01): OpenAI documents
`codex cloud exec --env ENV_ID <query>` as a direct submission path whose
submission failure exits non-zero, and `codex cloud list --json` as a
machine-readable source containing task `id`, `url`, `status`, `environment_id`,
`summary`, and `attempt_total`. That is current evidence for a potential Codex
Cloud adapter's submit/discovery/status advertisement, not proof of result-read,
exact-target, pull-request, or branch-write capabilities and not universal Codex
semantics. The command remains documented as Experimental. A browser/UI adapter
may remain a physical fallback when it is the only advertised observation or
continuation path. Provider documentation:
<https://learn.chatgpt.com/docs/developer-commands?surface=cli>,
<https://learn.chatgpt.com/docs/cloud>, and
<https://learn.chatgpt.com/docs/third-party/github>.

## Mandatory-action derivation

Required capabilities are the union of capabilities needed by:

- the assignment's mandatory actions;
- selected workflow steps that are mandatory for this assignment;
- selected skill steps that are mandatory for this assignment;
- acceptance criteria;
- required verification/evidence gates;
- exact-state assertions that can only be established on a particular surface.

Optional steps do not become mandatory merely because a skill mentions them. Conversely, a mandatory acceptance criterion cannot be downgraded because the destination lacks the required surface.

## Modes and fallback

A skill/workflow may declare multiple supported execution modes, for example remote-repository mode and local-worktree mode. A fallback is admissible only if it proves the same required claim or the assignment explicitly accepts the weaker claim. Tool substitution never silently weakens evidence identity.

Examples:

- GitHub remote state can prove a PR HEAD but cannot prove an unpushed local HEAD.
- A repository connector can edit files but cannot satisfy a mandatory local test command unless an executable runtime is separately available.
- Playwright is not a browser-free fallback when Node/package/browser binaries are unavailable.

## Runtime drift after assignment

Executability proof is freshness-bounded. A capability or readiness state may change after a valid assignment. Current-executability revalidation MUST validate the newly cited current profile, including readiness, exact destination/runtime identity, freshness, and required capabilities. A non-usable current readiness fails closed before continuation. Capability loss after valid admission returns `BLOCKED_RUNTIME_DRIFT`; a profile that cannot be validated for current use requires current executability revalidation before continuation.

This is distinct from an assignment that was never admissible in the first place.

## Research semantics

Research `MACHINE_EXECUTABLE=true` / `CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS=true` are **method-level machine-only admission claims**. They mean the method does not depend on prohibited human labor and is representable as machine work. They are not destination-runtime proof.

Every Research assignment still requires this global destination executability preflight against its declared execution surface, source-access method, computation method, and verification method.

## Skill and pattern law

Every **new or substantively edited** reusable skill and Solution Pattern that can require external execution surfaces must declare:

- required execution capabilities;
- supported execution modes;
- conditional/optional capabilities;
- evidence path or equivalent fallback rules;
- unsupported-environment behavior.

### Migration compatibility for existing unannotated skills

Migration-preserved active skills/patterns that predate this contract are not automatically invalid merely because they do not yet contain a dedicated Execution contract section. Until each is explicitly annotated:

1. absence of a declaration means **execution prerequisites are UNKNOWN, not empty**;
2. before selecting that legacy skill/pattern for an assignment, the Control Director/router MUST inspect only that selected skill/pattern's mandatory procedure/evidence steps and derive concrete required capabilities from them;
3. if any mandatory prerequisite cannot be derived confidently, selection is `ASSIGNMENT_NOT_ADMISSIBLE` pending bounded capability clarification/annotation;
4. the router MUST NOT infer capability-free execution from missing metadata;
5. later bounded compatibility remediation may add declarations without changing the skill/pattern's proven procedural substance.

This compatibility rule preserves the migration invariant that legacy procedural substance was not silently rewritten while still preventing unannotated skills from bypassing destination preflight.

A pattern may remain valid even when the current destination cannot execute it. In that case selection is not admissible for that destination; the pattern itself is not defective merely for requiring a real runtime.
