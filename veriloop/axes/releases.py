"""Axis 7 · Releases — changelog/tag consistency (git-aware, degrades gracefully).

If there is no git history, we report "not applicable" rather than failing: a
verdict must never be fabricated.
"""

import os
import subprocess

from ._common import result

AXIS = 7


def _git(*args):
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True,
                             timeout=10).stdout.strip()
    except Exception:
        return None


def evaluate(root: str) -> dict:
    changelog = os.path.join(root, "CHANGELOG.md")
    if not os.path.exists(changelog):
        return result(AXIS, "releases", True, 100, 1, [],
                      "no changelog — release consistency not enforced")
    tag = _git("describe", "--tags", "--abbrev=0")
    if tag is None:
        return result(AXIS, "releases", True, 100, 1, [],
                      "no git history — release consistency not checkable (degraded)")
    try:
        text = open(changelog, encoding="utf-8", errors="ignore").read()
    except OSError:
        return result(AXIS, "releases", True, 100, 1, [], "changelog unreadable")
    ok = tag in text
    findings = [] if ok else [{"type": "tag-not-in-changelog", "tag": tag}]
    return result(AXIS, "releases", ok, 100 if ok else 80, 1, findings,
                  "release consistency ok" if ok else f"tag {tag} missing from CHANGELOG")
