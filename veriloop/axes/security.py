"""Axis 1 · Security — flag code-injection surfaces.

Scans code (after stripping string literals & comments) for dangerous call
patterns. Findings carry file:line so a human can verify each one.
"""

import os
import re

from ._common import iter_code, code_only, result

AXIS = 1
PATTERNS = [
    (r"\beval\s*\(", "high", "eval() runs arbitrary code — injection surface"),
    (r"\bexec\s*\(", "high", "exec() runs arbitrary code — injection surface"),
    (r"child_process", "mid", "spawns subprocess — audit the command source"),
    (r"new\s+Function\s*\(", "high", "Function() constructor == eval-class injection"),
    (r"innerHTML\s*=", "mid", "untrusted innerHTML assignment — XSS surface"),
    (r"sql.*\+.*\+", "mid", "string-concatenated SQL — prefer parameterized queries"),
]


def evaluate(root: str, max_findings: int = 50) -> dict:
    findings = []
    scanned = 0
    for path in iter_code(root):
        scanned += 1
        with open(path, encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                code = code_only(line)
                for pat, sev, why in PATTERNS:
                    if re.search(pat, code):
                        findings.append({
                            "file": os.path.relpath(path, root),
                            "line": i, "sev": sev, "why": why,
                            "snippet": line.strip()[:120],
                        })
                        if len(findings) >= max_findings:
                            break
    score = max(0, 100 - len(findings) * 10)
    return result(AXIS, "security", len(findings) == 0, score, scanned, findings,
                  f"scanned {scanned} files, {len(findings)} hit(s)")
