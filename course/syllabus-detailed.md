# 《从零构建 AI Agent》课程大纲 202609

> **课程定位（一句话）**：学完本课程，学员能够**亲手搭建出一个完整可运行的 `agent-from-scratch` 项目**——这个项目不是教学玩具，而是逐章生长出的、经得起审计的真实工程。
>
> **课程最终目标（贯穿全程的唯一主线）**：从第 1 章到第 20 章，学员跟随着课程的每一步，**从空目录开始，一行一行写出一个约 3700 行的完整 Agent 框架**——涵盖 LLM 调用与 LiteLLM 封装、消息类型与通信总线、工具注册与调用、ReAct 循环、结构化输出、MCP、上下文管理、记忆管理、上下文优化、规划与反思、Skills 渐进式披露、E2B 代码执行沙箱、多智能体编排、Transfer/A2A，以及注解类安全 Python 规范编程。**每一章都向前推进同一个项目，而非另起炉灶**；课程结束时，学员手里不是一堆零散的 demo，而是一套自己亲手写就、跑得通、能继续扩展的 Agent 框架。
>
> **本课程拒绝的教法**：囫囵吞枣地调用 LangChain / CrewAI / AutoGen 等现成 SDK API。SDK 会遮蔽 Agent 的内部机制，学完只会"用"而不会"造"。本课程反过来——先造，再用（附录中再回头对比 SDK 的取舍）。
>
> **授课对象**：计算机相关专业大学生、具备一定 Python 基础的软件工程师、对大模型与智能体开发感兴趣的人员。
>
> **前置要求**：Python 3.13+ 基础语法、基本类型注解（PEP 585/604）、`async/await` 异步编程基础、Pydantic 基础、`uv` 包管理工具的基本使用。
>
> **授课总课时**：建议 40～48 学时（正课第 0~20 章共 21 章 + 3 个附录），每章约 2 学时，含理论讲解 + 源码精读 + 动手实验。其中**动手实验是主课时**，讲解与源码精读服务于"把这一步代码写出来"。

---
## 基本信息
| 项目        | 内容                                             |
| --------- | ---------------------------------------------- |
| 项目名称      | `agent-from-scratch`（Python 包名 `scratchagent`） |
| 项目定位      | 从零手写 AI Agent 的教学型框架，拒绝"黑盒调用 SDK"              |
| 开源协议      | MIT License                                    |
| Python 版本 | 3.13（`requires-python = ">=3.13.0, <3.14"`）    |
| 作者        | YouliangXia（youliangxia0505@gmail.com）         |
| 仓库地址      | https://github.com/Leoxia55/agent-from-scratch |
| 构建系统      | Hatchling（PEP 517）                             |
| 依赖管理      | `uv` + `uv.lock`（锁文件约 46 万字节，依赖可复现）            |

## 一、课程设计原则

1. **项目贯通是第一原则**：全程只有一个项目、一条主线——学员从空目录开始，逐步搭出完整的 `agent-from-scratch`。每章结束时，项目都能跑；每章新增的代码，都是在"上一章能跑的版本"上叠加。不允许出现"这章的例子和上章没关系"的断裂。
2. **从最小内核逐层生长**：全课程围绕第 4 章的"最小可运行 ReAct 内核"展开，后续所有能力（session、memory、callback、code execution、skills、multi-agent）都是"在这个内核上叠加"，而不是替换内核。**学员从始至终维护的是同一份代码库。**
3. **结论先行，证据驱动**：每章先给出"这个模块解决了什么问题"，再动手写代码验证，最后用正反例对比"好的实现 vs 常见错误实现"。
4. **源码即教材**：每一章都对应到 `scratchagent/` 下的具体源码文件，学生写的是真实、已通过审计（mypy 3 错误、`__all__` 29 符号零缺失、93 分）的工程代码，而非玩具示例。参考项目本身就是"学员最终应该写出的成品"的答案对照。
5. **安全边界贯穿始终**：文件工具、代码执行、MCP、人工审批（Human-in-the-loop）的安全考虑不单独成章，而是渗透进每一处涉及外部副作用的能力。
6. **规范即教学内容**：PEP 585/604/695 类型注解、`TYPE_CHECKING` 延迟导入、循环依赖规避、`__all__` 包导出、`from __future__ import annotations` 等工程规范，本身就是一条隐藏的"第二条教学主线"，从第 1 章搭脚手架起就持续贯彻。

---

## 二、课程主线与两大知识脉络

本课程有**两条并行的知识脉络**，最终合流为"能自主设计 Agent 框架"的能力：

| 脉络 | 内容 | 贯穿章节 |
|------|------|----------|
| **脉络 A：Agent 机制** | LLM 调用 → 消息协议 → 工具调用 → ReAct 循环 → 记忆 → 规划 → 沙箱 → 多智能体 | 第 2 章 → 第 20 章 |
| **脉络 B：Python 工程规范** | uv 脚手架 → 类型注解 → 包结构 → 循环导入 → 测试 → 审计 | 第 1、3 章 + 附录 1、2 |

**能力跃迁点**（关键里程碑）：
- 第 8 章后：能独立写出一个带工具的 ReAct Agent。
- 第 15 章后：能理解并实现上下文压缩、记忆注入。
- 第 17 章后：能安全地让 Agent 执行代码。
- 第 20 章后：能编排多智能体、实现动态 Transfer 转交。

