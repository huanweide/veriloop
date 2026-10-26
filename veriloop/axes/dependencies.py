"""Axis 6 · Dependencies — floating versions and missing lockfile."""

import json
import os

from ._common import result

AXIS = 6


def evaluate(root: str) -> dict:
    findings = []
    scanned = 0
    pj = os.path.join(root, "package.json")
    if os.path.exists(pj):
        scanned += 1
        try:
            data = json.load(open(pj, encoding="utf-8"))
        except (OSError, ValueError):
            return result(AXIS, "dependencies", False, 0, 1, [{"type": "invalid-json"}],
                          "package.json not parseable")
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        for name, ver in deps.items():
            if ver in ("*", "latest") or ver.startswith("git") or "://" in str(ver):
                findings.append({"type": "floating-dep", "name": name, "version": ver})
        if not any(os.path.exists(os.path.join(root, f)) for f in
                   ("package-lock.json", "pnpm-lock.yaml", "yarn.lock")):
            findings.append({"type": "no-lockfile"})
    score = max(0, 100 - len(findings) * 10)
    return result(AXIS, "dependencies", len(findings) == 0, score, scanned, findings,
                  f"{len(findings)} dependency issue(s)")
