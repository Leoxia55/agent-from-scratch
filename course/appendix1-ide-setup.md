# 附录 1：VS Code + Claude Code 开发环境

> 本附录为工程实践章，无对应源码模块。目标是让学员在一套**可复现、可调试**的本地环境中跑通 `scratchagent`。

---

## 一、为什么需要规范的开发环境

前 20 章都在读源码、写代码，但「能写」和「能**高效地调试、审计**」是两回事。`scratchagent` 是一个**异步**框架（`Agent.run` 是 `async def`），依赖 Pydantic、LiteLLM、ChromaDB 等第三方库，还涉及 `__all__` 导出、mypy 静态检查——这些特性都要求一个「正确配置」的环境，否则你会被「async 函数没 await」「类型检查报错看不懂」「断点不进协程」这类问题反复绊住。

本附录聚焦两件事：

1. **VS Code 配置**：让异步代码可断点调试、类型检查实时反馈；
2. **Claude Code 配置**：把「AI 辅助编程」接进日常开发循环。

---

## 二、VS Code 环境配置

### 2.1 必备扩展

| 扩展 | 用途 | 关键配置 |
|---|---|---|
| Python (ms-python.python) | 解释器选择、调试、测试 | 选 `3.13` 解释器 |
| Pylance | 类型检查、跳转、补全 | 与 mypy 配合 |
| Ruff 或 Black+isort | 格式化（项目用 black+isort） | `line-length=88` |

### 2.2 解释器与虚拟环境

项目锁定 `requires-python = ">=3.13.0, <3.14"`（`pyproject.toml`），且大量使用 PEP 604（`str | None`）、PEP 695 等新语法。**必须用 Python 3.13**，用 3.12 会语法报错。

```bash
# 建虚拟环境（Windows）
python -m venv .venv
.venv\Scripts\activate

# 安装项目（含 dev 依赖）
pip install -e ".[dev]"
```

### 2.3 调试异步代码

`Agent.run` 是 `async def`，调试异步代码需要两个要点：

1. **用 `asyncio.run()` 包裹入口**：断点会正常命中协程内部；
2. **`justMyCode` 设为 false**（可选）：允许进入第三方库（如 litellm）源码，理解调用链。

`.vscode/launch.json` 示例：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Agent",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

**调试技巧**：在 `agent.py` 的 `run()` 主循环内（`for` 循环处）设断点，可以观察每一轮 `step` 的 `context.events` 如何增长——这是理解 ReAct 循环最直观的方式。

### 2.4 类型检查集成

项目用 mypy（`[tool.mypy]` 配置），Pylance 默认也做类型检查。二者定位不同：

| 工具 | 定位 | 何时用 |
|---|---|---|
| Pylance | 编辑器**实时**反馈 | 写代码时即时看红线 |
| mypy | CI 里的**权威**门禁 | 提交前 `poe mypy` |

建议 Pylance 和 mypy 都用，但以 mypy 为准（因为 CI 跑的是 mypy）。

---

## 三、Claude Code 配置

### 3.1 定位

Claude Code 是「AI 辅助编程」的入口。在本教程的语境下，它的价值不是「替你把 20 章的代码写完」，而是：

- **对照审计**：让 AI 逐符号核对你写的代码与「标准答案」`D:\00_persist\agent-from-scratch` 的差异；
- **解释报错**：贴出 mypy/pytest 报错，让 AI 解释根因；
- **生成测试**：为某个函数快速生成 pytest 用例骨架。

### 3.2 建议的工作流（人 + AI 分工）

```text
人：精读源码 → 理解原理 → 亲手写一个模块
        ↓ 写完
AI：对照标准答案审计 → 指出差异/笔误
        ↓ 修订
人：跑 pytest + mypy 验证 → 记录踩坑
```

**关键原则**：**先自己写，再让 AI 审**。如果直接让 AI 生成代码，你学不到「源码精读」的能力——而这正是本教程的核心目标。

### 3.3 常用指令示例

```text
# 对照审计
"对照 D:\00_persist\agent-from-scratch\src\scratchagent\agent.py，
 审计我写的 agent.py，逐符号指出差异"

# 解释报错
"这个 mypy 报错是什么原因？
  error: Incompatible types in assignment ..."

# 生成测试骨架
"为 vector_search 函数生成 pytest 用例，覆盖 top_k 边界"
```

---

## 四、自检

- [ ] 我能用 Python 3.13 建虚拟环境并 `pip install -e ".[dev]"`。
- [ ] 我能用 VS Code 调试 `async def` 的 `Agent.run`，并在主循环设断点观察 events 增长。
- [ ] 我能区分 Pylance（实时）和 mypy（CI 门禁）的定位。
- [ ] 我理解「先自己写、再让 AI 审」的分工原则。