---

## 三、课程大纲主体

### 阶段 0：认知与准备（第 0～1 章）

---

#### 第 0 章：智能体（Agent）及 Agent 开发全景

**核心问题**：什么是 Agent？它和"会聊天的 LLM"有什么区别？

**教学目标**：
1. 理解 LLM 与 Agent 的本质差异——LLM 是无状态的"大脑"，Agent 是"大脑 + 手脚 + 记忆 + 决策循环"。
2. 认识主流 Agent 产品（ChatGPT、Claude、Manus、Perplexity 等）和开发平台（LangChain、LlamaIndex、CrewAI、AutoGen、Dify、Coze 等）。
3. 建立"自研 Agent 需要哪些基本技术"的完整地图。

**核心内容**：
- LLM 的无状态特征：每次请求独立，没有记忆、没有行动能力。
- Agent 的定义：感知环境 → 推理决策 → 执行动作 → 观察反馈的闭环系统。
- ReAct 模式的直观介绍（Thought → Action → Observation 循环）。
- Agent SDK vs 自研框架的取舍：SDK 上手快但遮蔽原理，自研代码量大但掌握第一性原理。
- 本课程选型的理由：为何选择"读源码 + 手写"而非"调 API"。

**本章对应的项目证据**：`README.md` 的章节规划、`project-requirements.md` §2.2 教学目标。

**动手实验**：使用一个现有 Agent 产品完成一个多步任务，记录它调用了哪些工具、经历了多少轮思考。

---

#### 第 1 章：agent-from-scratch 项目预览

**核心问题**：这个项目长什么样？如何跑起来？

**教学目标**：
1. 克隆/下载项目，理解目录结构与模块边界。
2. 用 `scratchagent.Agent` 开发并运行第一个最简 Agent。
3. 建立"每章能力 → 源码模块"的映射认知。

**核心内容**：
- 项目目录结构导读（`scratchagent/` 包、`notebooks/ch02~ch10`、`tests/`、`examples/`）。
- 运行方式：`uv sync` → `cp .env.example .env` → `uv run jupyter lab`。
- 首个最小示例：创建 `Agent`、注册工具、`await agent.run(...)`。
- 公开 API 9 个核心符号：`Agent`、`LlmClient`、`Message`、`ExecutionContext`、`AgentResult`、`LoopWorkFlow`、`SequentialWorkFlow`、`ParallelWorkFlow`、`SkillInfo`。
- 全书章节脉络总览：LLM API → Tool → ReAct → RAG → Memory → Planning → Code Exec → Multi-Agent → Evaluation。

**本章对应的项目证据**：`README.md`、`technical-architecture.md` §4 架构分层、§16.2 Notebook 学习路径。

**动手实验**：跑通 `examples/basic_agent.py`，观察 `AgentResult` 中的 `output` 与 `context.events`。

---

### 阶段 1：地基——LLM 调用与环境工程化（第 2～3 章）

---

#### 第 2 章：大模型 LLM API 调用与 LiteLLM 封装

**核心问题**：Agent 的"大脑"如何接入？如何屏蔽不同模型厂商的差异？

**教学目标**：
1. 掌握 OpenAI、Anthropic、Gemini 的基础 API 调用方式。
2. 理解 LLM API 的**无状态**特征，以及结构化输出、异步调用、并发限流。
3. 学会用 LiteLLM 把不同 provider 封装成统一的 OpenAI-compatible 格式。

**核心内容**：
- 直接调用 OpenAI Chat Completions API 的完整流程（请求 → 响应 → usage）。
- 内部统一协议对象：`LlmRequest`（instructions/contents/tools/tool_choice/model_id）与 `LlmResponse`（content/error_message/usage_metadata）。
- LiteLLM 的 `acompletion()`：一条代码切换不同 model 字符串（`openai/...`、`anthropic/...`、`gemini/...`）。
- Provider 中立性的**边界**：工具 schema 是 OpenAI-compatible、embedding/token 计数默认偏 OpenAI——这是诚实认知，而非"完全无关"。
- 多模态消息格式的转换。

**动手实验**：分别用原生 OpenAI SDK 和 LiteLLM 调用同一模型，对比代码量；尝试切换到本地模型端点。

---

#### 第 3 章：项目脚手架与 Python 工程规范

**核心问题**：一个"能上生产、能教学、经得起审计"的 Python 项目怎么搭？

**教学目标**：
1. 掌握 `uv` 初始化项目、锁定 Python 版本、管理依赖。
2. 掌握 Python 3.13 注解类开发规范（PEP 585/604/695）。
3. 理解包管理、发布规范与 `__all__` 导出边界。

**核心内容**：
- `uv init` → `uv python pin 3.13` → `uv add` → `uv sync --extra dev` 完整流程。
- PEP 585（`list[str]` 替代 `List[str]`）、PEP 604（`str | None` 替代 `Optional[str]`）、PEP 695（`type` 别名）。
- `from __future__ import annotations` 延迟注解解析的作用。
- `TYPE_CHECKING` 延迟导入：何时用、为什么用（规避循环依赖 + 减少运行时依赖）。
- `pyproject.toml` 关键字段：`[project]`、`requires-python`、`[tool.mypy]`、`[tool.pytest.ini_options]`。
- 包导出规范：顶层 `__all__` 29 符号零缺失，`from scratchagent import *` 与 `__all__` 一致。


