"""Axis 2 · Complexity — flag functions whose cyclomatic complexity is too high.

High complexity correlates with bugs and hard reviews. We count decision points
via the AST and report functions above a threshold.
"""

import ast
import os

from ._common import iter_code, cyclomatic, result

AXIS = 2
THRESH = 12


def evaluate(root: str) -> dict:
    offenders = []
    scanned = 0
    for path in iter_code(root):
        try:
            src = open(path, encoding="utf-8").read()
        except OSError:
            continue
        scanned += 1
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and cyclomatic(node) > THRESH:
                offenders.append({
                    "file": os.path.relpath(path, root),
                    "line": node.lineno, "func": node.name, "cc": cyclomatic(node),
                })
    score = max(0, 100 - len(offenders) * 5)
    return result(AXIS, "complexity", len(offenders) == 0, score, scanned, offenders,
                  f"scanned {scanned} files, {len(offenders)} func(s) over CC {THRESH}")
