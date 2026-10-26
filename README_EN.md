<p align="center">
  <img src="assets/banner_en.svg" alt="VeriLoop">
</p>

# VeriLoop 🔁

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![CI](https://github.com/huanweide/veriloop/actions/workflows/ci.yml/badge.svg)
![Stars](https://img.shields.io/github/stars/huanweide/veriloop?style=social)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

> **The self-iterating code auditor that *proves its own fixes*.**
> AI code audit engine — whether it's fixed is decided by tests, not by the model.

Natural language / AI iteration → automated "Scan → Flag → Propose Fix → Sandbox-Verify → Converge". Zero dependencies, offline, deterministic.

[30-Second Tour](#30-second-tour) · [Features](#features) · [Quick Start](#quick-start) · [Architecture](#architecture) · [Contributing](#contributing)

---

## 30-Second Tour

```
User:     fix the injection flaw in this code
Naive loop: ✅ fixed (switched to parameterized query)   ← the model says so itself
VeriLoop:  re-run verification gate → re-scan security axis → username field still injectable
           discriminating test: must be RED before fix + GREEN after fix → old "fix" fails the gate
           → never reports "fixed" until a real check turns green
```

One sentence difference: **the criterion for "fixed" comes from outside the model, not from the model itself.**

## What It Does

Give it a project path and watch it run a full audit loop:

```
$ veriloop check ./your-project

Round 1: Scan   → 12 analyzers run in parallel, each flags RED/GREEN + score + evidence(file:line)
Round 2: Judge  → four brakes pass in turn: root-cause / discriminating / verification / escape
Round 3: Fix    → Healer tries the fix in a sandbox copy, re-runs the check, proves it green
Round 4: Converge → either a "sandbox-verified fix candidate" or a "needs-human" stall report
```

Built for AI self-iteration quality assurance, pre-CI autonomous-repair pre-checks, and any scenario where you refuse to trust a model's self-reported green.

## Features

- **Verification Gate (Evidence-Anchored)** — a claim of "fixed" is accepted only if an independent check matches verbatim in real code output; no model self-reported green.
- **Sandbox-Verified Healer** — tries the fix in a temp copy, re-runs the check, proves it green, then delivers the candidate; **never touches your code**, landing is up to you or an upper agent.
- **Four Verification Brakes (generic pattern)** — root-cause gate / discriminating test / verification gate + evidence anchor / escape ladder + stall guard; any "all-green" round must pass the discriminating test or it keeps fixing.
- **12 Pluggable Analyzers** — security / complexity / duplication / repo-hygiene / docs / dependencies / releases / typecheck / accessibility / devdeps / maturity / robustness; zero-dep, offline, deterministic, out-of-the-box.
- **Dogfood Contract** — the engine self-scans its own source ALL GREEN (health 92/100); no double standard; adding an analyzer = drop one file into `veriloop/axes/`.
- **Honest Degradation** — repos without git history report the release-consistency axis as "n/a", never faking a pass.

## Quick Start

### Installation

```bash
# PyPI (recommended)
pip install veriloop

# or run from source (zero deps, Python 3.8+)
git clone https://github.com/huanweide/veriloop.git
cd veriloop && PYTHONPATH=. python -m veriloop --help
```

### One-shot audit

```bash
veriloop scan ./your-project
```

### Run the convergence loop (generate sandbox-verified fix candidates)

```bash
veriloop check ./your-project
```

### Prove it catches fake-green

```bash
veriloop selftest
```

Sample output (running `check` on a dirty project containing `eval`):

```
=== VeriLoop report ===
verdict : CONVERGED: 1 axis(s) proven fixable in sandbox (NOT auto-applied)
health  : 89/100  (round 1)
strategy: standard

AXIS           PASS SCORE EVIDENCE
security       NO   88    scanned 2 files, 1 hit(s)
complexity     yes  100   scanned 2 files, 0 func(s) over CC 12
duplication    yes  100   2 files, dup-ratio=0.00% (thresh 5%), 0 dup block(s)
...

fix candidates (sandbox-verified, NOT auto-applied):
  [security] src/dirty.py:2 -> verified_green=True
```

> ⚠️ **VeriLoop only delivers "sandbox-verified fix candidates" and never modifies your code on its own.** That is the safety boundary.

## CLI Command Reference

| Command | Purpose |
|---|---|
| `veriloop scan <path>` | one-shot run of all 12 axes, prints each axis PASS / SCORE / EVIDENCE |
| `veriloop check <path>` | convergence loop: audit + Healer-generated sandbox-verified fix candidates |
| `veriloop selftest` | prove it catches fake-green (built-in contrast samples) |

## Architecture

VeriLoop defaults to a **verification-driven convergence loop** (not a fixed-round spin): every "all-green" round must pass the discriminating test, otherwise it keeps fixing; sustained stall triggers a brake and stops.

### Primitive table

| Concept | Meaning |
|---|---|
| **Axis report** | each axis returns `{passed? score evidence(file:line)}`; the repo average is `health` |
| **Verification Gate** | "fixed" accepted ⟺ an independent check matches verbatim in real code output |
| **Discriminating Test** | RED before fix + GREEN after fix, the two-state contrast locks the evidence |
| **Healer Sandbox** | temp copy → try fix → re-run check → prove green → deliver candidate (no source edit) |
| **Escape Ladder / Stall Guard** | stuck → force a different tactic; N consecutive no-progress rounds → stop and report to human |

### Convergence loop

```
Scan(12 axes) → any RED? ──no──> discriminating test passed? ──yes──> deliver(ALL GREEN)
                   │                           │
                  yes                         no
                   ▼                           ▼
          Four brakes(root-cause/discrim/verify/escape)   keep fixing (no spin)
                   │
          verifiable RED axis?
                   ├─ yes → Healer sandbox verify → prove green → deliver candidate
                   └─ no  → escape ladder / stall guard → stop & report to human
```

### Core modules

| Module | File | Description |
|---|---|---|
| Perception Layer | `veriloop/engine.py` · `PerceptionLayer` | loads & schedules the 12 analyzers, emits evidence-anchored axis reports |
| Brake Core | `veriloop/engine.py` · `BrakeCore` | four brakes: root-cause gate / discriminating test / verification gate / escape ladder |
| Convergence Protocol | `veriloop/engine.py` · `ConvergenceProtocol` | escape ladder + stall guard |
| Fix Candidate | `veriloop/healer.py` | sandbox-verified repair, never mutates user code |
| Analyzers | `veriloop/axes/*.py` | 12 zero-dep, offline, deterministic checkers, pluggable |
| CLI | `veriloop/cli.py` | `scan` / `check` / `selftest` entry points |

No code-reading required: see [ARCHITECTURE.md](./ARCHITECTURE.md) (analogies + glossary).

## Add your own analyzer

```python
# veriloop/axes/myrule.py
from ._common import result

AXIS = 13

def evaluate(root):
    findings = []
    scanned = 0
    # ... your zero-dep, offline check logic ...
    passed = len(findings) == 0
    score = 100 if passed else 60
    return result(AXIS, "myrule", passed, score, scanned, findings, "1 finding")
```

Drop it in and `veriloop scan` picks it up automatically.

## Roadmap

- [x] 12 built-in analyzers + sandbox Healer
- [x] `veriloop selftest` proves it catches fake-green
- [ ] more domain axis templates (security-compliance / performance / i18n)
- [ ] render fix candidates as a reviewable diff (still human-confirmed)
- [ ] more agent integration examples

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Analyzer and brake-strategy PRs welcome.

## Security Boundary

VeriLoop only reads and analyzes your code, and only delivers "sandbox-verified fix candidates". **It will not, and must never, modify your source files.** Any auto-landing of fixes must be explicitly authorized by you or an upper agent.

## License

[MIT](./LICENSE) © The VeriLoop Authors

## ⭐ Star VeriLoop

If this project saved you from one fake-green, drop a Star so more people find it — Issues and PRs are welcome.

> 🔁 **VeriLoop** — let the tests decide what's fixed.