**动手实验**：从零用 `uv` 搭建一个空包，配置 mypy + pytest + black + isort，跑通 `poe check`。

---

### 阶段 2：核心机制——消息、上下文、工具、ReAct（第 4～8 章）

---

#### 第 4 章：核心消息类型（Message / ToolCall / ToolResult / Event）

**核心问题**：Agent 内部如何表示"一段对话 + 一次工具交互"？

**教学目标**：
1. 理解四种核心类型的语义与职责。
2. 理解 `ContentItem` 联合类型如何让一个 Event 承载文本、工具请求、工具结果。

**核心内容**：
- `Message`：`role`（system/user/assistant）+ `content`，普通文本消息。
- `ToolCall`：`tool_call_id` + `name` + `arguments`（JSON 字符串），模型请求执行工具。
- `ToolResult`：`tool_call_id` + `name` + `status`（success/error）+ `content`（list）。
- `Event`：`id` + `execution_id` + `timestamp` + `author` + `content`，执行历史的最小单元。
- **关键设计**：`tool_call_id` 是 ToolCall 与 ToolResult 配对的唯一依据（同名工具多次调用必须靠 ID 区分）。


**动手实验**：手工构造一条"用户问 → ToolCall → ToolResult → 最终回答"的 Event 序列，体会事件流的形状。

---

#### 第 5 章：上下文管理对象（ExecutionContext）

**核心问题**：一次 Agent 执行的所有状态存在哪里？

**教学目标**：
1. 理解 `ExecutionContext` 作为"执行期中央状态容器"的角色。
2. 理解 `events` 为何是项目最重要的"数据总线"。

**核心内容**：
- `ExecutionContext` 字段：`execution_id`、`events`、`current_step`、`state`、`final_result`、`session`、`session_manager`、`memory_manager`、`code_env`、`transfer_to`、`transfer_tools`。
- `events` 的三重身份：运行日志 + 对话上下文 + 工具调用轨迹 + 下一轮请求数据源。
- `AgentResult`：`output` + `context` + `status`，返回的不只是答案，还有"如何得到答案"的完整轨迹。
- `current_step` 与 `max_steps` 的关系（防死循环安全阀）。

**动手实验**：打印一次 `run()` 后的 `context.events`，统计 user/agent 事件的交替规律。

---

#### 第 6 章：内部消息到 OpenAI-compatible 消息格式的转换

**核心问题**：框架内部的"统一协议"如何翻译成具体模型 API 能读的格式？

**教学目标**：
1. 理解 `build_messages()` 的转换规则。
2. 认识转换过程中的**信息损失**及其影响。

**核心内容**：
- 转换对照表：

| 内部类型 | API 消息形式 |
|---|---|
| `Message` | `role` + `content` |
| `ToolCall` | assistant message with `tool_calls` |
| `ToolResult` | tool message with `tool_call_id` |

- **信息损失点**（教学重点，正反例）：
  - `ToolResult.name` 和 `status` 不会发给模型；
  - `ToolResult.content` 多个元素时只发第一个；
  - 复杂结构用 `str()` 转文本而非严格 JSON 序列化。
  - `build_messages()` 在 `TYPE_CHECKING` 下的导入问题（曾导致循环依赖，已修复）。

**动手实验**：构造含嵌套结构的工具结果，观察它被 `str()` 转成文本后的样子，讨论"模型能读懂吗？"。

---

#### 第 7 章：工具的定义、抽象封装（BaseTool / FunctionTool / @tool）

**核心问题**：一个普通 Python 函数，如何变成"模型能看懂、Agent 能调用"的工具？

**教学目标**：
1. 理解 `BaseTool` 抽象基类的统一协议。
2. 理解 `FunctionTool` 如何把函数包装成工具（Adapter 模式）。
3. 掌握 `@tool` 装饰器的两种用法。
4. 理解从函数签名自动生成 OpenAI function schema 的过程。

**核心内容**：
- `BaseTool` 协议：`name`、`description`、`tool_definition`、`requires_confirmation`、`execute()`、`__call__()`、`process_llm_request()` 钩子。
- **`__call__` 的魔法**：`await tool_obj(context, **args)` → `BaseTool.__call__` → 动态分派到 `FunctionTool.execute`（多态）。
- `needs_context` 按**参数名** `context` 识别，而非类型。
- 同步/异步函数统一：`inspect.iscoroutine(result)` 判断后 `await`。
- `function_to_input_schema()`：`inspect.signature` + 类型注解 → JSON Schema。
- `@tool` 与 `@tool(...)` 两种写法，装饰后函数名指向 `FunctionTool` 对象而非原函数。
- **Schema 生成的局限**（诚实认知）：`str | None` 回退为 `type: string`、`Literal` 未映射为 enum、默认值未写入 schema。

**动手实验**：给一个带 `Optional`、`Literal` 类型注解的函数生成 schema，观察局限；对比"手写 schema"与"自动生成"的差异。

---

#### 第 8 章：ReAct 智能体 Agent 搭建（课程核心里程碑）

