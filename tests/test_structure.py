from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import unittest


class ProjectResolverStructureTest(unittest.TestCase):
    def test_structural_validator_passes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, str(root / "tools/validate_structure.py")],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
