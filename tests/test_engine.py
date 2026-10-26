"""VeriLoop regression gate.

Run with:  python tests/test_engine.py
Or:        veriloop selftest   (delegates to veriloop.selftest.run_selftest)
"""

from veriloop.selftest import run_selftest

if __name__ == "__main__":
    raise SystemExit(0 if run_selftest() else 1)