**核心问题**：Agent 的"大脑 + 手脚 + 循环"如何组装成一个会思考-行动-观察的闭环？

**教学目标**：
1. 完整理解 `Agent.run()` → `step()` → `think()` / `act()` 的执行链路。
2. 理解"结构化 ReAct"如何用 `Message/ToolCall/ToolResult` 替代脆弱的文本解析。
3. 理解最终响应的判断与提取逻辑。
4. **里程碑：能独立写出一个带工具的 ReAct Agent。**

**核心内容**：
- 核心方法职责表：

| 方法 | 责任 |
|---|---|
| `__init__()` | 配置模型、工具、指令、输出类型 |
| `run()` | 管理整个执行生命周期 |
| `step()` | 完成一次 Think-Act 周期 |
| `think()` | 调用 LLM（薄封装，未来扩展点） |
| `act()` | 执行模型请求的工具 |
| `_prepare_llm_request()` | 把执行历史展平成下一次请求 |
| `_is_final_response()` | 判断是否完成 |
| `_extract_final_result()` | 提取普通或结构化答案 |
| `_setup_tools()` | 注册工具 + 动态创建 `final_answer` |

- 执行链路（伪代码）：

```
run()
  while not final_result and current_step < max_steps:
      step()
        -> _prepare_llm_request()   # 展平 events
        -> think()                  # LlmClient.generate
        -> 记录 assistant Event
        -> 如有 ToolCall: act()     # 查工具 -> 执行 -> ToolResult
        -> current_step += 1
```

- **ReAct 概念映射**：

| ReAct 概念 | 项目表示 |
|---|---|
| Thought / Reasoning | 模型生成下一步决策 |
| Action | `ToolCall` |
| Observation | `ToolResult` |
| Final Answer | assistant `Message` |
| Scratchpad / Trajectory | `ExecutionContext.events` |
| Loop Controller | `Agent.run()` |
| One ReAct iteration | `Agent.step()` |

- **工具错误是可恢复事件而非崩溃**：工具不存在、参数 JSON 解析失败、除零等，都转成 `ToolResult(status="error")` 回灌给模型，让模型自我修正。
- **当前实现的已知局限**（正反例，教学价值极高）：
  - `step()` 忽略 `LlmResponse.error_message`，LLM 失败可能被静默重试至 max_steps；
  - 达到 max_steps 后 `status` 仍是 `complete`，无法区分正常完成与无结果退出；
  - token usage 未写入 context；
  - 同一轮多个 ToolCall 串行执行。

**动手实验**：实现 `calculator` + `search_web` 两个工具的 Agent，运行"最新百米冠军速度 → 跑到月球要多久"的经典案例，逐步跟踪事件时间线。

---

### 阶段 3：结构化输出与外部生态（第 9～10 章）

---

#### 第 9 章：结构化输出（Structured Output）

**核心问题**：如何让 Agent 的输出是"机器可读的、经过校验的"，而非一段自由文本？

**教学目标**：
1. 理解"把提交最终答案也建模成一个工具（`final_answer`）"的巧妙设计。
2. 理解 Pydantic 校验驱动的自我修复循环。

**核心内容**：
- `Agent(output_type=SomePydanticModel)` 触发结构化模式。
- 从 Pydantic 模型 `model_json_schema()` 生成 schema，动态创建 `final_answer` 工具。
- `tool_choice="required"` 的含义（必须调用工具，但不限定是 `final_answer`）。
- 自我修复循环：

```
模型调用 final_answer
  -> Pydantic 校验
     成功 -> 结束
     失败 -> ToolResult(error) -> 模型读错误修正 -> 再次调用
```

- **局限**：`output_schema.pop("$defs")` 对嵌套模型的引用可能失效；该实现不等价于所有 provider 的原生 structured output。

**动手实验**：定义 `SentimentAnalysis(BaseModel)`，用 Agent 对一段文本做结构化情感分析，故意触发一次校验失败观察修复循环。

---

#### 第 10 章：外部工具接入与 MCP（Model Context Protocol）

**核心问题**：Agent 的能力如何突破"框架内置工具"，接入广阔的外部工具生态？

**教学目标**：
1. 理解 MCP 协议解决的核心问题（工具调用的标准化）。
2. 掌握 FastMCP HTTP 工具的加载流程。
3. 了解 FastMCP 这一更高级的封装，以及远程 MCP 的接入方式。

**核心内容**：
- MCP 协议背景：为什么需要统一的工具连接标准。
- `load_mcp_tools()` 流程：从 FastMCP HTTP 服务器拉取工具 → 包装为 `FunctionTool`（详见 `tools/_fast_mcp.py`）。
- MCP tool 与普通 FunctionTool 的统一：都遵循 `BaseTool` 接口。
- FastMCP 替代 mcp：接口更高级（`@mcp.tool` 装饰器、`mcp.run(transport="http")`）。
- 远程 MCP：FastMCP 服务通过 HTTP 暴露，Agent 通过 `load_mcp_tools()` 接入远程工具。
- **安全边界**：MCP 工具权限边界取决于 server 实现，接入前需评估其数据访问范围。


**动手实验**：用 FastMCP 写一个本地工具服务，再让 Agent 通过 `load_mcp_tools()` 接入并调用它。

