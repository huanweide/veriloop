**中文** · [README.md](./README.md)

<p align="center">
  <img src="assets/banner.svg" alt="VeriLoop">
</p>

# VeriLoop 🔁

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![CI](https://github.com/huanweide/veriloop/actions/workflows/ci.yml/badge.svg)
![Stars](https://img.shields.io/github/stars/huanweide/veriloop?style=social)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

> **AI code audit engine — whether it's fixed, the test decides.**
> *The self-iterating code auditor that proves its own fixes.*

Natural-language / AI iteration → automatically completes the full flow "scan → flag red → propose fix → sandbox-verify → converge". Zero dependencies, offline, deterministic.

[Overview](#overview) · [Features](#features) · [Quick start](#quick-start) · [Architecture](#architecture) · [Contributing](#contributing)

---

## Overview

```
User: fix the injection risk in this code
Normal loop: ✅ fixed (switched to parameterized)   ← model says "fixed"
VeriLoop:   verification gate re-check → re-run security axis → username field still injectable
           discriminating test: must-RED-before + must-GREEN-after → old "fix" failed the gate
           → doesn't say "fixed", keeps fixing until it truly passes the test before delivering
```

One sentence: **the criterion for "fixed" comes from outside the model, not from the model itself.**

---

## Who should use it

- You run AI self-iteration and want a code-quality gate that **proves its own fixes** rather than trusting a self-reported green.
- You want an **autonomous pre-check before CI** that proposes sandbox-verified fix candidates.
- You want **12 pluggable analysis axes** you can extend with one file.

## Who should NOT use it

- You expect it to **auto-apply fixes to your code** — it only delivers sandbox-verified candidates; landing them is up to you.
- You want a single quick lint — this runs a convergence loop (more thorough, slower).
- You need a GUI; this is a CLI.

---

## Features

- **Verification gate (evidence anchor)** — a "fixed" claim is only accepted if an independent check appears char-by-char in the real code output, killing the model's self-reported fake-green.
- **Sandbox-verified Healer** — tries the fix in a temp copy, re-runs the verification, proves it turned green, then delivers the candidate; **never touches your code**, landing decided by you or your upper agent.
- **Four brakes (shared paradigm)** — root-cause gate / discriminating test / verification gate + evidence anchor / escape ladder + anti-spin; any round that goes "all green" must pass the discriminating test or it keeps fixing.
- **12 pluggable analysis axes** — security / complexity / duplication / repo hygiene / docs / dependencies / release / types / accessibility / dependency-class / maturity / robustness; zero-dep, offline, deterministic, ready out of the box.
- **Docs-as-contract (dogfood)** — the engine self-checks its own source as ALL GREEN (health 92/100), never a double standard; adding a checker = drop one file into `veriloop/axes/`.
- **Honest degradation** — a repo with no git history reports the release-consistency axis truthfully as "not applicable", never faking a pass.

---

## Quick start

### Install

```bash
# PyPI (recommended)
pip install veriloop

# or run from source (zero-dep, Python 3.8+)
git clone https://github.com/huanweide/veriloop.git
cd veriloop && PYTHONPATH=. python -m veriloop --help
```

### One-shot audit

```bash
veriloop scan ./your-project
```

### Run the convergence loop (produces sandbox-verified fix candidates)

```bash
veriloop check ./your-project
```

### Prove it blocks "fake fixes"

```bash
veriloop selftest
```

Sample output (running `check` on a dirty project with `eval`):

```text
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

> ⚠️ **VeriLoop only delivers "sandbox-verified fix candidates" and never edits your code on its own.** That is the safety boundary.

---

## CLI reference

| Command | Purpose |
|---|---|
| `veriloop scan <path>` | One-shot run of 12 axes, outputs each axis pass / score / evidence |
| `veriloop check <path>` | Run the convergence loop: audit + Healer produces sandbox-verified fix candidates |
| `veriloop selftest` | Prove it blocks "fake fixes" (built-in controlled sample) |

---

## Architecture

VeriLoop uses a **verification-driven convergence loop** by default (not a fixed-round empty spin): every round that goes "all green" must pass the discriminating test, or it keeps fixing; consecutive empty spinning triggers the brake to stop.

### Primitives

| Concept | Meaning |
|---|---|
| **Analysis-axis report** | Each axis returns `{pass? score evidence(file:line)}`; the whole repo averages to health |
| **Verification gate** | "Fix holds" ⟺ an independent check hits char-by-char in the real code output |
| **Discriminating test** | must-RED-before + must-GREEN-after, binary contrast locks the evidence |
| **Healer sandbox** | temp copy tries fix → re-run criterion → prove green → deliver candidate (don't touch source) |
| **Escape ladder / anti-spin** | force a new tactic when stuck; stop and report to human after N rounds with no progress |

### Convergence loop

```text
scan(12 axes) → flag red? ──no──> discriminating test passed? ──yes──> deliver(ALL GREEN)
                │                        │
               yes                      no
                ▼                        ▼
         four brakes(root/disc/verify/escape)   keep fixing (no empty spin)
                │
           verifiable red axis?
                ├─ yes → Healer sandbox verify → prove green → deliver candidate
                └─ no → escape ladder / anti-spin → stop and report to human
```

### Core modules

| Module | File | Description |
|---|---|---|
| Perception layer | `veriloop/engine.py` · `PerceptionLayer` | Loads and schedules the 12 analysis axes, produces evidence-anchored axis reports |
| Brake core | `veriloop/engine.py` · `BrakeCore` | Four brakes: root-cause / discriminating / verification / escape |
| Convergence protocol | `veriloop/engine.py` · `ConvergenceProtocol` | Escape ladder + anti-spin |
| Fix candidate | `veriloop/healer.py` | Sandbox-copy verified fix, never touches user code |
| Analysis axes | `veriloop/axes/*.py` | 12 zero-dep, offline, deterministic checkers, pluggable |
| CLI | `veriloop/cli.py` | `scan` / `check` / `selftest` entry points |

For a no-code explanation: see [ARCHITECTURE.md](./ARCHITECTURE.md) (life analogies + glossary).

---

## Add your own analysis axis

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

Drop it in and it takes effect — `veriloop scan` will pick it up automatically.

---

## Roadmap

- [x] 12 built-in analysis axes + sandbox Healer
- [x] `veriloop selftest` proves it blocks fake-green
- [ ] More domain axis templates (security-compliance / performance / i18n)
- [ ] Feed fix candidates back as reviewable diffs (still human-confirmed)
- [ ] More agent integration examples

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Axes and brake strategies are welcome.

## Safety boundary

VeriLoop only reads and analyzes your code, and only delivers "sandbox-verified fix candidates". **It will not, and never does, modify your source files.** Any auto-landing of fixes should be done by you or your upper agent under explicit authorization.

## License

[MIT](./LICENSE) © The VeriLoop Authors

## ⭐ Star VeriLoop

If this project blocked one "fake-green" for you, drop a Star so more people see it — issues and PRs welcome.

> 🔁 **VeriLoop** — whether it's fixed, let the test decide.
