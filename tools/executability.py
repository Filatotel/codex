#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping


def _normalize(values: Iterable[str]) -> list[str]:
    return sorted({value.strip() for value in values if isinstance(value, str) and value.strip()})


def evaluate_assignment_admissibility(
    required_capabilities: Iterable[str],
    available_capabilities: Iterable[str],
) -> dict[str, object]:
    """Return the deterministic subset result for one destination capability profile."""
    required = _normalize(required_capabilities)
    available = _normalize(available_capabilities)
    missing = sorted(set(required) - set(available))
    return {
        "status": "ADMISSIBLE" if not missing else "NOT_ADMISSIBLE",
        "required_capabilities": required,
        "available_capabilities": available,
        "unsatisfied_required_capabilities": missing,
    }


def validate_admissibility_record(record: Mapping[str, object]) -> list[str]:
    """Validate that a durable ASSIGNMENT_ADMISSIBILITY record matches the subset calculation."""
    errors: list[str] = []
    required = record.get("required_capabilities")
    available = record.get("available_capabilities")
    missing = record.get("unsatisfied_required_capabilities")
    status = record.get("status")

    if not isinstance(required, list) or not all(isinstance(v, str) for v in required):
        return ["required_capabilities must be a list of strings"]
    if not isinstance(available, list) or not all(isinstance(v, str) for v in available):
        return ["available_capabilities must be a list of strings"]
    if not isinstance(missing, list) or not all(isinstance(v, str) for v in missing):
        return ["unsatisfied_required_capabilities must be a list of strings"]

    expected = evaluate_assignment_admissibility(required, available)
    if status != expected["status"]:
        errors.append(f"status drift: expected {expected['status']}, got {status}")
    if _normalize(missing) != expected["unsatisfied_required_capabilities"]:
        errors.append(
            "unsatisfied_required_capabilities drift: "
            f"expected {expected['unsatisfied_required_capabilities']}, got {_normalize(missing)}"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Project Resolver destination executability")
    parser.add_argument("--required", nargs="*", default=[])
    parser.add_argument("--available", nargs="*", default=[])
    parser.add_argument("--record", help="Validate an ASSIGNMENT_ADMISSIBILITY JSON file")
    args = parser.parse_args()

    if args.record:
        with open(args.record, "r", encoding="utf-8") as handle:
            record = json.load(handle)
        errors = validate_admissibility_record(record)
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1

    result = evaluate_assignment_admissibility(args.required, args.available)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ADMISSIBLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
