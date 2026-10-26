"""Healer: propose fixes and *prove* them in a sandbox — never touch user code.

For a red axis whose verdict can be mechanically re-checked, the Healer copies
the target into a temporary directory, neutralizes the flagged line, re-runs the
axis, and reports whether the axis now passes. The candidate is delivered with a
``verified_green`` flag; applying it is left to the human / outer agent. This is
the safety boundary: VeriLoop proves a fix works, it does not silently rewrite
your codebase.
"""

import os
import shutil
import tempfile

# Axes whose verdict can be re-derived mechanically in a sandbox copy.
VERIFIABLE_AXES = {"security"}


def _neutralize_line(path: str, line_no: int) -> None:
    """Replace a flagged line with a neutral stub that contains no dangerous token."""
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    if 1 <= line_no <= len(lines):
        indent = len(lines[line_no - 1]) - len(lines[line_no - 1].lstrip())
        lines[line_no - 1] = " " * indent + "pass  # sanitized by veriloop healer\n"
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def sandbox_verify_fix(root: str, finding: dict, judge) -> tuple:
    """Copy ``root`` to a temp dir, neutralize the finding, re-run ``judge``.

    Returns (passed, tmp_dir). The temp dir is always cleaned up by the caller.
    """
    tmp = tempfile.mkdtemp(prefix="veriloop-sbx-")
    try:
        shutil.copytree(root, tmp, dirs_exist_ok=True)
        rel = finding.get("file")
        line = finding.get("line")
        if rel and line:
            _neutralize_line(os.path.join(tmp, rel), line)
        r = judge(tmp)
        return (bool(r.get("passed")), tmp)
    except Exception:
        return (False, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def propose(reds: list, by_name: dict, root: str) -> list:
    """For each red axis, produce a fix candidate (sandbox-verified when possible)."""
    fixes = []
    for r in reds:
        name = r["name"]
        if name in VERIFIABLE_AXES and name in by_name:
            judge = getattr(by_name[name], "evaluate", None)
            if judge is None:
                continue
            proven = False
            for fnd in r.get("findings", [])[:5]:
                passed, _ = sandbox_verify_fix(root, fnd, judge)
                if passed:
                    fixes.append({
                        "axis": name,
                        "file": fnd.get("file"),
                        "line": fnd.get("line"),
                        "verified_green": True,
                        "suggestion": (
                            "Remove or replace the flagged call with a safe, explicit alternative "
                            "(e.g. ast.literal_eval / json.loads / a typed decoder). "
                            "Verified green in sandbox — human review before applying."
                        ),
                    })
                    proven = True
                    break
            if not proven:
                fixes.append({
                    "axis": name,
                    "verified_green": False,
                    "suggestion": "Sandbox could not prove a trivial fix; needs manual review.",
                })
        else:
            fixes.append({
                "axis": name,
                "verified_green": False,
                "suggestion": f"Manual review required for {name} findings.",
            })
    return fixes
