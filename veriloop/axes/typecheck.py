"""Axis 8 · Type safety — weak typing escape hatches (any / ts-ignore / casts)."""

import os
import re

from ._common import iter_code, code_only, result

AXIS = 8


def evaluate(root: str) -> dict:
    findings = []
    scanned = 0
    # Match only type-escape usages, NOT the builtin any(...) call.
    pat = re.compile(r":\s*any\b(?!\()| as any\b|<any>|any\[\]|:\s*Any\b(?!\()|@ts-ignore|@ts-nocheck|eslint-disable")
    for path in iter_code(root):
        scanned += 1
        with open(path, encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                if pat.search(code_only(line)):
                    findings.append({"file": os.path.relpath(path, root), "line": i,
                                     "snippet": line.strip()[:100]})
    score = max(0, 100 - len(findings) * 3)
    return result(AXIS, "typecheck", len(findings) == 0, score, scanned, findings,
                  f"{len(findings)} weak-typing site(s)")
