# Foundation V0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Materialize the planned `foundation` Engine so a routed raw project idea can become durable, explicitly non-authoritative working project state without prematurely creating Canon, Research, or Production authority.

**Architecture:** Add one `foundation` Engine with one `form_project_foundation` workflow, four cognitive skills, and three Foundation-owned durable artifact schemas. Reuse the existing Router, Assignment Compiler, executability/admissibility chain, durable-output/readback contract, shared Executor/Control Director roles, and common artifact envelope; do not create a Foundation-specific runtime or second control plane.

**Tech Stack:** Markdown skill/workflow contracts, YAML engine registry/manifest, JSON Schema Draft 2020-12, Python `unittest` regression tests, existing `tools/resolver_spawn.py` and GitHub Actions `Project Resolver CI`.

**Spec:** `docs/superpowers/specs/2026-10-04-foundation-v0-design.md`

## Global Constraints

- `RAW OWNER IDEA != PROJECT_SEED != CANON`.
- Foundation artifacts are durable working state and MUST be machine-checkably non-authoritative.
- Foundation V0 exposes one root semantic capability only: `form_project_foundation`.
- Required skills: `develop-project-seed`, `define-project-outcome`, `classify-consequential-unknowns`; `design-discovery` is optional and loaded only when materially useful.
- No fixed questionnaire and no mandatory minimum question count; zero clarification questions is valid.
- Skills are guidance-first; hard invariants are reserved for authority/evidence/provenance boundaries.
- Foundation MUST NOT invent Owner intent, accept/mutate Canon, auto-dispatch Research, start Production, freeze architecture, or treat model memory as external evidence.
- Foundation V0 creates exactly three Engine-owned durable artifact types: `PROJECT_SEED`, `PROJECT_OUTCOME`, `CONSEQUENTIAL_UNKNOWN_MAP`.
- `FOUNDATION_READY_FOR_OWNER_GATE` is a workflow/result status, not a fourth durable artifact type and not an Owner decision.
- `FOUNDATION_READY_FOR_OWNER_GATE` is allowed only after the assignment-declared three durable outputs are materialized and satisfy the existing durable-output/reference/readback contract.
- Reuse `roles/executor/ROLE.md` and `roles/control-director/ROLE.md`; do not create a Foundation persona.
- Reuse the common artifact envelope and generic resolver/executability machinery; no Foundation-specific spawn/runtime path.
- `NO GLOBAL SKILL DISCOVERY` remains in force.
- The exact Owner Foundation Gate and handoff into Canon are a later #53 wave and are not implemented here.

## Review Focus

- A fully specified Owner idea must be able to form useful working state with **zero** clarification questions; tests must reject any fixed-question-count contract.
- A plausible model proposal must remain distinguishable from explicit Owner intent and must not become authoritative merely because it appears in a durable Foundation artifact.
- An `EXTERNAL_FACT` or `FEASIBILITY` unknown must remain a classified unknown; Foundation must not imply that Research has been dispatched or evidence obtained.
- Straightforward project formation must not load `design-discovery` unconditionally; required/optional skill composition must be explicit and testable.
- A result claiming `FOUNDATION_READY_FOR_OWNER_GATE` without all three assignment-declared durable outputs/readback requirements must be invalid under the existing generic durable completion semantics.

---

## File Structure

**Create**
- `engines/foundation/MANIFEST.yaml` — Foundation ownership, workflow composition, capability mapping, execution boundaries.
- `engines/foundation/workflows/form-project-foundation.md` — single V0 formation workflow and STOP boundary.
- `engines/foundation/skills/develop-project-seed/SKILL.md` — working project concept formation.
- `engines/foundation/skills/define-project-outcome/SKILL.md` — desired completion/outcome reasoning.
- `engines/foundation/skills/classify-consequential-unknowns/SKILL.md` — bounded uncertainty classification.
- `engines/foundation/skills/design-discovery/SKILL.md` — optional exploratory reasoning before Canon.
- `engines/foundation/schemas/project-seed.schema.json` — non-authoritative `PROJECT_SEED` schema.
- `engines/foundation/schemas/project-outcome.schema.json` — non-authoritative `PROJECT_OUTCOME` schema.
- `engines/foundation/schemas/consequential-unknown-map.schema.json` — non-authoritative unknown-map schema.
- `tests/test_foundation_materialization.py` — Foundation registry, schema, skill, workflow, routing, authority and durable-output integration tests.

