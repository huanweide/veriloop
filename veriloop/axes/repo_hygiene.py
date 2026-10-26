"""Axis 4 · Repo hygiene — license, readme, committed secrets, oversized files."""

import os
import re

from ._common import iter_code, code_only, result

AXIS = 4
SECRET_PAT = re.compile(
    r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{8,}['\"]")
LARGE = 500_000
SKIP = (".git", "node_modules", "__pycache__", "tests")
SECRET_EXT = (".py", ".js", ".ts", ".env")


def _root_files(root):
    findings = []
    names = os.listdir(root)
    if not any(f.lower().startswith("license") for f in names):
        findings.append({"type": "missing-license", "where": "repo root"})
    if not any(f.lower().startswith("readme") for f in names):
        findings.append({"type": "missing-readme", "where": "repo root"})
    return findings


def _walk_code(root):
    for dp, _, fs in os.walk(root):
        parts = dp.split(os.sep)
        if any(s in parts for s in SKIP):
            continue
        for fn in fs:
            p = os.path.join(dp, fn)
            if fn == ".env" or fn.endswith(SECRET_EXT):
                yield p


def _inspect_file(p, root, findings):
    rel = os.path.relpath(p, root)
    if os.path.basename(p) == ".env":
        findings.append({"type": "committed-env", "where": rel})
    try:
        size = os.path.getsize(p)
    except OSError:
        return
    if size > LARGE:
        findings.append({"type": "large-file", "where": rel, "bytes": size})
    if not p.endswith(SECRET_EXT) or p.endswith(".env"):
        return
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                if SECRET_PAT.search(code_only(line)):
                    findings.append({"type": "hardcoded-secret", "where": rel, "line": i})
    except OSError:
        pass


def evaluate(root: str) -> dict:
    findings = _root_files(root)
    for p in _walk_code(root):
        _inspect_file(p, root, findings)
    scanned = sum(1 for _ in _walk_code(root))
    score = max(0, 100 - len(findings) * 8)
    return result(AXIS, "repo_hygiene", len(findings) == 0, score, scanned, findings,
                  f"{len(findings)} hygiene issue(s)")
