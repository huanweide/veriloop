"""Axis 9 · Accessibility — images without alt, heading jumps, deprecated tags."""

import os
import re

from ._common import result

AXIS = 9
SKIP = (".git", "node_modules", "tests")
EXT = (".md", ".html", ".jsx", ".tsx")
IMG_RE = re.compile(r"<img\b[^>]*\bsrc=", re.I)
ALT_RE = re.compile(r"alt=", re.I)
DEPRECATED_RE = re.compile(r"<(font|center|marquee|blink)\b", re.I)
HEAD_RE = re.compile(r"^(#{1,6})\s", re.M)


def _check_lines(text, rel, findings):
    for i, line in enumerate(text.splitlines(), 1):
        if IMG_RE.search(line) and not ALT_RE.search(line):
            findings.append({"type": "img-no-alt", "where": rel, "line": i})
        if DEPRECATED_RE.search(line):
            findings.append({"type": "deprecated-tag", "where": rel, "line": i})


def _check_headings(text, rel, findings):
    heads = [len(m) for m in HEAD_RE.findall(text)]
    for a, b in zip(heads, heads[1:]):
        if b - a > 1:
            findings.append({"type": "heading-jump", "where": rel})
            return


def evaluate(root: str) -> dict:
    findings = []
    scanned = 0
    for dp, _, fs in os.walk(root):
        if any(s in dp.split(os.sep) for s in SKIP):
            continue
        for fn in fs:
            if not fn.endswith(EXT):
                continue
            scanned += 1
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, root)
            try:
                text = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            _check_lines(text, rel, findings)
            _check_headings(text, rel, findings)
    score = max(0, 100 - len(findings) * 5)
    return result(AXIS, "accessibility", len(findings) == 0, score, scanned, findings,
                  f"{len(findings)} a11y issue(s)")