**Modify**
- `SYSTEM_MANIFEST.yaml` — move `foundation` from `planned_engines` to `engine_registry: available` with `form_project_foundation`.
- `ROUTER.md` — add Foundation progressive-disclosure route and remove Foundation from the generic non-materialized gate wording.
- `protocols/artifacts.md` — document the three Engine-owned Foundation durable types without adding them to the universal required-common-type ontology.
- `tools/validate_structure.py` — structurally require the active Foundation manifest/workflow/schemas and root registration once the Engine becomes available.
- `tests/test_v0_structure.py` or `tests/test_structure.py` — extend structural regression coverage for Foundation registration as appropriate to the existing validator test split.

No production Python module is added for Foundation-specific orchestration. `tools/resolver_spawn.py` remains the generic spawn path.

---

### Task 1: Foundation Artifact Schemas and Non-Authority Contract

**Files:**
- Create: `engines/foundation/schemas/project-seed.schema.json`
- Create: `engines/foundation/schemas/project-outcome.schema.json`
- Create: `engines/foundation/schemas/consequential-unknown-map.schema.json`
- Create: `tests/test_foundation_materialization.py`
- Modify: `protocols/artifacts.md`

**Interfaces:**
- Consumes: common envelope fields defined by `protocols/artifacts.md`: `artifact_id`, `artifact_type`, `produced_by_role`, `assignment_id`, `input_state_ref`, `status`, `provenance`, `related_artifacts`.
- Produces: closed JSON Schemas for `PROJECT_SEED`, `PROJECT_OUTCOME`, `CONSEQUENTIAL_UNKNOWN_MAP`, each with a machine-checkable non-authority field fixed to `false`.

- [ ] **Step 1: Write failing schema/envelope tests**

Add `FoundationMaterializationTest` cases that assert:

```python
ENVELOPE.issubset(set(schema["required"]))
schema["properties"]["artifact_type"]["const"] == expected_type
schema_accepts(valid_artifact, schema)
not schema_accepts({**valid_artifact, "authoritative": True}, schema)
```

Also assert the unknown-map classification enum is exactly:

```python
{
    "OWNER_PREFERENCE",
    "EXTERNAL_FACT",
    "FEASIBILITY",
    "ARCHITECTURE_DECISION",
    "IMPLEMENTATION_DEPENDENT",
    "NICE_TO_KNOW",
}
```

and that schemas are closed with `additionalProperties: false`.

- [ ] **Step 2: Run the focused test to prove RED**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: FAIL because the three Foundation schema files do not exist.

- [ ] **Step 3: Implement the three schemas**

Use JSON Schema Draft 2020-12. Each schema MUST require the common envelope plus:

`PROJECT_SEED`:
- `authoritative: {"const": false}`
- non-empty `working_summary`
- bounded arrays for `protected_owner_intent`, `constraints`, `non_goals`, `known_decisions`, `working_interpretations`, `model_proposals`, `material_question_refs`; arrays may be empty and most semantic dimensions remain optional rather than mandatory form fields.

`PROJECT_OUTCOME`:
- `authoritative: {"const": false}`
- non-empty `target_outcome`
- `completion_condition` as non-empty string or explicit null/open representation
- `required_deliverables` array
- optional `optional_deliverables`, `audience`, `non_goals`
- `requires_downstream_realization` as boolean or explicit unknown enum/string consistent with the schema design.

