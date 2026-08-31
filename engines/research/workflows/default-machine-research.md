# Workflow — Default Machine Research

## Entry
Load the kernel constitution first. Validate the candidate question before creating any work package.

## Steps
1. `R0`: assemble research control state and stable identities.
2. `R-WHAT`: classify target construct and submit question-admission object.
3. Automated verifier runs `validate_question`. On failure, return `REJECT_METHOD / REQUIRE_MACHINE_REDESIGN`; do not activate the question.
4. If genuine project-scope authority is needed, emit an `OWNER_SCOPE_GATE`; Owner/K0 decides only the project choice.
5. `R-WHERE`: select machine-accessible sources and methods. Every source record must pass `validate_source` before admission; external/pre-existing human-derived sources are source material only and cannot become project-generation methods.
6. Create a work package from `templates/research-work-package.yaml`; automated verifier runs `validate_work_package`.
7. Before a method freeze can become authoritative, construct the freeze object and run `validate_method_freeze`. `METHOD_FROZEN=true` is valid only when that semantic machine-only validation passes.
8. Execute machine research and evidence extraction. Every computational experiment object must pass `validate_experiment` before execution/result admission; field names are structural and semantic checks apply recursively to values.
9. Automated adversarial validation checks provenance, reproducibility, contradiction handling, proxy labeling, prohibited overclaim, source admission, experiment validity, and freeze integrity.
10. Gaps are handled with machine methods or explicit unknown/insufficient-evidence outcomes.
11. Owner/K0 may adjudicate research sufficiency or priorities if a project decision is genuinely required.
12. Release controller freezes the research release and emits the Canon reconciliation package. Research does not mutate Canon.

## Stop conditions
Stop the invalid method, not the whole research project, when a downstream instruction requests prohibited human participation. A rejected method returns a machine-executable redesign if feasible; otherwise return an explicit limitation state.

## Human-research boundary
No transition in this workflow enters human research. A separately authorized `human-research/` namespace is outside this workflow. Its authorization is valid only when `validate_human_research_authorization` revalidates the exact durable `OWNER_DECISION_RECORD` that created the bounded workstream; an authorization object without resolvable Owner/K0 provenance is invalid and never changes default Research mode.
