"""Shared helpers for axes: file walking, literal/comment stripping, scoring."""

import ast
import os

# Directories we never descend into (offline, no surprise).
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".next", "out", "target", ".idea", ".vscode", ".tailwind", "coverage",
    ".pytest_cache", ".mypy_cache", ".tox", "site-packages", "tests",
}
CODE_EXT = (".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs")


def iter_code(root):
    for dp, _, fs in os.walk(root):
        parts = dp.split(os.sep)
        if any(s in parts for s in SKIP_DIRS):
            continue
        for fn in fs:
            if fn.endswith(CODE_EXT):
                yield os.path.join(dp, fn)


def code_only(line: str) -> str:
    """Drop comments and string literals so scanners don't false-positive on them.

    Handles single and triple-quoted strings. So a docstring that mentions a
    dangerous call is treated as data, not as executable code — otherwise the
    dangerous token would leak into the scanned code and raise a false hit.
    """
    out = []
    i = 0
    n = len(line)
    in_str = None
    while i < n:
        c = line[i]
        if in_str:
            if c == in_str:
                # triple-quote close: look ahead for two more identical quotes
                if i + 2 < n and line[i:i + 3] == in_str * 3:
                    i += 3
                    in_str = None
                    continue
                in_str = None
            i += 1
            continue
        if c == "#":
            break
        if c in "\"'":
            if i + 2 < n and line[i:i + 3] == c * 3:  # triple-quote open
                in_str = c
                i += 3
                continue
            in_str = c
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def result(axis, name, passed, score, scanned, findings, evidence):
    return {
        "axis": axis,
        "name": name,
        "passed": bool(passed),
        "score": int(max(0, min(100, score))),
        "scanned": int(scanned),
        "findings": findings[:50],
        "evidence": evidence,
    }


def cyclomatic(node) -> int:
    """Rough cyclomatic complexity of a function/async-function node."""
    c = 1
    for ch in ast.walk(node):
        if isinstance(ch, (ast.If, ast.For, ast.AsyncFor, ast.While,
                           ast.With, ast.AsyncWith, ast.Try, ast.ExceptHandler,
                           ast.BoolOp, ast.IfExp, ast.comprehension)):
            if isinstance(ch, ast.BoolOp):
                c += len(ch.values) - 1
            elif isinstance(ch, ast.comprehension):
                c += 1 + len(ch.ifs)
            else:
                c += 1
    return c
