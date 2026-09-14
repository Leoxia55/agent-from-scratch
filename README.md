# ScratchAgent

> **用约 3700 行代码，从第一性原理手写一个 AI Agent——让你从「会开车」到「会造车」。**

**为什么会有这个项目？** 学操作系统，就该写一个迷你 OS 来理解它；学数据库，就该写一个迷你数据库。学 Agent 开发，如果只是用现成的框架（LangChain / CrewAI / AutoGen 等）搭一搭，而不理解智能体内部的运行机制，就很难真正落地。

**用 Agent 好比开车，但要修车、甚至造车，就必须从底层原理出发——哪怕是造一辆简易的车，也能真正建立对「车」的技术理解。** 这个项目就是那辆「简易的车」：它用**约 3700 行可通读的 Python 代码**，把一个智能体拆成像乐高积木一样的基础部件，逐层拼装，最后通过 `examples/` 目录下 **20 个可运行示例**展示完整的智能体能力。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![mypy: strict](https://img.shields.io/badge/mypy-strict-green.svg)](pyproject.toml)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**作者**：AI动力老夏（25 年 IT 工程师 · 10 年大学计算机编程兼职讲师）

> 💬 **一起动手学 Agent**：关注公众号「**老夏的AI自习室**」（公众号 ID：`persist_ai_lab`），或扫描下方二维码加微信「**动力老夏**」，备注 **agent**，拉你进「Agent 动手学习群」。学习交流，前期全部免费。
>
> <p align="left"><img src="assets/wechat-dongli-laoxia.png" width="180" alt="微信二维码：动力老夏"></p>

本项目的目标不是提供一个“调用几行代码就完成一切”的黑盒框架，而是把智能体拆成可以阅读、调试和替换的基础部件，帮助你理解：模型如何决定下一步、工具如何被描述和执行、上下文如何持续、错误如何回传，以及多个智能体如何协作。

项目**不使用第三方智能体 SDK 或 Agent Framework 来实现核心循环**。项目使用 LiteLLM、Pydantic、OpenAI 兼容客户端、ChromaDB、Tavily、E2B 等基础库接入模型和基础设施，但 `Agent`、工具协议、执行上下文和编排逻辑由本项目自行实现。

> **如果你觉得这个项目对你有帮助，请点一个 Star ⭐ 支持一下。** 欢迎提交 Issue、PR，或分享给同样想「理解 Agent 底层原理」的朋友。

> 当前仓库是教学型源码，不提供官方 CLI 或服务端入口；使用方式是由外部 Python 脚本导入 `scratchagent`。仓库内附有 `examples/`（20 个可运行示例）、`tests/`（单元与集成测试）、`docs/`（分层文档）和 `course/`（21 章系统课程）供学习和验证。

## 目录

- [核心亮点速览](#核心亮点速览)
- [一、先定义 Agent](#一先定义-agent)
- [二、从第一性原理拆解](#二从第一性原理拆解)
- [三、核心执行闭环](#三核心执行闭环)
- [四、快速开始](#四快速开始)
- [五、工具调用](#五工具调用)
- [六、上下文、会话与确认](#六上下文会话与确认)
- [七、结构化输出](#七结构化输出)
- [八、编排与多智能体](#八编排与多智能体)
- [九、记忆、RAG、上下文优化](#九记忆rag上下文优化)
- [十、Skills 与代码执行](#十skills-与代码执行)
- [十一、代码结构](#十一代码结构)
- [十二、开发规范与质量检查](#十二开发规范与质量检查)
- [十三、边界与安全提醒](#十三边界与安全提醒)
- [十四、建议学习顺序](#十四建议学习顺序)
- [许可证](#许可证)

## 核心亮点速览

| 亮点 | 说明 |
| --- | --- |
| 🧩 **规模恰到好处** | 约 3700 行核心源码——多到有真东西，少到能通读、能调试、能替换 |
| 🔍 **拒绝黑盒 SDK** | 核心循环、工具协议、上下文、编排全部手写，每一步都能追到源码 |
| 🚀 **开箱即跑** | `examples/` 下 20 个可运行示例，覆盖工具调用、记忆、RAG、沙箱、多智能体 |
| 📚 **配套完整** | `course/` 21 章系统课程（每章：原理→源码精读→动手实验）+ `docs/` 30 篇分层文档 + `tests/` 单元与集成测试，不是「丢个仓库就走」 |
| 🛡️ **工程严谨** | Python 3.13 现代类型注解、mypy 严格检查、black/isort 统一风格、异步优先 |
| 🔐 **安全自觉** | Human-in-the-loop 人工审批、E2B 沙箱隔离、信任边界文档 |

## 一、先定义 Agent

普通的 LLM 调用通常是：

```text
输入 -> 模型 -> 输出
```

它适合问答、分类、摘要等一次性任务。Agent 面对的任务往往具有以下特点：

- 需要访问模型上下文之外的信息；
- 需要调用搜索、计算、文件或业务系统；
- 需要根据工具结果决定下一步；
- 需要跨多轮保留状态；
- 需要在执行高风险动作前等待人类批准；
- 需要把任务分给不同的专业角色。

因此，Agent 的本质不是一个特殊的模型，而是一个**由模型参与决策、由程序负责执行的闭环系统**：

```text
用户目标 + 当前状态
        |
        v
  构造模型请求
        |
        v
      LLM 决策
      /       \
普通回复      工具调用
   |             |
   |        程序执行工具
   |             |
   +------< 工具结果写回上下文
        |
        v
  最终结果 / 继续循环 / 请求确认 / 转移给其他 Agent
```

模型负责生成候选动作，程序负责验证边界、执行副作用、记录事实和决定何时停止。把这两部分分开，是理解 Agent 工程的起点。

## 二、从第一性原理拆解

ScratchAgent 将一个 Agent 拆为六个最小问题：

### 1. 模型看到了什么

模型不能直接读取 Python 对象。`types.py` 中的 `Message`、`ToolCall`、`ToolResult` 和 `SummaryMessage` 组成内部内容协议；`llm/_client.py` 再把它们转换为具体模型 API 所需的消息格式。

### 2. 模型可以做什么

工具必须同时具备：

- 名称；
- 人类和模型都能理解的描述；
- 参数 JSON Schema；
- 实际的 Python 执行函数；
- 可选的确认策略和请求处理钩子。

`FunctionTool` 和 `@tool` 负责把普通 Python 函数包装成这个协议。

### 3. 动作如何执行

模型返回 `ToolCall` 后，Agent 根据工具名查找工具，解析 JSON 参数，执行函数，再把结果封装为 `ToolResult`。工具异常会被转为错误结果，模型可以据此修正计划或给出失败说明。

### 4. 状态放在哪里

`ExecutionContext` 保存一次执行的事件序列、步骤计数、业务状态、最终结果、会话、长期记忆、沙箱和 Agent 转移信息。状态不应隐含在 prompt 字符串或全局变量中。

### 5. 什么时候停止

Agent 在以下情况之一发生时结束：得到最终结果、达到 `max_steps`、等待工具确认，或转移给另一个 Agent。最大步数是必要的保险丝，不能假设模型一定会自行停止。

### 6. 如何观察和恢复

每次用户输入、模型回复和工具结果都会写入 `Event`。事件日志既是发送给模型的历史，也是调试、会话恢复和长期记忆提取的原材料。

## 三、核心执行闭环

`Agent.run()` 的主要流程可以概括为：

1. 创建或恢复 `ExecutionContext`；
2. 按 `session_id` 恢复会话状态；
3. 按需准备 E2B 沙箱；
4. 处理上一次运行遗留的工具确认；
5. 追加用户事件；
6. 在 `max_steps` 内循环调用 `step()`；
7. 根据事件构造 `LlmRequest`；
8. 执行上下文优化和其他 before-LLM 回调；
9. 调用 `LlmClient.generate()`；
10. 记录模型回复；
11. 执行工具调用并记录工具结果；
12. 检查最终回复、待确认调用和 Agent 转移；
13. 保存会话和长期记忆，并清理由当前 Agent 创建的沙箱。

对应源码入口：

- `src/scratchagent/agent.py`：Agent 主循环、think、act 和停止判断；
- `src/scratchagent/types.py`：内部消息和事件协议；
- `src/scratchagent/context.py`：运行状态和结果类型；
- `src/scratchagent/llm/_client.py`：模型适配层。

## 四、快速开始

### 环境要求

- Python `>=3.13,<3.14`；
- 一个支持工具调用的模型端点；
- 对应服务商的 API Key 和 Base URL。

### 安装

项目使用 `pyproject.toml` 管理依赖。使用 `uv` 时：

```bash
uv sync
```

也可以安装开发依赖：

```bash
uv sync --extra dev
```

复制环境变量模板并填写需要的配置：

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux
```

不要把包含真实密钥的 `.env` 提交到 Git。进程环境变量优先于 `.env` 中的同名变量。

### 最小 Agent

下面的代码使用 OpenAI 兼容端点。这里的 `openai_compat` 只表示模型接口协议，不表示 Agent 使用了第三方 Agent 框架。

```python
import asyncio

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config


async def main() -> None:
    config = resolve_model_config(
        provider=Provider.OPENAI_COMPAT,
        model="gpt-4o-mini",
    )
    model = LlmClient(default_config=config)
    agent = Agent(
        model=model,
        name="teacher",
        instruction="Explain concepts clearly and say when information is uncertain.",
        max_steps=5,
    )

    result = await agent.run("What is the difference between an LLM call and an Agent?")
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
```

`resolve_model_config()` 会读取：

- `OPENAI_API_KEY`；
- `OPENAI_BASE_URL`。

也可以使用 `Provider.ANTHROPIC`、`Provider.LLAMA` 或 `Provider.LM_STUDIO`。不同提供商需要各自的环境变量，具体映射见 `src/scratchagent/llm/_config.py`。

项目通过 `scratchagent/config.py` 的 `load_project_env()` 统一加载 `.env`，该函数全局只加载一次，且不会覆盖进程环境中已存在的同名变量。

## 五、工具调用

工具调用的关键不是“让模型执行 Python”，而是建立一个可验证的协议：

```text
Python 函数
   |
   | 函数名 + 描述 + 类型标注
   v
工具 JSON Schema -> LLM
                         |
                         | ToolCall(name, arguments)
                         v
                    参数解析与校验
                         |
                         v
                     Python 执行
                         |
                         v
                 ToolResult 写回上下文
```

### 定义一个工具

```python
from scratchagent.tools import tool


@tool
def multiply(first_number: float, second_number: float) -> float:
    """Multiply two numbers."""
    return first_number * second_number
```

把工具传给 Agent：

```python
agent = Agent(
    model=model,
    tools=[multiply],
    instruction="Use the calculator when arithmetic is required.",
)
```

`@tool` 返回的是 `FunctionTool`。它会从函数签名生成输入 Schema，并兼容同步和异步函数。需要访问上下文的工具可以声明 `context` 参数：

```python
from scratchagent import ExecutionContext
from scratchagent.tools import tool


@tool
def read_state(context: ExecutionContext, key: str) -> str:
    """Read a value from the current execution state."""
    return str(context.state.get(key, ""))
```

`context` 是运行时注入参数，不会暴露给模型的工具 Schema。

### 工具确认

带有副作用的工具可以要求确认：

```python
from scratchagent.tools import tool


@tool(required_confirmation=True)
def publish_report(report: str) -> str:
    """Publish a report to an external system."""
    # 在真实项目中执行外部写操作
    return f"Published: {report}"
```

Agent 不会立即执行这类工具，而是返回 `AgentResult(status="pending")` 和 `pending_tool_calls`。用户批准后，将 `ToolConfirmation` 传回下一次 `run()`。批准、拒绝和参数修改都应在应用层明确记录。

项目还提供 `approval_callback`、`search_compressor` 等回调示例。回调是显式注入的扩展点；默认导出的文件工具并不会自动获得审批策略。

## 六、上下文、会话与确认

### ExecutionContext

`ExecutionContext` 是 Agent 的运行时状态中心：

```python
from scratchagent import ExecutionContext

context = ExecutionContext()
context.state["language"] = "zh-CN"
result = await agent.run("Continue the task", context=context)
```

上下文中的 `events` 保存事实记录，`state` 保存应用状态。不要把需要程序可靠读取的值只放在自然语言中。

### 多轮会话

LLM API 本身通常是无状态的。ScratchAgent 通过 `Session` 和 `BaseSessionManager` 保存多次调用之间的事件与状态。开发和测试可使用内存实现：

```python
from scratchagent.memory import InMemorySessionManager

session_manager = InMemorySessionManager()
agent = Agent(model=model, session_manager=session_manager)

first = await agent.run(
    "My preferred language is Chinese.",
    session_id="demo-session",
    user_id="demo-user",
)
second = await agent.run(
    "What language did I prefer?",
    session_id="demo-session",
    user_id="demo-user",
)
```

生产环境应继承 `BaseSessionManager` 实现数据库或其他持久化后端，而不是把存储逻辑写进 Agent 主循环。

### Human-in-the-loop

确认流程可以抽象为：

```text
模型提出有副作用的 ToolCall
        |
        v
应用展示工具名、参数和风险
        |
批准 / 拒绝 / 修改参数
        |
        v
Agent 恢复执行并记录结果
```

确认是授权边界，不是模型提示词。任何外部写入、删除、付款、发送消息或执行任意代码的能力，都应在工具层和应用层同时设置约束。

## 七、结构化输出

需要稳定数据结构时，可以传入 Pydantic 模型作为 `output_type`：

```python
from pydantic import BaseModel
from scratchagent import Agent


class Answer(BaseModel):
    conclusion: str
    confidence: float


agent = Agent(
    model=model,
    output_type=Answer,
    instruction="Return a concise, evidence-based answer.",
)
result = await agent.run("Assess whether the claim is supported by the supplied context.")
answer: Answer = result.output
```

Agent 会把最终答案建模为一个 `final_answer` 工具，并使用 Pydantic 校验结果。结构化输出适合程序继续处理的场景；面向人的回答则可以直接使用文本结果。

## 八、编排与多智能体

### 顺序工作流

`SequentialWorkFlow` 将同一个 `ExecutionContext` 依次传给多个 Agent，适合“研究 -> 审核 -> 汇总”：

```python
from scratchagent import SequentialWorkFlow

workflow = SequentialWorkFlow(
    agents=[researcher, reviewer, writer],
)
result = await workflow.run("Prepare a short technical report.")
```

### 并行工作流

`ParallelWorkFlow` 使用 `asyncio.gather` 并发执行多个 Agent，并合并事件和输出。它适合相互独立的调查或评估任务。共享可变状态时必须自行设计隔离、合并和冲突策略。

```python
from scratchagent import ParallelWorkFlow

workflow = ParallelWorkFlow(agents=[fact_checker, risk_analyst])
result = await workflow.run("Analyze this proposal from both perspectives.")
```

### 循环工作流

`LoopWorkFlow` 重复运行一组 Agent，直到 `stop_condition` 返回真或达到 `max_iterations`：

```python
from scratchagent import LoopWorkFlow


def is_ready(result, iteration: int) -> bool:
    return iteration >= 3 or bool(result.output)

workflow = LoopWorkFlow(
    agents=[draft_agent, critique_agent],
    stop_condition=is_ready,
    max_iterations=5,
)
```

### Agent 转移

工作流是程序预先定义的控制流；转移是由当前 Agent 根据任务动态选择下一个 Agent。`create_transfer_tool()` 为目标 Agent 生成 `transfer_to_agent` 工具，Agent 执行该工具后通过 `context.transfer_to` 触发转移。

```python
from scratchagent.orchestration import create_transfer_tool

transfer_tool = create_transfer_tool([researcher, writer])
router = Agent(
    model=model,
    name="router",
    tools=[transfer_tool],
    sub_agents=[researcher, writer],
)
```

## 九、记忆、RAG、上下文优化

这些概念解决的是不同问题，不应混为一谈：

| 能力 | 解决的问题 | ScratchAgent 实现 |
| --- | --- | --- |
| 会话 | 当前用户的连续对话和状态 | `Session`、`InMemorySessionManager` |
| 长期记忆 | 从历史任务中提取可复用经验 | `TaskMemoryManager`、ChromaDB |
| RAG | 从外部文档检索相关知识 | 分块、embedding、余弦相似度 |
| 上下文优化 | 历史太长，无法全部放入请求 | 滑动窗口、压缩、摘要 |

### 长期任务记忆

`TaskMemoryManager` 从执行上下文中提取任务摘要、处理方法、最终答案、正确性和错误分析，再使用向量检索查找相似任务。`MemoryTool` 可在发送模型请求前注入相关历史经验。

它是“任务经验记忆”的教学实现，不是通用的人类记忆模型。记忆的提取、去重和正确性判断都应经过评估，不能把模型生成的历史记录直接当成事实。

### RAG

`src/scratchagent/rag.py` 提供三个基础步骤：

```python
from scratchagent import fixed_length_chunking, get_embeddings, vector_search

chunks = fixed_length_chunking(document, chunk_size=500, overlap=50)
embeddings = get_embeddings(chunks)
hits = vector_search("target question", chunks, embeddings, top_k=3)
```

RAG 提供的是外部知识，不会自动形成记忆，也不能替代工具执行和结果验证。

### 上下文优化

`ContextOptimizer` 可以作为 before-LLM callback 显式传入 Agent。常见策略是：

1. 先压缩过长的工具参数和工具结果；
2. 再使用滑动窗口保留必要的近期历史；
3. 最后用摘要替代较早的事件。

上下文优化是有损变换。必须保留任务目标、约束、关键证据和未完成动作，并通过测试验证摘要是否丢失关键信息。

## 十、Skills 与代码执行

### Skills

Skills 是带有说明文件的可发现目录。每个技能目录至少包含：

```text
skills/
└── csv-analysis/
    └── SKILL.md
```

`SKILL.md` 以简单 frontmatter 提供 `name` 和 `description`：

```markdown
---
name: csv-analysis
description: Analyze CSV files with Python.
---

# CSV analysis

Read this file before using the skill.
```

`discover_skills()` 发现技能，`generate_skills_prompt()` 将技能名称、描述和沙箱路径注入模型指令。技能目录还可以在 E2B 沙箱中上传，供模型按说明使用。

### E2B 沙箱

设置 `code_execution="e2b"` 后，Agent 可以准备 E2B 环境并使用：

- `execute_python_in_e2b`：执行 Python；
- `base_e2b_tool`：执行 shell 命令；
- `upload_file_to_e2b`：上传本地文件。

使用前配置 `E2B_API_KEY`。网络访问默认关闭，创建沙箱时必须显式开启。沙箱不是权限系统的替代品；执行代码、上传文件和网络访问仍然需要资源范围、超时和审批策略。

## 十一、代码结构

```text
.
├── pyproject.toml                 # 依赖、类型检查、测试和质量命令
├── .env.example                   # 环境变量模板
├── LICENSE                        # 许可证
├── README.md                      # 教学说明
├── examples/                      # 20 个可运行的完整示例
│   ├── basic_agent.py             # 最小 Agent + 工具调用示例
│   ├── callback_agent.py          # 工具调用前后回调拦截
│   ├── human_in_loop_agent.py     # 危险工具人工确认（Human-in-the-loop）
│   ├── planning_reflection_agent.py # 规划与反思（create_tasks / reflection）
│   ├── session_agent.py           # 多轮会话持久化
│   ├── memory_agent.py            # 长期记忆（ChromaDB）
│   ├── rag_agent.py               # 检索增强生成（RAG）
│   ├── e2b_agent.py               # E2B 沙箱执行 Python 代码
│   ├── skill_agent.py             # Skills 技能系统 + PDF 合并
│   ├── sequential_wf_agent.py     # 多智能体顺序编排
│   ├── parallel_wf_agent.py       # 多智能体并行编排
│   ├── loop_wf_agent.py           # 多智能体循环编排
│   ├── transfer_to_agent.py       # 多智能体路由转接
│   ├── remote_server_fast_demo.py # FastMCP MCP 服务器示例（供 fast_mcp_agent 连接）
│   └── fast_mcp_agent.py          # FastMCP 集成示例（端到端调用 MCP 工具）
├── tests/                         # 单元测试与集成测试
│   ├── conftest.py                # 顶层 fixtures
│   ├── unit/                      # 单元测试（按模块划分）
│   └── integration/               # 集成测试
├── course/                        # 21 章系统课程（原理 → 源码精读 → 动手实验）
├── docs/                          # 分层文档（教程、How-to、概念、参考）
├── labs/                          # 实验脚本（e2b/litellm/mcp/rag）
└── src/scratchagent/
    ├── __init__.py                # 公开 API 汇总导出
    ├── agent.py                   # Agent 主循环
    ├── config.py                  # .env 统一加载（load_project_env）
    ├── context.py                 # ExecutionContext 与 AgentResult
    ├── types.py                   # Message、ToolCall、ToolResult、Event
    ├── rag.py                     # 文本分块、向量检索
    ├── skills.py                  # Skills 发现与提示词生成
    ├── llm/
    │   ├── __init__.py            # LlmClient、Provider 等导出
    │   ├── _client.py             # LLM 请求/响应适配
    │   └── _config.py             # Provider 和环境变量解析
    ├── tools/
    │   ├── __init__.py            # 工具导出
    │   ├── _base.py               # BaseTool、FunctionTool、@tool
    │   ├── _helpers.py            # Schema 生成等工具辅助
    │   ├── _calculator.py         # 计算器示例
    │   ├── _file_tools.py         # 文件能力
    │   ├── _search.py             # Tavily 搜索
    │   ├── _callbacks.py          # 审批与结果压缩回调
    │   ├── _memory_tool.py        # 记忆注入工具
    │   └── _code_execution.py     # E2B 工具
    ├── memory/
    │   ├── __init__.py            # 记忆模块导出
    │   ├── _session.py            # 会话抽象与内存实现
    │   ├── _long_term.py          # 任务长期记忆
    │   └── _context_optimizer.py  # 上下文管理
    ├── orchestration/
    │   ├── __init__.py            # 工作流导出
    │   ├── _sequential.py         # 顺序工作流
    │   ├── _parallel.py           # 并行工作流
    │   ├── _loop.py               # 循环工作流
    │   ├── _transfer.py            # Agent 转移
    │   └── _planning_reflection.py # 规划与反思工具
    └── sandbox/
        ├── __init__.py            # 沙箱模块导出
        └── _e2b_sandbox.py        # E2B 生命周期管理
```

## 十二、开发规范与质量检查

项目使用 Python 3.13、类型标注、Pydantic 数据模型和异步接口。建议每次修改都遵循：

1. 先确认内部协议和状态边界；
2. 为工具输入、输出和异常定义清晰契约；
3. 不在模块之间复制模型供应商格式；
4. 将外部副作用放在工具中，并提供审批或资源限制；
5. 对循环设置最大步数或最大迭代次数；
6. 对上下文压缩和并发合并编写测试；
7. 保持同步工具和异步工具都能被一致调用。

### 测试

测试已落地在 `tests/` 目录，包含单元测试（`tests/unit/`）和集成测试（`tests/integration/`）。pytest 配置位于 `pyproject.toml` 的 `[tool.pytest.ini_options]`，已启用 `pythonpath = ["src"]`、`asyncio_mode = "auto"`，并预置 `e2e`、`slow` 两个 marker。

```bash
# 运行全部测试
uv run pytest tests/

# 仅运行单元测试
uv run pytest tests/unit/

# 跳过需要真实 API Key 的端到端测试
uv run pytest tests/ -m "not e2e"
```

### 类型检查与格式化

dev 依赖包含 `mypy`、`black`、`isort` 和 `poethepoet`，可通过 poe 任务或直接命令调用：

```bash
# 类型检查
uv run mypy src/

# 格式化
uv run black src/ examples/ tests/
uv run isort src/ examples/ tests/

# 测试与覆盖率
uv run pytest tests/ --cov=src/scratchagent --cov-report=term-missing
```

`pyproject.toml` 中预置了以下 poe 任务：

```bash
uv run poe mypy          # 类型检查
uv run poe test          # 运行测试
uv run poe test-cov      # 测试 + 覆盖率
uv run poe format-black  # black 格式化
uv run poe format-isort  # isort 导入排序
```

新增功能时，应优先补充针对消息转换、工具 Schema、停止条件、确认恢复、会话恢复和并发合并的测试。

## 十三、边界与安全提醒

这是用于学习内核原理的项目，不应未经审计直接暴露为生产级自主执行服务。特别注意：

- 文件工具可能读取、删除或解压本地路径；
- 解压和文件删除应限制在明确的工作目录，并增加路径校验；
- E2B shell、Python 和文件上传工具具有较强能力；
- 外部搜索、模型调用和多模态处理会把数据发送给第三方服务；
- API Key 只能通过环境变量或安全凭证管理提供；
- 并行工作流共享上下文时存在竞态和合并语义问题；
- 模型输出、历史记忆和 RAG 内容都必须视为不可信输入；
- `max_steps`、超时、速率限制、预算限制和人工审批应在应用层配置。

“工具确认”只能防止未经批准的调用，不能替代沙箱隔离、最小权限、输入校验、审计日志和网络控制。

## 十四、建议学习顺序

推荐按以下顺序阅读和动手修改：

1. 阅读 `types.py`，理解内部消息协议；
2. 阅读 `context.py`，理解状态为何独立于消息；
3. 阅读 `llm/_client.py`，观察内部协议如何映射到模型 API；
4. 阅读 `tools/_base.py`，实现一个最小同步工具和异步工具；
5. 阅读 `agent.py` 的 `run()`、`step()`、`think()` 和 `act()`；
6. 为 Agent 加入工具错误恢复和停止条件测试；
7. 实现一个持久化 `BaseSessionManager`；
8. 对比滑动窗口、压缩和摘要的上下文效果；
9. 使用顺序、并行和循环工作流组合多个角色；
10. 最后再接入长期记忆、RAG、Skills 和沙箱。

学习时可以尝试替换单个部件：先用固定的 `before_llm_callback` 模拟模型，再替换成真实 LLM；先用内存会话，再替换成数据库；先用纯 Python 检索，再替换成向量存储。这样能够清楚地看到每个抽象解决了什么问题。

## 许可证

许可证信息以仓库中的 `LICENSE` 文件为准。