`CONSEQUENTIAL_UNKNOWN_MAP`:
- `authoritative: {"const": false}`
- `items` array of closed objects requiring `id`, `question`, `classification`, `why_it_matters`, `state`
- `classification` exact V0 enum above
- `state` bounded to `OPEN | DEFERRED` for V0.

Do not add Owner/Canon authority fields that could imply acceptance.

- [ ] **Step 4: Document Engine-owned artifact types without universalizing them**

In `protocols/artifacts.md`, add a short section stating that Foundation owns the three artifact types and that they use the common envelope but are not universal required common artifact types and carry no semantic authority.

- [ ] **Step 5: Run focused tests to prove GREEN**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: schema/envelope/non-authority tests PASS.

- [ ] **Step 6: Commit**

```bash
git add engines/foundation/schemas tests/test_foundation_materialization.py protocols/artifacts.md
git commit -m "feat: define Foundation working-state artifacts"
```

---

### Task 2: Foundation Cognitive Skills

**Files:**
- Create: `engines/foundation/skills/develop-project-seed/SKILL.md`
- Create: `engines/foundation/skills/define-project-outcome/SKILL.md`
- Create: `engines/foundation/skills/classify-consequential-unknowns/SKILL.md`
- Create: `engines/foundation/skills/design-discovery/SKILL.md`
- Modify: `tests/test_foundation_materialization.py`

**Interfaces:**
- Consumes: Liaison bounded routing frame, explicit Owner material, native LLM reasoning, and only directly relevant project context.
- Produces: cognitive instructions that populate/refine the three Foundation working artifacts while preserving Owner/model/proposal/evidence distinctions; no separate durable result for `design-discovery`.

- [ ] **Step 1: Write failing skill-contract tests**

Add tests asserting all four skill files:
- have unique frontmatter `name` values matching their directory names;
- contain `## Execution contract`, `## Thinking guidance`, `## Hard invariants`, `## Procedure`;
- explicitly preserve native model reasoning / judgment;
- explicitly state that durable output does not create Canon/Owner authority.

Add behavior assertions:

```python
self.assertNotRegex(all_skill_text, r"(?i)(ask|require).*(at least|minimum)\s+[1-9][0-9]*\s+(questions|fields)")
self.assertIn("zero clarification", seed_or_workflow_text.lower())
```

and assert `design-discovery` states it is optional and creates no `DESIGN_DISCOVERY_RESULT` artifact.

- [ ] **Step 2: Run focused tests to prove RED**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: FAIL because Foundation skill files do not exist.

- [ ] **Step 3: Implement `develop-project-seed`**

Follow the approved spec. It MUST distinguish:
- explicit Owner statement;
- strongly implied context;
- model working interpretation;
- model proposal;
- unresolved material question.

Thinking guidance should encourage inference/reframing/judgment. Hard invariants should be limited to Owner intent, evidence, Canon, authority, provenance, and global-discovery boundaries.

- [ ] **Step 4: Implement `define-project-outcome`**

Guide reasoning about target outcome, completion condition, deliverables, audience/non-goals when material, and whether realization is required. Explicitly prohibit assuming software/Production by default.

- [ ] **Step 5: Implement `classify-consequential-unknowns`**

Use exactly the six V0 classes. State explicitly that classification is not resolution, Research dispatch, Owner decision, or architecture authority. Non-consequential unknowns need not be materialized.

- [ ] **Step 6: Implement optional `design-discovery`**

Allow proposal/comparison/reframing/scope simplification/trade-off exploration. Explicitly preserve proposal status and prohibit architecture freeze by plausibility. Do not define a fourth durable artifact.

- [ ] **Step 7: Run focused tests to prove GREEN**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: all skill-contract and cognitive-freedom tests PASS.

- [ ] **Step 8: Commit**

```bash
git add engines/foundation/skills tests/test_foundation_materialization.py
git commit -m "feat: add Foundation cognitive skills"
```

---

### Task 3: Foundation Manifest and Formation Workflow