---

### 阶段 4：知识与记忆（第 11～15 章）

---

#### 第 11 章：RAG 基础——切分、Embedding 与向量检索

**核心问题**：Agent 如何利用"外部知识"而非只靠模型参数内的知识？

**教学目标**：
1. 理解 RAG 的核心思想：切块 → embedding → 相似度检索 → 增强上下文。
2. 掌握 `fixed_length_chunking`、`get_embeddings`、`vector_search` 三个基础函数。
3. 理解余弦相似度与 top-k 检索。

**核心内容**：
- `get_embeddings()`：调用 embedding 模型把文本转成高维向量（语义表示）。
- `fixed_length_chunking(text, chunk_size, overlap)`：固定长度切块 + 重叠避免语义切断；**边界风险**（`overlap >= chunk_size` 导致死循环）。
- `vector_search(query, chunks, embeddings, top_k)`：`cosine_similarity` + `argsort` 取 top-k。
- 本项目 RAG 是"教学型一次性内存过滤"，无持久化向量库。

**动手实验**：对一段长文本做切块 → embedding → 检索，观察 top-k 结果与查询的语义相关性。

---

#### 第 12 章：Callback、搜索压缩与人工审批（Human-in-the-loop）

**核心问题**：Agent 的"动作"如何被拦截、改写、审批？这既是性能优化也是安全机制。

**教学目标**：
1. 理解 `before_llm_callback`、`before_tool_callback`、`after_tool_callback` 三类回调的机制。
2. 理解 before 回调是"守卫链"、after 回调是"结果处理管道"的本质区别。
3. 掌握 `search_compressor`（RAG 压缩搜索结果）和 `approval_callback`（人工审批）。

**核心内容**：
- 三类回调的执行时机与返回值协议：

| 回调 | 时机 | `None` 含义 | 非 `None` 含义 |
|---|---|---|---|
| `before_llm_callback` | LLM 调用前 | 不拦截 | 可修改/替换请求 |
| `before_tool_callback` | 工具执行前 | 允许执行 | 拦截，作为错误结果返回 |
| `after_tool_callback` | 工具执行后 | 保留原结果 | 替换 `ToolResult` |

- **before 回调 = 短路检查链**：任一回调返回非 None 即拦截，停止后续。
- **after 回调 = 串联转换管道**：每次非空返回都替换 `tool_result`，逐个传递。
- 同步/异步回调统一兼容（`inspect.isawaitable`）。
- `search_compressor`：用 RAG 把长搜索结果压到 top-3 相关块，降低 token 成本。
- `approval_callback`：危险工具（delete_file、send_email 等）执行前请求用户确认。
- **正反例教训**：参数顺序不一致（`context` vs `tool_call`）、`arguments` 是 JSON 字符串需 `json.loads` 等真实 bug 的排查过程。

**动手实验**：给 Agent 同时注册 `before_tool_callback=[approval_callback]` 和 `after_tool_callback=[search_compressor]`，跑一次长搜索任务，观察审批与压缩的协同。

---

#### 第 13 章：Session Memory 与多轮会话持久化

**核心问题**：Agent 如何跨多次 `run()` 记住对话？Session 与 ExecutionContext 有何区别？

**教学目标**：
1. 理解 `Session`、`BaseSessionManager`、`InMemorySessionManager` 三层设计。
2. 理解 Session（跨 run 持久化）与 ExecutionContext（单次 run 临时）的本质区别。
3. 理解"保存时只存 events、不存 state"这一缺陷的影响。

**核心内容**：
- `Session`：`session_id` + `user_id` + `events` + `state` + 时间戳。
- `BaseSessionManager` 抽象接口：`create` / `get` / `save` / `get_or_create`。
- `InMemorySessionManager`：字典实现，进程重启即丢失，仅适合开发/教学。
- Agent 中的会话流转：

```
session_id -> get_or_create -> 恢复 Session.events -> 构造 ExecutionContext
  -> 执行追加事件 -> 保存回 Session
```

- **关键缺陷分析**（正反例）：`pending_tool_calls` 存在 `context.state` 而非 `session.state`，导致仅凭 `session_id` 无法恢复人工确认流程；`user_id` 未传入；`updated_at` 未更新。


**动手实验**：同一 `session_id` 连续两次 `run()`，验证第二次能记住第一次的对话内容。

---

#### 第 14 章：长期记忆、去重与 Memory Injection

**核心问题**：如何让 Agent 复用"过去任务的经验"，而非只依赖当前 session？

**教学目标**：
1. 理解长期记忆的完整链路：执行历史 → LLM 抽取 `TaskMemory` → embedding → 去重 → ChromaDB 存储 → 检索注入。
2. 理解"显式工具 vs 隐式 request processor"的区别（`MemoryTool` 是隐式的）。

**核心内容**：
- 长期记忆链路：

```
执行历史 -> LLM 提取 TaskMemory -> embedding / 查重 -> ChromaDB 存储
  -> 后续 MemoryTool 检索 -> 注入 prompt
```

- `MemoryTool` 的"隐式工具"特征：不暴露给模型，通过 `process_llm_request()` 修改请求，把 `<PAST_EXPERIENCES>` 注入指令。
- 去重策略：向量相似度查重，避免重复存储等价经验。
- **治理局限**（诚实认知）：缺少用户隔离、项目隔离、记忆生命周期、删除、隐私过滤。

