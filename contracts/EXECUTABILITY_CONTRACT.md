# Destination Executability Contract

This contract prevents Project Resolver from assigning mandatory work to a destination instance that cannot physically perform or prove it.

## Kernel law

**NO ASSIGNMENT WITHOUT EXECUTABILITY PROOF.**

Before `ASSIGN`, the Control Director MUST establish for the exact destination instance:

```text
REQUIRED_CAPABILITIES ⊆ AVAILABLE_CAPABILITIES
```

The comparison covers every mandatory action and every mandatory acceptance/evidence gate, not only the engine's semantic capability.

If the subset relation is not proven, the work is **not an executable assignment for that destination**. Return `ASSIGNMENT_NOT_ADMISSIBLE`, choose another already-authorized executable destination/mode, or escalate. Do not intentionally issue the assignment and wait for the Executor/Verifier to discover the missing runtime later.

## Three separate questions

1. **Semantic ownership:** which engine conceptually owns the transformation?
2. **Authority:** is the requested action authorized?
3. **Destination executability:** can this exact destination instance perform every mandatory action and obtain every mandatory evidence path here?

All three must pass. Semantic capability never implies runtime capability.

## CAPABILITY_PROFILE

A `CAPABILITY_PROFILE` is a freshness-bounded observation of the execution surfaces available to one exact destination instance.

It records:

- destination/runtime identity;
- observed available capabilities;
- unavailable or explicitly excluded capabilities;
- evidence/source for capability claims;
- freshness boundary and limitations.

A capability profile is evidence about a runtime, not authority to use that capability.

For deterministic admission, the profile freshness boundary contains timezone-aware
`observed_at` and `valid_until` timestamps. `valid_until` must still be in the future.
Every available capability cites a separately represented, `RESOLVED`
`CAPABILITY_EVIDENCE` artifact embedded in `evidence_artifacts`; that artifact must
name the same exact `runtime_identity`, prove the cited capability, and remain valid
for the whole profile freshness boundary. An arbitrary or unresolved string is not
capability evidence.

## ASSIGNMENT_ADMISSIBILITY

An `ASSIGNMENT_ADMISSIBILITY` record binds an assignment draft to an exact destination and capability profile. It records:

- required capabilities derived from mandatory actions and mandatory evidence gates;
- available capabilities from the destination profile;
- unsatisfied required capabilities;
- mandatory evidence paths;
- selected execution mode/fallback, if any;
- `ADMISSIBLE` or `NOT_ADMISSIBLE`.

`ADMISSIBLE` is valid only when the unsatisfied set is empty. The deterministic reference implementation lives at `tools/executability.py`.

An executable assignment carries `execution_contract.assignment_draft_ref` equal
to the cited admissibility record's `assignment_draft_id`, plus the same exact
`runtime_identity`. Matching destination labels alone do not establish either
binding.

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
- `connector:<name>`

Capabilities may be narrower when necessary, for example `database_read:staging` or `deployment_access:preview`.

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

Executability proof is freshness-bounded. A capability may disappear after a valid assignment. In that case the Executor/Verifier truthfully returns `BLOCKED_RUNTIME_DRIFT` with evidence. Control then re-runs admissibility before reassignment.

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
