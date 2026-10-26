"""VeriLoop command-line interface.

Usage:
    veriloop scan <path>        one-shot audit report
    veriloop check <path>       run the convergence loop (scan + heal candidates)
    veriloop selftest           prove it catches a fake-green fix
"""

import sys

from .engine import PerceptionLayer, run_loop


def _print_report(rep: dict):
    print("\n=== VeriLoop report ===")
    print(f"verdict : {rep['verdict']}")
    print(f"health  : {rep['health_score']}/100  (round {rep['round']})")
    print(f"strategy: {rep['strategy']}")
    print(f"\n{'AXIS':<14}{'PASS':<6}{'SCORE':<7}EVIDENCE")
    for a in rep["axes"]:
        print(f"{a['name']:<14}{'yes' if a['passed'] else 'NO':<6}{a['score']:<7}{a['evidence'][:60]}")
    if rep["fix_candidates"]:
        print("\nfix candidates (sandbox-verified, NOT auto-applied):")
        for fx in rep["fix_candidates"]:
            print(f"  [{fx['axis']}] {fx.get('file')}:{fx.get('line')} -> verified_green={fx.get('verified_green')}")
    if rep["root_causes"]:
        print("\nroot causes:")
        for c in rep["root_causes"][:10]:
            print("  •", c)


def cmd_scan(args):
    root = args[0] if args else "."
    pl = PerceptionLayer()
    res = pl.sweep(root)
    health = sum(r["score"] for r in res) // len(res) if res else 0
    _print_report({
        "round": 1, "health_score": health, "verdict": "SCAN",
        "strategy": "standard", "axes": res, "root_causes": [], "fix_candidates": [],
    })


def cmd_check(args):
    root = args[0] if args else "."
    _print_report(run_loop(root, max_rounds=6))


def cmd_selftest(args):
    from .selftest import run_selftest
    ok = run_selftest()
    sys.exit(0 if ok else 1)


_DISPATCH = {"scan": cmd_scan, "check": cmd_check, "selftest": cmd_selftest}


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] not in _DISPATCH:
        print("usage: veriloop [scan|check|selftest] <path>")
        print("  scan     one-shot audit report")
        print("  check    run the convergence loop (scan + heal candidates)")
        print("  selftest prove it catches a fake-green fix")
        sys.exit(1)
    _DISPATCH[argv[0]](argv[1:])


if __name__ == "__main__":
    main()
