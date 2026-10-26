"""Axis 12 · Robustness — tech-debt markers and broad exception handlers."""

import os
import re

from ._common import iter_code, code_only, result

AXIS = 12


def evaluate(root: str) -> dict:
    findings = []
    scanned = 0
    debt = 0
    debt_pat = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
    broad_pat = re.compile(r"except\s*:|except\s+\w+.*:")
    for path in iter_code(root):
        scanned += 1
        with open(path, encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                c = code_only(line)
                if debt_pat.search(c):
                    debt += 1
                    findings.append({"file": os.path.relpath(path, root), "line": i, "type": "debt-marker"})
                if re.search(r"except\s*:\s*$", c) or re.search(r"except\s+Exception\s*:", c):
                    debt += 1
                    findings.append({"file": os.path.relpath(path, root), "line": i, "type": "broad-except"})
    score = max(0, 100 - debt * 2)
    return result(AXIS, "robustness", debt == 0, score, scanned, findings,
                  f"{debt} debt marker(s)")
