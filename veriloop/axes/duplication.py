"""Axis 3 · Duplication — flag copy-pasted code blocks across a codebase.

Normalizes non-blank line windows, hashes them, and reports hashes that appear
more than once. The ratio drives the score.
"""

import hashlib
import os

from ._common import iter_code, result

AXIS = 3
MIN_LINES = 4
WINDOW = 20
RATIO_THRESH = 0.05


def _blocks(src):
    lines = src.splitlines()
    for i in range(len(lines)):
        for j in range(i + MIN_LINES, min(i + WINDOW, len(lines) + 1)):
            block = lines[i:j]
            if len([l for l in block if l.strip()]) >= MIN_LINES:
                yield hashlib.md5("\n".join(block).strip().encode()).hexdigest(), i + 1


def evaluate(root: str, ratio_thresh: float = RATIO_THRESH, max_findings: int = 50) -> dict:
    seen = {}
    file_count = 0
    for path in iter_code(root):
        file_count += 1
        try:
            src = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        rel = os.path.relpath(path, root)
        for h, ln in _blocks(src):
            seen.setdefault(h, []).append(f"{rel}:{ln}")
    dups = {h: loc for h, loc in seen.items() if len(loc) > 1}
    total = sum(len(v) for v in seen.values())
    dup_blocks = sum(len(v) for v in dups.values())
    ratio = (dup_blocks / total) if total else 0.0
    findings = [{"hash": h[:8], "occ": len(loc), "locations": loc[:10]}
                for h, loc in sorted(dups.items(), key=lambda kv: -len(kv[1]))[:max_findings]]
    score = max(0, 100 - int(ratio * 100 * 2))
    return result(AXIS, "duplication", ratio <= ratio_thresh, score, file_count, findings,
                  f"{file_count} files, dup-ratio={ratio:.2%} (thresh {ratio_thresh:.0%}), {len(dups)} dup block(s)")
