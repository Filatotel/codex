# Workflow — Default Machine Research

## Entry
Load the kernel constitution first. Validate the candidate question before creating any work package.

## Steps
1. `R0`: assemble research control state and stable identities.
2. `R-WHAT`: classify target construct and submit question-admission object.
3. Automated verifier runs `validate_question`. On failure, return `REJECT_METHOD / REQUIRE_MACHINE_REDESIGN`; do not activate the question.
4. If genuine project-scope authority is needed, emit an `OWNER_SCOPE_GATE`; Owner/K0 decides only the project choice.
5. `R-WHERE`: select machine-accessible sources and methods.
6. Create a work package from `templates/research-work-package.yaml`; automated verifier runs `validate_work_package`.
7. Execute machine research, evidence extraction, experiments, and finding synthesis.
8. Automated adversarial validation checks provenance, reproducibility, contradiction handling, proxy labeling, and prohibited overclaim.
9. Gaps are handled with machine methods or explicit unknown/insufficient-evidence outcomes.
10. Owner/K0 may adjudicate research sufficiency or priorities if a project decision is genuinely required.
11. Release controller freezes the research release and emits the Canon reconciliation package. Research does not mutate Canon.

## Stop conditions
Stop the invalid method, not the whole research project, when a downstream instruction requests prohibited human participation. A rejected method returns a machine-executable redesign if feasible; otherwise return an explicit limitation state.

## Human-research boundary
No transition in this workflow enters human research. A separately authorized `human-research/` namespace is outside this workflow.