**动手实验**：让 Agent 完成两次相似任务，观察第二次是否通过长期记忆复用了第一次的经验。

---

#### 第 15 章：上下文优化管理——窗口滑动、压缩与摘要

**核心问题**：当对话历史 + 工具结果 + 工具定义让请求 Token 爆炸时，如何优雅地裁剪？

**教学目标**：
1. 理解 token 统计、滑动窗口、内容压缩、历史摘要四种策略。
2. 理解 `ContextOptimizer` 的"分层优化"思想：先做便宜的确定性压缩，仍不够再调用 LLM 语义摘要。
3. 理解 `create_optimizer_callback`（函数工厂）与 `ContextOptimizer`（可调用对象）的关系与差异。

**核心内容**：
- 三种策略：

| 策略 | 机制 | 代价 |
|---|---|---|
| 滑动窗口 | 删除较旧执行记录 | 可能拆散 ToolCall/ToolResult 配对 |
| 内容压缩 | 把冗长工具参数/结果替换为简短引用 | 有损，需重读文件 |
| 历史摘要 | 调用 LLM 总结旧历史 | 额外 LLM 调用 |

- `count_tokens()`：用 `tiktoken` 近似统计（对非 OpenAI 模型只是近似）。
- `ContextOptimizer.__call__` 分层流程：超阈值 → 先 compaction → 仍超 → 再 summarization。
- **真实 bug 与修复**（教学价值极高）：
  - `create_optimizer_callback` 缺少 `return callback`，导致拿到 `None`；
  - `last_summary_idx` 用易变的列表索引表示不可变的历史语义，导致重复摘要、摘要边界失真；
  - **修复方案演进**：整数索引 → 稳定消息 ID → 显式 `SummaryMessage` 节点（把摘要作为 contents 中的一等对象，边界随节点移动）。


**动手实验**：构造一个超长对话，观察 `ContextOptimizer` 先压缩、后摘要的完整过程；实现一个最小版的"显式摘要节点"。

---

### 阶段 5：高级能力——规划、沙箱、技能（第 16～18 章）

---

#### 第 16 章：规划与反思模式（Planning & Reflection）

**核心问题**：Agent 面对复杂任务时，如何显式拆解、跟踪进度、复盘纠错？

**教学目标**：
1. 理解 `create_tasks()` 与 `reflection()` 两个规划工具的职责。
2. 理解"规划/反思也是工具"的统一设计哲学。

**核心内容**：
- `create_tasks()`：让 Agent 显式创建任务计划（Task 模型）。
- `reflection()`：让 Agent 对当前进展反思、自检、决定是否重规划。
- 与 ReAct 的差异：ReAct 是隐式的一步一决策，规划是显式的任务分解。
- 典型应用：plan-review-revise 类工作流（为第 19 章的 LoopWorkflow 铺垫）。


**动手实验**：让 Agent 用 `create_tasks` 拆解一个多步骤任务，观察它如何跟踪子任务完成度。

---

#### 第 17 章：E2B 代码执行沙箱

**核心问题**：Agent 生成了"不可信代码"，如何安全地执行它？

**教学目标**：
1. 理解为什么 LLM 生成的代码不能直接在宿主机执行（代码注入、rm -rf、挖矿、容器逃逸）。
2. 理解 E2B 的 Firecracker Micro-VM 隔离原理（每个沙箱独立内核，非 Docker 共享内核）。
3. 掌握 E2B 沙箱的生命周期与代码执行流程。
4. 理解自定义模板（Template）解决依赖预装问题。

**核心内容**：
- E2B 定位：给每个 Agent 分配一台临时隔离的微型云电脑。
- 隔离对比：Docker（共享内核，隔离弱）vs Firecracker Micro-VM（独立内核，强隔离，80-200ms 启动）。
- 代码执行流程：

```
Agent.run() -> _setup_code_env() -> Sandbox.create()
  -> LLM 调用 execute_python / bash_tool -> 沙箱内执行 -> finally 阶段 kill sandbox
```

- **自定义模板**：`Template().from_template("code-interpreter-v1").pip_install("pypdf==5.6.1")` → 发布为专用模板，运行阶段保持沙箱无网络。
- **真实案例复盘**（教学价值极高）：`pdf-merge` skill 因沙箱缺 `pypdf` 失败 → 构建自定义模板解决 → 成功合并 58 页 PDF。
- 安全边界：网络权限、文件上传下载、资源限额、超时、结果脱敏。

**动手实验**：让 Agent 在 E2B 沙箱内执行一段 pandas 数据分析代码，验证隔离性；尝试构建一个带自定义依赖的模板。

---

#### 第 18 章：Skills 技能系统与沙箱注入

**核心问题**：如何给 Agent "渐进式披露"地加载专业技能（SKILL.md），而非把所有能力一次性塞进 prompt？

**教学目标**：
1. 理解 SKILL.md 的目录约定与 YAML frontmatter 解析。
2. 理解"渐进式披露"（progressive disclosure）的核心思想。
3. 理解 skills 注入 prompt 与复制到沙箱的两种用法。

**核心内容**：
- Skills 目录约定：

