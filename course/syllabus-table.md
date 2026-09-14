# 《从零构建 AI Agent》课程大纲（表格版）

> **课程定位**：学完本课程，学员能够亲手搭建出一个完整可运行的 `agent-from-scratch` 项目——逐章生长、经得起审计的真实工程（约 3700 行）。
>
> **前置要求**：Python 3.13+ 基础、PEP 585/604 类型注解、`async/await`、Pydantic 基础、`uv` 包管理。
>
> **总课时**：建议 40～48 学时（正课第 0~20 章共 21 章 + 3 个附录），每章约 2 学时。

---

## 主线大纲

| 阶段     | 主题                                                | 核心内容                                                                | 学习目标 / 预期效果                                                                                                                                                                                                                         |
| ------ | ------------------------------------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **0**  | 智能体 Agent 及 Agent 开发简介                            | 常见智能体、常见智能体开发平台、自研智能体常识                                             | 1. 了解 LLM、会用现有 AI Agent 做日常工作；<br>2. 了解 Agent SDK、并能简单 API 调用构建智能体；<br>3. 了解自研智能体 Agent 都需要哪些基本技术                                                                                                                                   |
| **1**  | agent-from-scratch 项目预览                           | 下载项目、了解项目结构、用 `scratchagent.Agent` 开发简单智能体                          | 克隆项目、跑通 `examples/basic_agent.py`，掌握 9 个核心公开 API（`Agent`/`LlmClient`/`Message`/`ExecutionContext`/`AgentResult`/`LoopWorkFlow`/`SequentialWorkFlow`/`ParallelWorkFlow`/`SkillInfo`），建立"每章能力 → 源码模块"映射                               |
| **2**  | 大模型 LLM API 调用、LiteLLM 封装                         | 本地、及云端大模型 LLM API、LiteLLM 封装成通用 openai 格式                           | 1. 掌握 OpenAI/Anthropic/Gemini 基础调用；<br>2. 理解内部统一协议对象 `LlmRequest` / `LlmResponse`；<br>3. 用 LiteLLM `acompletion()` 一条代码切换不同 model 字符串；理解 Provider 中立性的边界                                                                            |
| **3**  | 项目脚手架搭建                                           | Python 项目脚手架、UV 开发环境、Python 3.12、3.13 注解类 开发规范、包管理及发布规范             | 1. `uv init` → `uv python pin 3.13` → `uv add` → `uv sync --extra dev` 完整流程；<br>2. PEP 585 / 604 / 695 注解类规范；<br>3. `TYPE_CHECKING` 延迟导入 + `__all__` 导出边界 + `pyproject.toml` 关键字段                                                   |
| **4**  | 核心消息类型                                            | `Message`/`ToolCall`/`ToolResult`/`Event` 四种核心类型，`ContentItem` 联合类型 | 1. 理解四种类型的语义与职责；<br>2. 理解 `tool_call_id` 是 ToolCall 与 ToolResult 配对的唯一依据；<br>3. 手工构造"用户问 → ToolCall → ToolResult → 最终回答"的 Event 序列                                                                                                  |
| **5**  | 上下文管理对象                                           | `ExecutionContext` 执行期中央状态容器 + `AgentResult` 返回结构                   | 1. 理解 `events` 的三重身份（运行日志 + 对话上下文 + 工具调用轨迹 + 下一轮请求数据源）；<br>2. 打印一次 `run()` 后的 `context.events`，统计 user/agent 事件交替规律；<br>3. `current_step` 与 `max_steps` 防死循环安全阀                                                                     |
| **6**  | 内部消息到 OpenAI-compatible 格式转换                      | `build_messages()` 转换规则 + 信息损失分析                                    | 1. 理解 `Message`/`ToolCall`/`ToolResult` → API 消息的对照转换；<br>2. 识别信息损失点（`ToolResult.name`/`status` 不发模型、多个 content 只发第一个、`str()` 序列化问题）；3. 修复 `TYPE_CHECKING` 导致的循环依赖                                                                  |
| **7**  | 工具的定义、抽象封装（`BaseTool` / `FunctionTool` / `@tool`） | 工具抽象基类协议 + 函数签名自动生成 JSON Schema                                     | 1. 掌握 `BaseTool` 协议与 `FunctionTool` 适配器模式；<br>2. 理解 `__call__` 多态分派与 `needs_context` 按参数名识别；<br>3. 认识 Schema 自动生成的局限（`str \| None`、`Literal`、默认值处理）                                                                                 |
| **8**  | ReAct 智能体 Agent 搭建（核心里程碑）                         | `Agent.run/step/think/act` 完整执行链路 + 结构化 ReAct 替代文本解析                | **★里程碑**：能独立写出一个带工具的 ReAct Agent。<br>理解 `_prepare_llm_request()` 展平 events、`think()`/`act()` 分工、<br>ToolCall/ToolResult 配对、`current_step` 终止控制、工具错误→可恢复事件的处理                                                                        |
| **9**  | 结构化输出（Structured Output）                          | `output_type=Pydantic` 触发 + `final_answer` 动态工具 + 校验驱动自我修复          | 1. 理解"提交最终答案也是工具"的设计；<br>2. 掌握 Pydantic 校验失败 → `ToolResult(error)` → 模型自我修正的修复循环；<br>3. 认识 `output_schema.pop("$defs")` 对嵌套模型的可能影响                                                                                                  |
| **10** | 外部工具接入与 MCP（Model Context Protocol）               | FastMCP HTTP 工具加载流程 + 远程 MCP 接入    | 1. 理解 MCP 解决"工具调用标准化"的核心问题；<br>2. 掌握 `load_mcp_tools(connection)` 全流程；<br>3. 用 FastMCP 写本地工具服务，通过 load_mcp_tools() 接入并调用                                                                                                                |
| **11** | RAG 基础——切分、Embedding 与向量检索                        | 固定长度切块 + 余弦相似度 + top-k 检索                                           | 1. 掌握 `fixed_length_chunking` / `get_embeddings` / `vector_search` 三个基础函数；<br>2. 理解重叠避免语义切断的边界风险（`overlap >= chunk_size` 死循环）；<br>3. 对长文本做切块 → embedding → 检索，观察 top-k 语义相关性                                                        |
| **12** | Callback、搜索压缩与人工审批（Human-in-the-loop）             | 三类回调机制 + `search_compressor` + `approval_callback`                  | 1. 区分 before 回调（守卫链）vs after 回调（串联管道）；<br>2. 用 `approval_callback` 拦截危险工具；用 `search_compressor` 压长搜索结果到 top-3；<br>3. 排查参数顺序不一致、`arguments` 需 `json.loads` 等真实 bug                                                                   |
| **13** | Session Memory 与多轮会话持久化                           | `Session` / `BaseSessionManager` / `InMemorySessionManager` 三层设计    | 1. 理解 Session（跨 run 持久化）与 ExecutionContext（单次 run 临时）的本质区别；<br>2. 掌握 `session_id → get_or_create → 恢复 events → 构造 ExecutionContext → 执行 → 保存` 流转；<br>3. 分析"仅存 events 不存 state"的缺陷影响                                                 |
| **14** | 长期记忆、去重与 Memory Injection                         | 执行历史 → LLM 抽取 `TaskMemory` → embedding → 去重 → ChromaDB → 检索注入       | 1. 理解长期记忆完整链路；<br>2. 理解 `MemoryTool` 是"隐式工具"（通过 `process_llm_request()` 注入 `<PAST_EXPERIENCES>`）；<br>3. 用向量相似度查重；认识治理局限（用户隔离、生命周期、删除、隐私过滤缺失）                                                                                        |
| **15** | 上下文优化管理——窗口滑动、压缩与摘要                               | 滑动窗口 + 内容压缩 + 历史摘要 + `ContextOptimizer` 分层优化                        | 1. 掌握三种策略的机制与代价；<br>2. 理解 `ContextOptimizer.__call__` 分层流程（超阈值→先 compaction→仍超→再 summarization）；<br>3. 排查真实 bug（缺少 `return`、`last_summary_idx` 易变）并演进修复（索引→稳定 ID→`SummaryMessage` 节点）                                               |
| **16** | 规划与反思模式（Planning & Reflection）                    | `create_tasks()` 显式拆解 + `reflection()` 自检复盘                         | 1. 理解规划/反思也是工具的统一设计哲学；<br>2. 区分 ReAct（隐式一步一决策）vs 规划（显式任务分解）；<br>3. 跑多步骤任务，观察子任务完成度跟踪；                                                                                                                                               |
| **17** | E2B 代码执行沙箱                                        | Firecracker Micro-VM 隔离 + 自定义 Template 解决依赖预装 + 沙箱生命周期              | 1. 理解为何 LLM 代码不能宿主机直接执行（注入、`rm -rf`、挖矿、容器逃逸）；<br>2. 对比 Docker（共享内核）vs Firecracker（独立内核，80-200ms 启动）；<br>3. 用自定义模板解决 `pdf-merge` 缺 `pypdf` 类问题，构建无网络沙箱运行模板                                                                           |
| **18** | Skills 技能系统与沙箱注入                                  | SKILL.md 目录约定 + YAML frontmatter + 渐进式披露（progressive disclosure）    | 1. 理解 SKILL.md 结构和 `discover_skills()` 递归发现；<br>2. 掌握技能注入 instructions + 启用 E2B 时同步复制到沙箱路径；<br>3. 写"PDF 合并" SKILL.md，让 Agent 在沙箱中完成依赖类任务                                                                                            |
| **19** | 多智能体工作流编排——Sequential、Parallel、Loop               | 三种工作流模式 + `ParallelWorkflow` 共享 context 的并发状态交错风险                   | 1. 理解 `SequentialWorkflow`（分阶段）/ `ParallelWorkflow`（`asyncio.gather()`）/ `LoopWorkflow`（plan-review-revise）适用场景；<br>2. 识别并发状态隔离问题（events 交错、state 覆盖、`final_result` 竞争）；<br>3. 改进方向：`clone()` + `merge_contexts()` + 独立 `branch_id` |
| **20** | 多智能体 Transfer（动态转交控制权）                            | handoff 转交控制权 + `context.transfer_to` 转交闭环             | **★第二个验收点**：能编排多智能体、实现动态 Transfer 转交。<br>理解 `transfer_to_agent` → `context.transfer_to` → `target.run(context=context)` 的 handoff 链路；<br>理解 Transfer（模型动态路由）与工作流（代码静态调度）的本质区别                                                      |