**Files:**
- Create: `engines/foundation/MANIFEST.yaml`
- Create: `engines/foundation/workflows/form-project-foundation.md`
- Modify: `tests/test_foundation_materialization.py`

**Interfaces:**
- Consumes: generic `exact_assignment`, destination `CAPABILITY_PROFILE`, `ASSIGNMENT_ADMISSIBILITY`, Liaison route frame, Owner material/provenance.
- Produces: Engine capability mapping `form_project_foundation -> form_project_foundation`; required skill set of three skills plus optional `design-discovery`; workflow terminal status `FOUNDATION_READY_FOR_OWNER_GATE` only after generic durable completion/readback requirements are satisfied.

- [ ] **Step 1: Write failing manifest/workflow tests**

Assert:

```python
manifest contains "engine_id: foundation"
manifest contains "status: available"
capability mapping is exactly {"form_project_foundation"}
workflow names roles/executor/ROLE.md and roles/control-director/ROLE.md
required skills are exactly the three required Foundation skills
optional skills contain exactly design-discovery
```

Also assert `does_not_own` includes Owner authority, Canon acceptance/mutation, substantive Research, Production, independent Verification, generic orchestration and transport.

- [ ] **Step 2: Add RED tests for readiness/durability wording**

The workflow test MUST assert that `FOUNDATION_READY_FOR_OWNER_GATE` requires all three declared durable outputs to have exact refs/readback under the existing generic durable contract, and that the workflow STOPs before Owner gate, Canon, Research dispatch and Production.

- [ ] **Step 3: Run focused tests to prove RED**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: FAIL because manifest/workflow do not exist.

- [ ] **Step 4: Implement `engines/foundation/MANIFEST.yaml`**

Follow existing Engine manifest conventions. Define:
- ownership and explicit non-ownership boundaries;
- shared Executor/Control Director roles;
- one workflow;
- one capability mapping;
- `workflow_contracts.form_project_foundation.required_skills` with the three required skills;
- `optional_skills` with `design-discovery` only;
- generic executability contract reference;
- `global_skill_discovery: forbidden`;
- outputs listing the three Foundation artifacts plus ordinary executor/workflow result.

Do not add a Foundation-specific spawn tool.

- [ ] **Step 5: Implement `form-project-foundation.md`**

Encode the approved reasoning sequence and allow internal iteration without questionnaire behavior. The workflow MUST require assignment declaration/materialization/readback of:
- `PROJECT_SEED`;
- `PROJECT_OUTCOME`;
- `CONSEQUENTIAL_UNKNOWN_MAP`.

The status `FOUNDATION_READY_FOR_OWNER_GATE` is permitted only after those outputs satisfy generic durable completion/readback rules. Otherwise return the smallest bounded clarification/blocker. STOP before the future Owner Foundation Gate.

- [ ] **Step 6: Run focused tests to prove GREEN**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: manifest/workflow composition and boundary tests PASS.

- [ ] **Step 7: Commit**

```bash
git add engines/foundation/MANIFEST.yaml engines/foundation/workflows tests/test_foundation_materialization.py
git commit -m "feat: materialize Foundation formation workflow"
```

---

### Task 4: Root Registry and Router Activation

**Files:**
- Modify: `SYSTEM_MANIFEST.yaml`
- Modify: `ROUTER.md`
- Modify: `tests/test_foundation_materialization.py`

**Interfaces:**
- Consumes: `form_project_foundation` semantic capability selected after Liaison `ROUTE`.
- Produces: root Engine registration pointing at `engines/foundation/MANIFEST.yaml` and Router route to the Foundation workflow through the existing compiler/executability chain.

- [ ] **Step 1: Write failing registry/router tests**

Assert Foundation:
- exists once in `engine_registry`;
- has `status: available`;
- points at `engines/foundation/MANIFEST.yaml`;
- advertises only `form_project_foundation`;
- no longer appears under `planned_engines`;
- has a Router current-route row `form_project_foundation | foundation`;
- is excluded from the `ENGINE_NOT_MATERIALIZED` example/gate wording.

