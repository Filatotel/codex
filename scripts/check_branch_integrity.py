#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

REQUIRED_LABELS = [
    "Current branch:",
    "Target branch:",
    "Base SHA:",
    "Current HEAD SHA:",
    "Merge base SHA:",
    "Risk level:",
]


def find_branch_state_file(root: Path) -> Path | None:
    direct = root / "BRANCH_STATE.md"
    if direct.exists():
        return direct

    candidate = root / "templates" / "BRANCH_STATE.md"
    if candidate.exists():
        return candidate

    return None


def main() -> int:
    root = Path.cwd()
    path = find_branch_state_file(root)
    if path is None:
        print("No BRANCH_STATE.md found in current directory or templates/.")
        return 1

    text = path.read_text(encoding="utf-8")
    missing: list[str] = []

    for label in REQUIRED_LABELS:
        if label not in text:
            missing.append(label)

    if missing:
        print(f"Branch state file is missing required labels in {path}:")
        for item in missing:
            print(f"- {item}")
        return 1

    sha_fields = re.findall(r"SHA:\s*(.*)", text)
    empty_sha = [value for value in sha_fields if not value.strip()]
    if empty_sha:
        print(f"Branch state file {path} contains empty SHA fields.")
        return 1

    print(f"Branch state file {path} passed basic integrity checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
