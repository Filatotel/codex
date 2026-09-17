# Engine — Research

## Purpose
Reduce project uncertainty, build evidence-backed research releases, and reconcile already-durable Research outputs into bounded dependency/control state without mutating Canon.

## Default execution identity
`DEFAULT_RESEARCH_MODE = MACHINE_ONLY`.

The mandatory upstream constitution is `kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md`. No downstream project prompt, work package, method, or executor instruction may weaken it.

## Owns
- research-question admission;
- machine-executable research planning and work packages;
- source/evidence extraction;
- computational experiments and proxy analysis;
- automated verification, synthesis, adversarial validation, gap handling, and research release preparation;
- read-only Research-chain reconciliation over exact durable upstream Research artifacts;
- Canon reconciliation evidence packages.

## Does not own
- Owner/K0 project decisions;
- Canon acceptance or mutation;
- global Control Director authority;
- direct spawn/dispatch of candidate next Research;
- new project-generated human research in default mode;
- authority to convert proxy output into human evidence.

## Runtime rule
Load `MANIFEST.yaml`, the kernel machine-only constitution, and `RESEARCH_CONTROL_CONTRACT.md` before any project-specific Research Engine artifact. Admission and policy validation are fail-closed.

Actual Research execution continues through the normal Research question/work-package admission path. `reconcile_research_chain` is a separate read-only control-interpretation capability over already-durable Research artifacts: it does not itself call `tools.research_policy.admit_work_package()`, execute Research, or confer dispatch or Canon-mutation authority.