Also assert Router says Foundation loads its manifest/workflow/required skills and optional `design-discovery` only when selected, with no global discovery.

- [ ] **Step 2: Run focused tests to prove RED**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: FAIL because root registry still marks Foundation `not_materialized` and Router has no active route.

- [ ] **Step 3: Update `SYSTEM_MANIFEST.yaml`**

Move Foundation from `planned_engines` into `engine_registry` with:

```yaml
- engine_id: foundation
  manifest_path: engines/foundation/MANIFEST.yaml
  status: available
  capabilities:
    - form_project_foundation
```

Entry conditions must preserve the generic authority/state/assignment/executability chain without inventing Canon authority.

- [ ] **Step 4: Update `ROUTER.md`**

Add Foundation progressive-disclosure guidance and a current route for `form_project_foundation`. Preserve the generic compiler, destination preflight and role activation chain. Update the non-materialized gate so it refers only to still-unmaterialized engines such as `production/other-domains`.

- [ ] **Step 5: Run focused tests to prove GREEN**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: registry/router activation tests PASS.

- [ ] **Step 6: Commit**

```bash
git add SYSTEM_MANIFEST.yaml ROUTER.md tests/test_foundation_materialization.py
git commit -m "feat: activate Foundation Engine routing"
```

---

### Task 5: Generic Resolver and Durable-Output Integration

**Files:**
- Modify: `tests/test_foundation_materialization.py`
- Reference only: `tools/resolver_spawn.py`
- Reference only: existing durable-output/readback tests and contracts

**Interfaces:**
- Consumes: existing `bundle(engine_id, capability, workflow)` test helper / generic resolver inputs, selected prerequisite capability `durable_artifact_write`, assignment `required_durable_outputs`, and `durable_system_of_record_ref`.
- Produces: proof that Foundation reaches generic `SPAWN_READY` without a Foundation-specific runtime and that incomplete durable output coverage cannot count as complete/readback-proven formation.

- [ ] **Step 1: Write representative generic-spawn RED test**

Create a Foundation bundle using the existing test helper pattern:

```python
value = bundle("foundation", "form_project_foundation", "form_project_foundation")
```

Declare the mandatory durable-write prerequisite and the three required durable output identities. Assert expected result:

```python
(result["control_state"], result["status"]) == ("ASSIGN", "SPAWN_READY")
result["engine_id"] == "foundation"
result["assignment_admissibility"]["status"] == "ADMISSIBLE"
"durable_artifact_write" in result["assignment_admissibility"]["required_capabilities"]
```

Before Task 4 activation this test must fail with `ENGINE_NOT_MATERIALIZED` or equivalent route-state mismatch.

- [ ] **Step 2: Add fail-closed tests for generic durability**

Using the existing durable-output contract helpers/patterns, assert:
- missing one of the three required output identities cannot produce generic `COMPLETE`;
- duplicate/wrong output identity cannot satisfy the assignment;
- a returned artifact ref without independent readback does not establish readback proof;
- local/session copy cannot replace system-of-record readback.

Do not add Foundation-specific production logic for behavior already enforced by generic contracts.

- [ ] **Step 3: Run focused Foundation + durable tests**

Run:

```bash
python -m unittest \
  tests.test_foundation_materialization \
  tests.test_durable_output_contract \
  tests.test_durable_readback_enforcement -v
```

Expected: PASS after root activation, with no modification required to `tools/resolver_spawn.py` unless a genuine generic bug is exposed.

- [ ] **Step 4: If the generic resolver fails only because it hard-codes the old Engine set, fix the smallest generic defect**

Only if Step 3 proves a real generic blocker, update the existing generic registry/selection code rather than creating `resolve_foundation_spawn()`. Add the regression to the Foundation test. If no blocker exists, leave production Python unchanged.