---

## 项目生长地图（每章里程碑）

| 章节     | 本阶段新增的代码                                                                             | 项目里程碑（此刻能跑什么）           |
| ------ | ------------------------------------------------------------------------------------ | ----------------------- |
| 第 1 章  | `uv init` 脚手架、目录结构、`pyproject.toml`                                                  | 一个空包，能 `uv run` 起来      |
| 第 2 章  | `llm.py` / `llm/client.py` / `llm/config.py`（`LlmRequest`/`LlmResponse`/`LlmClient`） | 能调用一次 LLM 拿到回复          |
| 第 3 章  | 类型注解规范、`__all__`、mypy/pytest 配置                                                      | 规范、可通过审计的包骨架            |
| 第 4 章  | `types.py`（`Message`/`ToolCall`/`ToolResult`/`Event`）                                | 能构造一段事件流                |
| 第 5 章  | `context.py`（`ExecutionContext`/`AgentResult`）                                       | 有"执行期状态容器"              |
| 第 6 章  | `build_messages()` 消息转换                                                              | 内部协议 → 模型 API 格式        |
| 第 7 章  | `tools/base.py`、`tools/helpers.py`（`BaseTool`/`FunctionTool`/`@tool`）                | 能把普通函数变成工具              |
| 第 8 章  | `agent.py`（`Agent.run/step/think/act`）                                               | **★ 第一个完整 ReAct Agent** |
| 第 9 章  | 结构化输出（`output_type` + `final_answer`）                                                | Agent 能返回校验过的结构化结果      |
| 第 10 章 | `tools/mcp.py`、`tools/fast_mcp.py`                                                   | 能接入外部 MCP 工具            |
| 第 11 章 | `rag.py`（切分/embedding/检索）                                                            | 能用外部知识增强回答              |
| 第 12 章 | `callbacks.py`（三类回调 + 审批 + 压缩）                                                       | 能拦截/审批/压缩 Agent 动作      |
| 第 13 章 | `memory/session.py`（`Session`/SessionManager）                                        | 能跨 `run()` 记住对话         |
| 第 14 章 | `memory/long_term.py`、`tools/memory_tool.py`                                         | 能复用过去任务经验               |
| 第 15 章 | `memory/context_optimizer.py`                                                        | 能裁剪/压缩/摘要超长上下文          |
| 第 16 章 | `orchestration/_planning_reflection.py`（`create_tasks`/`reflection`）                                           | 能显式规划与反思                |
| 第 17 章 | `tools/code_execution.py`（E2B 沙箱）                                                    | 能安全执行不可信代码              |
| 第 18 章 | `skills.py`（SKILL.md 发现与注入）                                                          | 能渐进式加载专业技能              |
| 第 19 章 | `workflows/`（Sequential/Parallel/Loop）                                               | 能编排多个 Agent 协作          |
| 第 20 章 | `orchestration/_transfer.py`（Transfer）                      | **★ 完整多智能体 + 动态 Transfer**   |

