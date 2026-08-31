# Engine — Research

## Purpose
Reduce project uncertainty and build evidence-backed research releases without mutating Canon.

## Default execution identity
`DEFAULT_RESEARCH_MODE = MACHINE_ONLY`.

The mandatory upstream constitution is `kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md`. No downstream project prompt, work package, method, or executor instruction may weaken it.

## Owns
- research-question admission;
- machine-executable research planning and work packages;
- source/evidence extraction;
- computational experiments and proxy analysis;
- automated verification, synthesis, adversarial validation, gap handling, and research release preparation;
- Canon reconciliation evidence packages.

## Does not own
- Owner/K0 project decisions;
- Canon acceptance or mutation;
- new project-generated human research in default mode;
- authority to convert proxy output into human evidence.

## Runtime rule
Load `MANIFEST.yaml`, the kernel machine-only constitution, and `RESEARCH_CONTROL_CONTRACT.md` before any project-specific Research Engine artifact. Admission and policy validation are fail-closed.
