"""Axis 11 · Process maturity — does the repo look maintained?

Checks for the presence of tests, CI, contribution guide, license, changelog.
A low score is a signal, not a failure of the code itself.
"""

import os

from ._common import result

AXIS = 11


def evaluate(root: str) -> dict:
    checks = {
        "tests": (os.path.isdir(os.path.join(root, "tests")) or
                  os.path.isdir(os.path.join(root, "test"))),
        "ci": os.path.isdir(os.path.join(root, ".github", "workflows")),
        "contributing": os.path.exists(os.path.join(root, "CONTRIBUTING.md")),
        "license": any(f.lower().startswith("license") for f in os.listdir(root)),
        "changelog": os.path.exists(os.path.join(root, "CHANGELOG.md")),
    }
    missing = [k for k, v in checks.items() if not v]
    score = int(100 * (len(checks) - len(missing)) / len(checks))
    return result(AXIS, "maturity", len(missing) == 0, score, len(checks),
                  [{"missing": m} for m in missing],
                  f"maturity {score}% ({len(missing)} gap(s))")
