"""Axis 5 · Docs — images without alt text in markdown/html."""

import os
import re

from ._common import result

AXIS = 5


def evaluate(root: str) -> dict:
    findings = []
    scanned = 0
    for dp, _, fs in os.walk(root):
        if any(s in dp.split(os.sep) for s in (".git", "node_modules", "tests")):
            continue
        for fn in fs:
            if not fn.endswith((".md", ".mdx", ".html")):
                continue
            scanned += 1
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, root)
            try:
                lines = open(p, encoding="utf-8", errors="ignore").readlines()
            except OSError:
                continue
            for i, line in enumerate(lines, 1):
                if re.search(r"!\[]\((?!.*alt=).*\)", line):
                    findings.append({"type": "img-no-alt", "where": rel, "line": i})
    score = max(0, 100 - len(findings) * 5)
    return result(AXIS, "docs", len(findings) == 0, score, scanned, findings,
                  f"{len(findings)} doc issue(s)")
