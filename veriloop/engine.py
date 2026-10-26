"""VeriLoop core engine.

A self-iterating code auditor that proves its own fixes.

The engine runs a *perception layer* (pluggable analyzers called "axes") over a
codebase, then applies four verification brakes before it is allowed to declare
any problem "solved". The brakes are the whole point: the verdict that a problem
is fixed must come from **outside** the model that produced the fix, never from
the model's own word.

Brakes
------
1. Root-Cause Gate   — only act on a real, named root cause.
2. Discriminating Test — a fix is real only if "before" was red and "after" is green.
3. Verification Gate (+ Evidence Anchor) — re-run the real check; keep the proof.
4. Escape Ladder + Stall Guard — when stuck, force a strategy change; never spin.
"""

import importlib
import os
import pkgutil

from . import healer


class PerceptionLayer:
    """Loads every analyzer ("axis") from a package and sweeps a codebase.

    Each axis module exposes ``evaluate(root) -> dict`` with the keys
    ``axis, name, passed, score, scanned, findings, evidence``.
    """

    def __init__(self, axis_pkg: str = "veriloop.axes"):
        self.axes = []
        self.by_name = {}  # short module name -> module (for targeted sandbox re-runs)
        pkg = importlib.import_module(axis_pkg)
        for mod in pkgutil.iter_modules(pkg.__path__):
            if mod.name.startswith("_"):
                continue
            m = importlib.import_module(f"{axis_pkg}.{mod.name}")
            if hasattr(m, "evaluate"):
                self.axes.append(m)
                self.by_name[mod.name] = m

    def sweep(self, root: str) -> list:
        results = []
        for mod in self.axes:
            try:
                r = mod.evaluate(root)
            except Exception as e:  # an axis must never crash the loop
                r = {
                    "axis": getattr(mod, "AXIS", 0),
                    "name": mod.__name__.split(".")[-1],
                    "passed": False,
                    "score": 0,
                    "scanned": 0,
                    "findings": [],
                    "evidence": f"axis crashed: {e}",
                }
            if isinstance(r, dict) and "name" in r:
                results.append(r)
        return results


class BrakeCore:
    """The four verification brakes, shared by every iteration."""

    ESCAPE_AFTER = 3
    STALL_PATIENCE = 2

    @staticmethod
    def oracle_gate(results):
        """Verification Gate: a round passes only if NO axis is red."""
        reds = [r for r in results if not r.get("passed")]
        return (len(reds) == 0, reds)

    @staticmethod
    def root_cause_gate(reds):
        """Root-Cause Gate: turn each red axis into a named, evidence-backed cause."""
        causes = []
        for r in reds:
            causes.append(f"[{r['name']}] axis {r.get('axis')} — {r.get('evidence', '')}")
        return causes


class ConvergenceProtocol:
    """Drives escape ladder + stall guard so the loop never spins forever."""

    def __init__(self):
        self.stall_count = 0

    def escape_ladder(self, rnd: int) -> str:
        if rnd >= BrakeCore.ESCAPE_AFTER:
            return "escalate: change strategy (swap approach / swap target / concede)"
        return "standard"

    def stall_guard(self, health: int) -> bool:
        if health >= 90:
            self.stall_count = 0
            return False
        self.stall_count += 1
        return self.stall_count >= BrakeCore.STALL_PATIENCE


def _deliver(rnd, health, results, verdict, strategy, causes=None, fixes=None):
    return {
        "round": rnd,
        "health_score": health,
        "verdict": verdict,
        "strategy": strategy,
        "axes": results,
        "root_causes": causes or [],
        "fix_candidates": fixes or [],
    }


def run_loop(root: str, max_rounds: int = 6) -> dict:
    """Run the convergence loop over ``root`` and return an evidence report.

    The loop never mutates the user's code. When a red axis is verifiable, the
    Healer proposes a fix, proves it green inside a throwaway sandbox copy, and
    delivers the candidate — the human (or an outer agent) decides whether to
    apply it.
    """
    percept = PerceptionLayer()
    brake = BrakeCore()
    conv = ConvergenceProtocol()
    prev = None
    results = []
    causes = []
    fixes = []
    for rnd in range(1, max_rounds + 1):
        results = percept.sweep(root)
        health = sum(r["score"] for r in results) // len(results) if results else 0
        passed, reds = brake.oracle_gate(results)
        strategy = conv.escape_ladder(rnd)
        if passed:
            return _deliver(rnd, health, results, "ALL GREEN — converged", strategy)
        causes = brake.root_cause_gate(reds)
        # Healer: propose + sandbox-verify fixes; converge on a *verified* fix,
        # never on a silent mutation.
        fixes = healer.propose(reds, percept.by_name, root)
        verified = [f for f in fixes if f.get("verified_green")]
        if verified:
            return _deliver(
                rnd,
                health,
                results,
                f"CONVERGED: {len(verified)} axis(s) proven fixable in sandbox (NOT auto-applied)",
                strategy,
                causes,
                fixes,
            )
        stalled = conv.stall_guard(health)
        if stalled:
            return _deliver(
                rnd, health, results, "STALL GUARD — stop self-spin, report to human",
                strategy, causes, fixes,
            )
        prev = results
    return _deliver(
        max_rounds, health, results, "MAX ROUNDS — deliver evidence report",
        strategy, causes, fixes,
    )
