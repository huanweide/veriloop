<p align="center">
  <img src="assets/banner.svg" alt="VeriLoop">
</p>

# VeriLoop 🔁

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![CI](https://github.com/huanweide/veriloop/actions/workflows/ci.yml/badge.svg)
![Stars](https://img.shields.io/github/stars/huanweide/veriloop?style=social)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

> **AI 代码审计引擎 — 修没修好，测试说了算。**
> *The self-iterating code auditor that proves its own fixes.*

自然语言 / AI 迭代 → 自动完成「扫描 → 判红 → 提修复 → 沙箱验证 → 收敛」全流程。零依赖、离线、确定性。

[30 秒看懂](#30-秒看懂) · [特性](#特性) · [快速开始](#快速开始) · [架构](#架构) · [贡献](#贡献)

---

## 30 秒看懂

```
用户：把这段代码的注入隐患修一下
普通循环：✅ 已修复（改成参数化）        ← 模型自己说"修好了"
VeriLoop：验证闸门复检 → 重跑安全轴 → 发现 username 字段仍可注入
         判别测试：修复前必红 + 修复后必绿 → 旧"修复"没过门禁
         → 不出"已修复"，继续修到真过测试才交付
```

差别只有一句话：**「修好了」的判据来自模型之外，不来自模型自己。**

## 它能做什么

给它一个项目路径，看它跑一整轮审计：

```
$ veriloop check ./your-project

Round 1: 扫描 → 12 个分析轴并行体检，标记红/绿 + 分数 + 证据(file:line)
Round 2: 判红 → 四道刹车逐条过：根因 / 判别测试 / 验证 / 逃逸
Round 3: 提修复 → Healer 在沙箱副本里试修、重跑验证、证明变绿
Round 4: 收敛 → 要么拿到"经沙箱验证的修复候选"，要么报"需人工"停转
```

适用于 AI 自我迭代的代码质量保障、CI 前的自主修复预检、以及「不想靠模型自报 green」的任何场景。

## 特性

- **验证闸门（证据锚点）** — 声称"已修复"必须有独立检查在真实代码输出里逐字符出现才被采信，杜绝模型自说自话的假绿。
- **沙箱验证 Healer** — 在临时副本里试修复、重跑验证、证明变绿，再交付候选；**绝不改你代码**，落地由你或上层 agent 决定。
- **四道刹车（通用范式）** — 根因闸门 / 判别测试 / 验证闸门 + 证据锚点 / 逃逸阶梯 + 防空转；任何一轮「全绿」都得过判别测试，否则继续修。
- **12 个可插拔分析轴** — 安全 / 复杂度 / 重复 / 仓库卫生 / 文档 / 依赖 / 发版 / 类型 / 无障碍 / 依赖分类 / 成熟度 / 健壮性；零依赖、离线、确定性，开箱即用。
- **文档即契约（dogfood）** — 引擎对自身源码自检 ALL GREEN（health 92/100），绝不 double standard；加一个新检查器 = 丢一个文件进 `veriloop/axes/`。
- **诚实降级** — 无 git 历史的仓库，发版一致性轴如实报「不适用」，绝不伪造通过。

## 快速开始

### 安装

```bash
# PyPI（推荐）
pip install veriloop

# 或从源码跑（零依赖，Python 3.8+）
git clone https://github.com/huanweide/veriloop.git
cd veriloop && PYTHONPATH=. python -m veriloop --help
```

### 一次性审计

```bash
veriloop scan ./your-project
```

### 跑收敛循环（生成沙箱验证过的修复候选）

```bash
veriloop check ./your-project
```

### 自证它能拦住「假修复」

```bash
veriloop selftest
```

输出示例（对含 `eval` 的脏项目跑 `check`）：

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

> ⚠️ **VeriLoop 只交付「经沙箱验证的修复候选」，绝不擅自改你的代码。** 这是安全边界。

## CLI 命令速查

| 命令 | 作用 |
|---|---|
| `veriloop scan <path>` | 一次性跑 12 轴，输出各轴 通过 / 分数 / 证据 |
| `veriloop check <path>` | 跑收敛循环：审计 + Healer 生成沙箱验证的修复候选 |
| `veriloop selftest` | 自证能拦住「假修复」（内置对照样本） |

## 架构

VeriLoop 默认使用**验证驱动的收敛循环**（而非固定轮数空转）：每一轮「全绿」都必须通过判别测试，否则继续修；连续空转触发刹车停转。

### 原语（Primitive）表

| 概念 | 含义 |
|---|---|
| **分析轴报告** | 每个轴返回 `{通过? 分数 证据(file:line)}`，全仓取平均得 health |
| **验证闸门** | 声称修复成立 ⟺ 独立检查在真实代码输出里逐字符命中 |
| **判别测试** | 修复前必红 + 修复后必绿，二态对照锁死证据 |
| **Healer 沙箱** | 临时副本试修 → 重跑判据 → 证明变绿 → 交付候选（不改源） |
| **逃逸阶梯 / 防空转** | 卡住强制换打法；连续 N 次无进展则停转报人工 |

### 收敛循环

```
扫描(12轴) → 判红? ──否──> 判别测试通过? ──是──> 交付(ALL GREEN)
                │                        │
               是                      否
                ▼                        ▼
         四道刹车(根因/判别/验证/逃逸)   继续修(不空转)
                │
          可验证红轴?
                ├─ 是 → Healer 沙箱验证 → 证明变绿 → 交付候选
                └─ 否 → 逃逸阶梯/防空转 → 停转报人工
```

### 核心模块

| 模块 | 文件 | 说明 |
|---|---|---|
| 感知层 | `veriloop/engine.py` · `PerceptionLayer` | 加载并调度 12 个分析轴，产出带证据的轴报告 |
| 刹车内核 | `veriloop/engine.py` · `BrakeCore` | 四道刹车：根因闸门 / 判别测试 / 验证闸门 / 逃逸阶梯 |
| 收敛协议 | `veriloop/engine.py` · `ConvergenceProtocol` | 逃逸阶梯 + 防空转 |
| 修复候选 | `veriloop/healer.py` | 沙箱副本验证修复，绝不改用户代码 |
| 分析轴 | `veriloop/axes/*.py` | 12 个零依赖、离线、确定性检查器，可插拔 |
| CLI | `veriloop/cli.py` | `scan` / `check` / `selftest` 入口 |

不想读代码也能懂：见 [ARCHITECTURE.md](./ARCHITECTURE.md)（生活类比 + 术语表）。

## 加一个你自己的分析轴

```python
# veriloop/axes/myrule.py
from ._common import result

AXIS = 13

def evaluate(root):
    findings = []
    scanned = 0
    # ... 你的零依赖、离线检查逻辑 ...
    passed = len(findings) == 0
    score = 100 if passed else 60
    return result(AXIS, "myrule", passed, score, scanned, findings, "1 finding")
```

丢进去即生效，`veriloop scan` 会自动带上它。

## 路线图

- [x] 12 个内置分析轴 + 沙箱 Healer
- [x] `veriloop selftest` 自证拦假绿
- [ ] 更多领域轴模板（安全合规 / 性能 / i18n）
- [ ] 把修复候选回填为可审阅的 diff（仍由人确认）
- [ ] 更多 agent 接入示例

## 贡献

见 [CONTRIBUTING.md](./CONTRIBUTING.md)。欢迎提交你的分析轴与刹车策略。

## 安全边界

VeriLoop 只读取并分析你的代码、只交付「经沙箱验证的修复候选」。**它不会、也绝不修改你的源文件**。任何自动落地修复的行为都应由你或上层 agent 在显式授权后执行。

## License

[MIT](./LICENSE) © The VeriLoop Authors

## ⭐ Star VeriLoop

如果这个项目帮你挡住了一次「假绿」，点个 Star 让更多人看到 —— 也欢迎提 Issue / PR。

> 🔁 **VeriLoop** — 修没修好，让测试说了算。