- [ ] **Step 5: Commit**

```bash
git add tests/test_foundation_materialization.py
git commit -m "test: prove Foundation generic resolver integration"
```

If a generic production fix was required, include only the exact affected generic file in the same commit.

---

### Task 6: Structural Registration Gate

**Files:**
- Modify: `tools/validate_structure.py`
- Modify: `tests/test_v0_structure.py` or `tests/test_structure.py`
- Modify: `tests/test_foundation_materialization.py` only if Foundation-specific structural assertions belong there.

**Interfaces:**
- Consumes: active Foundation registration from Tasks 1-4.
- Produces: repository structural validation that fails if the active Foundation manifest/workflow/schemas disappear or the root manifest points to the wrong paths.

- [ ] **Step 1: Write failing structural tests**

Add assertions that validator source/runtime structurally requires at least:
- `engines/foundation/MANIFEST.yaml`;
- `engines/foundation/workflows/form-project-foundation.md`;
- all three Foundation schema paths;
- root manifest registration `manifest_path: engines/foundation/MANIFEST.yaml` and `form_project_foundation`.

Do not structurally require every skill body by hard-coded global scan if the manifest/workflow already owns exact required/optional skill paths; validate those declared paths through bounded Foundation-specific checks.

- [ ] **Step 2: Run structural test to prove RED**

Run: `python -m unittest tests.test_v0_structure tests.test_structure -v`

Expected: FAIL because validator does not yet protect Foundation registration.

- [ ] **Step 3: Extend `tools/validate_structure.py` minimally**

Add Foundation active-surface/path/registration checks while preserving all existing validator behavior. Do not replace or weaken prior structural checks.

- [ ] **Step 4: Run structural tests to prove GREEN**

Run: `python -m unittest tests.test_v0_structure tests.test_structure -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/validate_structure.py tests/test_v0_structure.py tests/test_structure.py
git commit -m "test: protect Foundation structural registration"
```

Add only files actually changed.

---

### Task 7: Full Regression, Diff Audit, and PR

**Files:**
- No planned new product files.
- Update the PR body only after verification evidence exists.

**Interfaces:**
- Consumes: all previous tasks.
- Produces: one reviewable Foundation V0 PR against exact current `main`, with full CI evidence and no Owner Foundation Gate/Canon/Research/Production scope creep.

- [ ] **Step 1: Run Foundation-focused suite**

Run: `python -m unittest tests.test_foundation_materialization -v`

Expected: PASS.

- [ ] **Step 2: Run full repository suite**

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS.

- [ ] **Step 3: Run structural validator directly**

Run: `python tools/validate_structure.py`

Expected: `Project Resolver structural validation: PASS`.

- [ ] **Step 4: Audit the branch diff against the exact base**

Confirm only approved Foundation V0 surfaces changed. Specifically verify there is no:
- Owner Foundation Gate implementation;
- Canon mutation/acceptance change;
- automatic Research dispatch;
- Production work;
- PAK/SBC/provider transport work;
- Foundation-specific resolver/runtime fork;
- fourth Foundation durable artifact.

- [ ] **Step 5: Open a draft PR against `main`**

PR title: `Foundation V0: materialize pre-Canon project formation`

PR body must include:
- issue #53 and spec/plan paths;
- exact base/head SHA;
- the three durable artifact types;
- four skills with `design-discovery` marked optional;
- explicit non-authority/STOP boundary;
- TDD evidence;
- full suite + structural validator evidence;
- explicit statement that Owner Foundation Gate → Canon remains a later wave.

- [ ] **Step 6: Verify GitHub Actions on the exact PR HEAD/merge ref**

Require `Project Resolver CI` success for the exact head being proposed. If the PR head moves, use the latest run only.

- [ ] **Step 7: Do not merge without separate Owner/K0 authorization**

Return the exact PR/head/CI status to Owner. Merge only after an explicit Owner/K0 instruction.
