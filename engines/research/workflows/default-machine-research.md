# Workflow — Default Machine Research

## Entry
Load the kernel constitution first. Validate the candidate question before creating any work package. Method-level machine-only admission and destination-runtime executability are separate gates.

## Steps
1. `R0`: assemble research control state and stable identities.
2. `R-WHAT`: classify target construct and submit question-admission object.
3. Automated verifier runs `validate_question`. On failure, return `REJECT_METHOD / REQUIRE_MACHINE_REDESIGN`; do not activate the question.
4. If genuine project-scope authority is needed, emit an `OWNER_SCOPE_GATE`; Owner/K0 decides only the project choice.
5. `R-WHERE`: select machine-accessible sources and methods. Every source record must pass `validate_source` before admission; external/pre-existing human-derived sources are source material only and cannot become project-generation methods.
6. Create a work package from `templates/research-work-package.yaml`; automated verifier runs `validate_work_package`. `MACHINE_EXECUTABLE=true` / `CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS=true` prove method-level machine-only admission only; they do not prove the current destination runtime.
7. Derive concrete destination requirements from `EXECUTION_SURFACE`, `SOURCE_ACCESS_METHOD`, `COMPUTATION_METHOD`, `VERIFICATION_METHOD`, and every mandatory validator/check for the next assignment. Bind an exact destination `CAPABILITY_PROFILE` and materialize `ASSIGNMENT_ADMISSIBILITY` under `contracts/EXECUTABILITY_CONTRACT.md`.
8. If required capabilities are not a subset of the destination's available capabilities, return `ASSIGNMENT_NOT_ADMISSIBLE` and choose another already-authorized machine mode/destination or redesign the method. Do not intentionally activate an executor/verifier that is known unable to run the mandatory validators/evidence path.
9. Before a method freeze can become authoritative, construct the freeze object and run `validate_method_freeze` on an admissible destination. `METHOD_FROZEN=true` is valid only when semantic machine-only validation passes and the required validation action was actually executable/performed.
10. Execute machine research and evidence extraction on the destination/mode named by the assignment execution contract. Every computational experiment object must pass `validate_experiment` before execution/result admission; field names are structural and semantic checks apply recursively to values.
11. Automated adversarial validation checks provenance, reproducibility, contradiction handling, proxy labeling, prohibited overclaim, source admission, experiment validity, and freeze integrity. Verification assignments receive their own destination executability preflight.
12. Gaps are handled with machine methods or explicit unknown/insufficient-evidence outcomes.
13. Owner/K0 may adjudicate research sufficiency or priorities if a project decision is genuinely required.
14. Release controller freezes the research release and emits the Canon reconciliation package. Research does not mutate Canon; any mandatory release validator/output surface must be preflighted before assignment.

## Stop conditions
Stop the invalid method, not the whole research project, when a downstream instruction requests prohibited human participation. A rejected method returns a machine-executable redesign if feasible; otherwise return an explicit limitation state.

Known missing runtime capability before assignment is not a research result and not `BLOCKED_PENDING_HUMANS`; it is `ASSIGNMENT_NOT_ADMISSIBLE` for that destination/mode. Loss of a capability after a valid assignment is `BLOCKED_RUNTIME_DRIFT` and returns to control for fresh admissibility.

## Human-research boundary
No transition in this workflow enters human research. A separately authorized `human-research/` namespace is outside this workflow. Its authorization is valid only when `validate_human_research_authorization` revalidates the exact durable `OWNER_DECISION_RECORD` that created the bounded workstream; an authorization object without resolvable Owner/K0 provenance is invalid and never changes default Research mode.