```
skills_path/
  some_skill/
    SKILL.md   # YAML frontmatter（name/description）+ 权威指令
```

- `discover_skills()` 递归发现 `SKILL.md`，解析 frontmatter，生成 `SkillInfo`。
- 注入方式：技能说明注入 Agent instructions；启用 E2B 时同步复制到沙箱路径。
- 渐进式披露的价值：模型按需读取技能，而非一次性加载全部，降低 prompt 冗余。
- **与 E2B 的协同**：skill 规定的依赖需在沙箱模板中预装（呼应第 17 章的 pdf-merge 案例）。

**动手实验**：写一个 `SKILL.md`（如"PDF 合并"），让 Agent 发现并读取它，在沙箱中完成任务。

---

### 阶段 6：多智能体与评估（第 19～20 章 + 附录）

---

#### 第 19 章：多智能体工作流编排——Sequential、Parallel、Loop

**核心问题**：单个 Agent 能力有限，如何编排多个 Agent 协作？

**教学目标**：
1. 理解三种工作流模式的语义与适用场景。
2. 理解 `ParallelWorkflow` 共享 context 的并发状态交错风险。

**核心内容**：
- `SequentialWorkflow`：`user_input → agent1 → shared context → agent2 → ... → final result`，适合分阶段处理。
- `ParallelWorkflow`：`asyncio.gather()` 并发运行，组合输出；**风险**：共享 context 导致 events 交错、state 覆盖、final_result 竞争。
- `LoopWorkflow`：多 Agent 循环直到停止条件，适合 plan-review-revise。
- **并发状态隔离问题**（正反例）：教学版共享 context 可展示概念，生产需"分支 context + 确定性合并"。
- 改进方向：`ExecutionContext.clone()`、`merge_contexts()`、独立 `branch_id`。

**动手实验**：用 SequentialWorkflow 串联"研究 → 写作 → 编辑"三个 Agent；用 ParallelWorkflow 并发跑多个独立子任务，观察结果组合。

---

#### 第 20 章：多智能体 Transfer（转交控制权，里程碑）

**核心问题**：Agent 之间如何"动态转交控制权"？

**教学目标**：
1. 理解 `transfer`（handoff）机制：`create_transfer_tool` 动态生成 `transfer_to_agent` 工具转交控制权。
2. 理解 `context.transfer_to` 的转交闭环（设置 → 检测 → 复位 → 递归 run）。
3. 理解 Transfer（模型动态路由）与第 19 章工作流（代码静态调度）的本质区别。

**核心内容**：
- Transfer / Handoff：

```
LLM 调用 transfer_to_agent(agent_name)
  -> context.transfer_to = agent_name
  -> Agent.run 检测转交 -> target.run(context=context)
```

- 源码对应：`orchestration/_transfer.py`（`create_transfer_tool`）+ `agent.py` §transfer。
- 多智能体模式的对比总结：Sequential / Parallel / Loop / Transfer 各自的取舍。

> **进阶方向（本教学项目未实现，供思考）**：`Agent-as-Tool`（把 Agent 包装成工具供另一 Agent 调用）、A2A（Agent-to-Agent 远程通信协议）是成熟框架的常见能力，本项目的 Transfer 是理解它们的最小前置——先掌握"单进程内的动态路由"，再谈"跨进程/跨服务的智能体通信"。

**动手实验**：实现一个"调度 Agent + 专家 Agent"的 handoff 场景，观察 `context.transfer_to` 的转交流程。

---

### 附录（进阶工程化）

---

#### 附录 1：VS Code + Claude Code IDE 插件搭建 Python 项目开发环境

**内容**：VS Code 配置、Claude Code 插件、调试 Python 异步代码、断点观察 `context.events` 的技巧、uv 集成。

---

#### 附录 2：AI 辅助编程与项目代码质量（含 Python 规范审计）

**内容**：
- 如何用 AI 辅助工具做代码审查。
- 本项目的审计轨迹：从 v4（78 分）到 v6（93 分）的演进，mypy 错误从 19 → 3。
- 类型注解的"照妖镜"效应：精确化类型暴露下游潜在问题。
- `cast(Any, ...)` 的正当使用与滥用边界、注释语言统一、`classifiers` 元数据等规范细节。

---

#### 附录 3：智能体可视化跟踪 Web 与 AI Coding 开发

**内容**：基于 `ExecutionContext.events` 做执行轨迹可视化（时序图、工具调用链）、AI Coding 的工程实践、测试方案（`agent-from-scratch_测试方案.md` 的单元/集成/E2E 三层设计，覆盖率门禁）。

---

## 四、课程主线项目：从空目录到完整 agent-from-scratch

> 本节是全课程的**核心骨架**。它不是"附加的综合练习"，而是课程本身——每一章的动手实验都是在推进同一个项目，章节之间严格串行、层层叠加。学员可对照下表，随时确认"我现在写到哪了、下一步加什么"。

### 4.1 项目生长地图（每一章结束时的里程碑）

