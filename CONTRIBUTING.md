# Contributing to VeriLoop

## 这是什么仓库

VeriLoop 是一个**带验证刹车的代码审计引擎**：12 个可插拔分析轴 + 一个收敛循环。它不是传统「跑一下就出结果」的工具——它的全部价值在于「修没修好由外部检查说了算」。这是一个 Python 包（`veriloop/`），外加 `tests/`。

## 目录结构

```
veriloop/
  engine.py        # 感知层 + 四道刹车 + 收敛循环 (run_loop)
  healer.py        # 沙箱验证修复候选（绝不改用户代码）
  cli.py           # scan / check / selftest 命令
  selftest.py      # 自证脚本
  axes/            # 12 个分析轴，每个一个模块，实现 evaluate(root)
tests/
  test_engine.py   # 回归门禁（委托 selftest）
```

## 本地门禁（提交前请自查）

```bash
# 1) 跑回归 + 自证（必须全绿）
PYTHONPATH=. python tests/test_engine.py

# 2) 对改动的目录跑一次真实审计，确认输出合理
PYTHONPATH=. python -m veriloop scan ./veriloop

# 3) 加新轴后，确认编号仍是 1..N 唯一、且能独立验证
PYTHONPATH=. python -m veriloop selftest
```

CI 会在每次 push / PR 跑同样的 `python tests/test_engine.py`。

## 分析轴的契约

新增一个轴，只需在 `veriloop/axes/` 放一个模块，实现：

```python
AXIS = <唯一编号 1..N>
def evaluate(root) -> dict:
    return {"axis": AXIS, "name": "...", "passed": bool, "score": 0..100,
            "scanned": int, "findings": [...], "evidence": "一行摘要"}
```

硬性要求：

- **零依赖、离线、确定性**——不能联网、不能依赖随机/时间。
- **绝不修改被扫描的树**——只读取、只报告。
- **先剥离字符串与注释再匹配**——避免把代码里的字符串字面量当成真调用（假阳）。
- **出错就返回红结果，不要抛异常**——一个轴崩了不能拖垮整个循环。

## 项目红线（以下 PR 会被拒）

- **不得移除或削弱四道刹车**（根因闸门 / 判别测试 / 验证闸门 / 逃逸阶梯+防空转）。这是 VeriLoop 的全部价值。
- **不得让「修好了」靠自我陈述**——任何修复/收敛都必须带外部验证证据（`file:line` 或沙箱重跑结果）。
- **不得让 Healer 自动落地修复到用户代码**——只交付验证过的候选，落地由人或上层 agent 决定（安全边界）。
- 分析轴不得引入依赖、不得修改被扫目录。

## 提交约定

- 一个 PR 聚焦一个议题；描述写清「改了什么 + 为什么 + 证据在哪」。
- 版本号随 CHANGELOG 更新。

欢迎提交你的分析轴与接入示例。
