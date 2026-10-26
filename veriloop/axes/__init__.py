"""Pluggable analyzers ("axes"). Add a new axis by dropping a module here.

Each axis module exposes:

    AXIS = <int>            # stable axis number (1..N, unique)
    def evaluate(root) -> dict:
        return {
            "axis": AXIS,
            "name": "<short name>",
            "passed": bool,
            "score": int,            # 0..100
            "scanned": int,          # files / units inspected
            "findings": [...],       # evidence rows
            "evidence": "<one-line summary>",
        }

Rules every axis must honor:
  * zero dependencies, offline, deterministic
  * never crash the loop (return a red result on error, don't raise)
  * strip string literals / comments before pattern matching (no false positives)
  * never modify the inspected tree
"""
