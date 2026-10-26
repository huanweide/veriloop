"""Axis 10 · Dev/dep separation — build/test tools misplaced in runtime deps."""

import json
import os

from ._common import result

AXIS = 10
DEV_HINTS = ("typescript", "jest", "eslint", "prettier", "@types/", "vitest",
             "mocha", "rollup", "webpack", "vite")


def evaluate(root: str) -> dict:
    findings = []
    scanned = 0
    pj = os.path.join(root, "package.json")
    if os.path.exists(pj):
        scanned += 1
        try:
            data = json.load(open(pj, encoding="utf-8"))
        except (OSError, ValueError):
            return result(AXIS, "devdeps", True, 100, 1, [], "package.json unreadable")
        for name in data.get("dependencies", {}):
            if any(h in name for h in DEV_HINTS):
                findings.append({"type": "misplaced-dev-dep", "name": name})
    score = max(0, 100 - len(findings) * 10)
    return result(AXIS, "devdeps", len(findings) == 0, score, scanned, findings,
                  f"{len(findings)} misplaced dep(s)")
