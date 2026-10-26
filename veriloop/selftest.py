"""Built-in self-test: proves VeriLoop catches a fake-green fix.

Uses only throwaway temp projects, never your code.
"""

import os
import shutil
import tempfile

from .engine import PerceptionLayer, run_loop


def _make_project(dirty=True):
    d = tempfile.mkdtemp(prefix="veriloop-test-")
    open(os.path.join(d, "LICENSE"), "w").write("MIT")
    open(os.path.join(d, "README.md"), "w").write("# demo\n")
    os.makedirs(os.path.join(d, "src"), exist_ok=True)
    if dirty:
        open(os.path.join(d, "src", "dirty.py"), "w").write(
            "def f():\n    return eval('1+1')\n")
    open(os.path.join(d, "src", "clean.py"), "w").write(
        "def g():\n    return 1 + 1\n")
    if not dirty:
        # A genuinely complete project also satisfies the maturity axis.
        os.makedirs(os.path.join(d, "tests"), exist_ok=True)
        open(os.path.join(d, "tests", "test_smoke.py"), "w").write(
            "def test_ok():\n    assert 1 + 1 == 2\n")
        os.makedirs(os.path.join(d, ".github", "workflows"), exist_ok=True)
        open(os.path.join(d, ".github", "workflows", "ci.yml"), "w").write(
            "name: ci\non: [push]\njobs:\n  t:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo ok\n")
        open(os.path.join(d, "CONTRIBUTING.md"), "w").write("# Contributing\n")
        open(os.path.join(d, "CHANGELOG.md"), "w").write("# Changelog\n")
    return d


def run_selftest():
    # 1) axis numbers are unique 1..N
    pl = PerceptionLayer()
    nums = [m.evaluate(".")["axis"] for m in pl.axes]
    assert len(nums) == len(set(nums)), f"duplicate axis numbers: {nums}"
    assert sorted(nums) == list(range(1, len(nums) + 1)), f"axis numbers not 1..N: {nums}"
    print(f"[ok] {len(nums)} axes loaded, numbers unique 1..{len(nums)}")

    # 2) dirty project converges on round 1 with a sandbox-verified fix
    d = _make_project(dirty=True)
    try:
        rep = run_loop(d, max_rounds=4)
        assert rep["verdict"].startswith("CONVERGED"), f"expected CONVERGED, got {rep['verdict']}"
        sec = next(a for a in rep["axes"] if a["name"] == "security")
        assert sec["passed"] is False, "security should be red in dirty project"
        verified = [f for f in rep["fix_candidates"] if f.get("verified_green")]
        assert verified, "expected at least one sandbox-verified fix candidate"
        assert verified[0]["axis"] == "security"
        print(f"[ok] dirty project -> {rep['verdict']} (security fix verified in sandbox)")
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # 3) clean project is ALL GREEN
    d2 = _make_project(dirty=False)
    try:
        rep = run_loop(d2, max_rounds=2)
        assert rep["verdict"] == "ALL GREEN — converged", f"clean should be ALL GREEN, got {rep['verdict']}"
        print(f"[ok] clean project -> ALL GREEN (health {rep['health_score']})")
    finally:
        shutil.rmtree(d2, ignore_errors=True)

    print("\nALL TESTS PASSED")
    return True
