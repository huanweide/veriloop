# VeriLoop · 会自己证明修复成立的代码审计引擎

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![CI](https://github.com/huanweide/veriloop/actions/workflows/ci.yml/badge.svg)
![Stars](https://img.shields.io/github/stars/huanweide/veriloop?style=social)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

> **English TL;DR** — VeriLoop is a self-iterating code auditor that *proves its own fixes*. It runs 12 pluggable analyzers over your codebase, then applies four verification brakes so a problem is only declared "fixed" when an **external check** confirms it — not when the model says so. Zero dependencies, offline, deterministic. `veriloop selftest` proves it catches fake-green fixes. MIT.

> **一句话**：让 AI 自我迭代不再「假绿空转」——修没修好，由代码之外的检查说了算，并在沙箱里真跑一遍证明。

---

## 30 秒看懂（demo）

```
用户：把这段代码的注入隐患修一下
普通循环：✅ 已修复（改成参数化）        ← 模型自己说"修好了"
VeriLoop：验证闸门复检 → 重跑安全轴 → 发现 username 字段仍可注入
         判别测试：修复前必红 + 修复后必绿 → 旧"修复"没过门禁
         → 不出"已修复"，继续修到真过测试才交付
```

差别只有一句话：**「修好了」的判据来自模型之外，不来自模型自己。**

---

## 为什么需要它

AI 自我迭代常犯一个错：每轮测试都过，问题却还在。VeriLoop 的全部设计只围绕一句话——

> **放行判据必须来自模型之外；只做合理且必要的改动。**

| 你现在的痛点 | VeriLoop 怎么做 |
|---|---|
| 改完一句「已修复」却没真修好 | 验证闸门：必须独立重跑检查，证据锚定 `file:line` |
| 同一缺陷换说法来回返工 | 根因闸门 + 逃逸阶梯：卡住就强制换打法，不空转 |
| 不知道改了到底有没有效 | Healer 在沙箱副本里真跑，证明变绿才交付候选 |
| 规则散落、难扩展 | 12 个可插拔分析轴，加一个只需丢一个文件 |

---

## 快速上手

```bash
# 安装（零依赖，Python 3.8+）
pip install veriloop
# 或直接从源码跑
git clone https://github.com/huanweide/veriloop.git && cd veriloop && PYTHONPATH=. python -m veriloop

# 一次性审计
veriloop scan ./your-project

# 跑收敛循环（审计 + 生成沙箱验证过的修复候选）
veriloop check ./your-project

# 证明它能拦住"假修复"
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

> 注意：**VeriLoop 只交付「经沙箱验证的修复候选」，绝不擅自改你的代码。** 落地由你或上层 agent 决定——这是安全边界。

---

## 特性

- **四道刹车（通用范式）**：根因闸门 / 判别测试 / 验证闸门 + 证据锚点 / 逃逸阶梯 + 防空转。
- **12 个可插拔分析轴**：安全、复杂度、重复、仓库卫生、文档、依赖、发版、类型、无障碍、依赖分类、成熟度、健壮性。零依赖、离线、确定性。
- **沙箱验证的 Healer**：对可机械验证的红轴，在临时副本里试修复、重跑验证、证明变绿，再交付候选。
- **可扩展**：加一个新检查器 = 在 `veriloop/axes/` 写一个 `evaluate(root)` 函数，引擎自动加载。
- **诚实降级**：无 git 历史的仓库，发版一致性轴如实报「不适用」，绝不伪造通过。

---

## 架构（人人能懂）

不想读代码也能懂：见 [ARCHITECTURE.md](./ARCHITECTURE.md) —— 用生活类比讲清四道刹车、一轮循环、12 个轴，并附术语表。

```
                 ┌──────────────────────────────┐
                 │   PerceptionLayer 感知层      │
                 │   12 个可插拔分析轴 (axes)     │
                 └──────────────┬───────────────┘
                                │ 每份 report: 通过? 分数? 证据?
                 ┌──────────────┴───────────────┐
                 │   BrakeCore 四道刹车           │
                 │   ① 根因闸门                   │
                 │   ② 判别测试                   │
                 │   ③ 验证闸门 + 证据锚点         │
                 │   ④ 逃逸阶梯 + 防空转           │
                 └──────────────┬───────────────┘
                                │ 有红轴且可验证
                 ┌──────────────┴───────────────┐
                 │   Healer 沙箱验证修复候选       │
                 │   (只交付候选, 不改你代码)       │
                 └──────────────────────────────┘
```

---

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

---

## 路线图

- [x] 12 个内置分析轴 + 沙箱 Healer
- [x] `veriloop selftest` 自证拦假绿
- [ ] 更多领域轴模板（安全合规 / 性能 / i18n）
- [ ] 把修复候选回填为可审阅的 diff（仍由人确认）
- [ ] 更多 agent 接入示例

欢迎 **Star** 追踪进展，也欢迎提交你的分析轴。

---

## 贡献

见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## License

[MIT](./LICENSE) © The VeriLoop Authors