| 章节 | 本阶段新增的代码 | 项目里程碑（此刻能跑什么） |
|---|---|---|
| 第 1 章 | `uv init` 脚手架、目录结构、`pyproject.toml` | 一个空包，能 `uv run` 起来 |
| 第 2 章 | `llm.py` / `llm/client.py` / `llm/config.py`（`LlmRequest`/`LlmResponse`/`LlmClient`） | 能调用一次 LLM 拿到回复 |
| 第 3 章 | 类型注解规范、`__all__`、mypy/pytest 配置 | 规范、可通过审计的包骨架 |
| 第 4 章 | `types.py`（`Message`/`ToolCall`/`ToolResult`/`Event`） | 能构造一段事件流 |
| 第 5 章 | `context.py`（`ExecutionContext`/`AgentResult`） | 有"执行期状态容器" |
| 第 6 章 | `build_messages()` 消息转换 | 内部协议 → 模型 API 格式 |
| 第 7 章 | `tools/base.py`、`tools/helpers.py`（`BaseTool`/`FunctionTool`/`@tool`） | 能把普通函数变成工具 |
| 第 8 章 | `agent.py`（`Agent.run/step/think/act`） | **★ 第一个完整 ReAct Agent** |
| 第 9 章 | 结构化输出（`output_type` + `final_answer`） | Agent 能返回校验过的结构化结果 |
| 第 10 章 | `tools/mcp.py`、`tools/fast_mcp.py` | 能接入外部 MCP 工具 |
| 第 11 章 | `rag.py`（切分/embedding/检索） | 能用外部知识增强回答 |
| 第 12 章 | `callbacks.py`（三类回调 + 审批 + 压缩） | 能拦截/审批/压缩 Agent 动作 |
| 第 13 章 | `memory/session.py`（`Session`/SessionManager） | 能跨 `run()` 记住对话 |
| 第 14 章 | `memory/long_term.py`、`tools/memory_tool.py` | 能复用过去任务经验 |
| 第 15 章 | `memory/context_optimizer.py` | 能裁剪/压缩/摘要超长上下文 |
| 第 16 章 | `orchestration/_planning_reflection.py`（`create_tasks`/`reflection`） | 能显式规划与反思 |
| 第 17 章 | `tools/code_execution.py`（E2B 沙箱） | 能安全执行不可信代码 |
| 第 18 章 | `skills.py`（SKILL.md 发现与注入） | 能渐进式加载专业技能 |
| 第 19 章 | `workflows/`（Sequential/Parallel/Loop） | 能编排多个 Agent 协作 |
| 第 20 章 | `orchestration/_transfer.py`、`tools/_base.py`（Agent-as-Tool） | **★ 完整多智能体 + A2A 系统** |

> **读法**：第 8 章和第 20 章是两个"验收点"。第 8 章结束时，学员已经拥有一个单智能体的最小可用框架；第 20 章结束时，学员拥有的是一套支持多智能体、A2A、沙箱、记忆、技能的全功能框架——两者之间不是两个项目，而是同一个项目长到了不同阶段。

### 4.2 每章的动手实验如何"接入主线"

- **每个动手实验都是"给项目加一块新代码"**，而不是"写一个一次性脚本"。实验产出的 `.py` 文件直接成为项目源码的一部分，下一章在此基础上继续。
- **每章开头先运行上一章的版本**，确认"上一章能跑"，再动手加新能力。这既是回归测试，也是"生长感"的来源。
- **参考答案即参考项目本身**：`scratchagent/` 是学员"最终应该写出的成品"的对照，但教学顺序刻意打乱为"先写最小内核、再逐层叠加"，避免"一次性看到完整代码失去探索感"。

### 4.3 贯穿全课程的验收标准

课程结束时，学员需要满足以下**可验证**标准（不是"理解了"这种主观表述）：

1. 从空目录出发，独立写出 `scratchagent/` 包的全部核心模块，`uv run` 后能跑通 `examples/` 下的完整示例。
2. 自己写的项目通过一次代码审计：`mypy` 错误数 ≤ 5、`pytest` 覆盖率达标、`__all__` 符号零缺失。
3. 能向他人讲清楚 ReAct 循环的执行链路，以及每一层能力是在哪一步、为什么这样叠加的。

---

## 五、考核与评价建议

| 考核项 | 权重 | 说明 |
|---|---|---|
| 全程项目（主线） | 50% | **从头到尾自己搭出来的 `agent-from-scratch`**：完整性（20 章能力是否齐备）、可运行性、代码质量。这是本课程的重心。 |
| 阶段里程碑检查 | 20% | 每个验收点（尤其第 8 章、第 20 章）的版本是否能在上一版基础上正确生长，而非"推倒重写"。 |
| 源码精读答辩 | 20% | 随机抽取自己写出的核心方法，讲解其职责与调用链（证明是真懂，不是照抄）。 |
| 规范审计 | 10% | 对自己写出的项目做一次 mypy/pytest/black 审计并产出报告。 |

---

> **一句话总结**：本课程把大模型当作"动作决策器"，把 Python 函数当作"可执行能力"，把 Event/ExecutionContext 当作"过程记忆"，由 Agent 反复组织三者，直到模型基于工具返回的数据形成最终答案——并在此过程中，同步掌握一套经得起审计的 Python 工程规范。**贯穿全程的唯一目标，是让学员从空目录出发，亲手搭出一个完整、可运行、可继续扩展的 `agent-from-scratch` 项目；机制讲解与规范训练，都是这条主线上"写这一行代码"所必需的知识点。**