---

## 两条并行的知识脉络

| 脉络 | 内容 | 贯穿章节 |
|------|------|----------|
| **A：Agent 机制** | LLM 调用 → 消息协议 → 工具调用 → ReAct → 记忆 → 规划 → 沙箱 → 多智能体 | 第 2 章 → 第 20 章 |
| **B：Python 工程规范** | uv 脚手架 → 类型注解 → 包结构 → 循环导入 → 测试 → 审计 | 第 1、3 章 + 附录 1、2 |

**能力跃迁点**：
- 第 8 章后：能独立写出一个带工具的 ReAct Agent
- 第 15 章后：能理解并实现上下文压缩、记忆注入
- 第 17 章后：能安全地让 Agent 执行代码
- 第 20 章后：能编排多智能体、实现动态 Transfer 转交

---

## 附录（进阶工程化）

| 附录 | 主题 | 核心内容 |
|------|------|----------|
| 附录 1 | VS Code + Claude Code IDE 插件搭建 Python 项目开发环境 | VS Code 配置、Claude Code 插件、调试 Python 异步代码、断点观察 `context.events` 的技巧、uv 集成 |
| 附录 2 | AI 辅助编程与项目代码质量（含 Python 规范审计） | AI 辅助代码审查；本项目审计轨迹（v4=78 分 → v6=93 分，mypy 错误 19 → 3）；`cast(Any, ...)` 正当使用与滥用边界；注释语言统一；`classifiers` 元数据 |
| 附录 3 | 智能体可视化跟踪 Web 与 AI Coding 开发 | 基于 `ExecutionContext.events` 做执行轨迹可视化（时序图、工具调用链）；AI Coding 工程实践；测试方案（单元/集成/E2E 三层 + 覆盖率门禁） |

---

## 考核与评价建议

| 考核项 | 权重 | 说明 |
|--------|------|------|
| 全程项目（主线） | 50% | 从头到尾自己搭出来的 `agent-from-scratch`：完整性（20 章能力是否齐备）、可运行性、代码质量 |
| 阶段里程碑检查 | 20% | 每个验收点（尤其第 8 章、第 20 章）的版本是否能在上一版基础上正确生长，而非"推倒重写" |
| 源码精读答辩 | 20% | 随机抽取自己写出的核心方法，讲解其职责与调用链（证明真懂，非照抄） |
| 规范审计 | 10% | 对自己写出的项目做一次 mypy/pytest/black 审计并产出报告 |

---

## 验收标准（贯穿全课程，可验证）

1. 从空目录出发，独立写出 `scratchagent/` 包的全部核心模块，`uv run` 后能跑通 `examples/` 下的完整示例
2. 自己写的项目通过一次代码审计：`mypy` 错误数 ≤ 5、`pytest` 覆盖率达标、`__all__` 符号零缺失
3. 能向他人讲清楚 ReAct 循环的执行链路，以及每一层能力是在哪一步、为什么这样叠加的
