# ScratchAgent 课程：从零手搓一个 AI 智能体

> 这是一门**系统课程**：第 0~20 章共 21 章 + 3 个附录，每章讲透一个模块，全部基于本仓库真实源码逐行讲解。
> 如果你是第一次接触，建议先看 [`docs/tutorials/`](../docs/tutorials/00-minimal-llm-request.md) 的 6 篇快速上手教程跑通最小路径，再回到本课程系统学习。

## 教学大纲（先看全景）

在逐章学习之前，建议先读一份大纲，建立课程的完整地图：

| 文档 | 说明 | 适合谁 |
|---|---|---|
| [课程大纲（详细版）](syllabus-detailed.md) | 20 章完整大纲：每章的核心问题、教学目标、核心内容、动手实验、源码对应 | 想了解"每章具体讲什么"再做学习/选课决策 |
| [课程大纲（表格版）](syllabus-table.md) | 一页表格速览：阶段、主题、学习目标、项目生长地图、考核方式 | 想快速扫一遍全貌、或老师备课参考 |

> 大纲是"地图"，正文（ch00~ch20）是"实地"——地图告诉你去哪、为什么这么走，正文带你一步步动手写代码。

## 学习方式

每一章的结构是统一的：**核心问题 → 教学目标 → 原理讲解 → 配图 → 源码精读 → 动手实验 → 本章自检**。建议边读边打开对应源码文件，每章的"动手实验"务必亲手运行。

## 课程目录

### 第一部分 · 全景与地基（第 0~3 章）

| 章 | 主题 | 对应源码 |
|---|---|---|
| [第 0 章](ch00-agent-overview.md) | 智能体（Agent）及 Agent 开发全景 | — |
| [第 1 章](ch01-project-preview-and-run.md) | 项目预览与运行 | 整体结构 |
| [第 2 章](ch02-llm-and-provider-abstraction.md) | 大模型 LLM API 调用与 LiteLLM 封装 | `llm/` |
| [第 3 章](ch03-scaffolding-and-engineering-standards.md) | 项目脚手架与 Python 工程规范 | `pyproject.toml` |

### 第二部分 · 核心机制（第 4~9 章）

| 章 | 主题 | 对应源码 |
|---|---|---|
| [第 4 章](ch04-core-message-types.md) | 核心消息类型 | `types.py` |
| [第 5 章](ch05-execution-context.md) | 执行上下文 | `context.py` |
| [第 6 章](ch06-message-conversion.md) | 消息转换 | `context.py` |
| [第 7 章](ch07-tool-abstraction.md) | 工具抽象 | `tools/_base.py` |
| [第 8 章](ch08-react-agent.md) | ReAct Agent（核心里程碑） | `agent.py` |
| [第 9 章](ch09-structured-output.md) | 结构化输出：可校验的 Pydantic 对象 | `agent.py` |

### 第三部分 · 能力扩展（第 10~15 章）

| 章 | 主题 | 对应源码 |
|---|---|---|
| [第 10 章](ch10-mcp-tool-integration.md) | 外部工具接入与 MCP | `tools/_fast_mcp.py` |
| [第 11 章](ch11-rag-basics.md) | RAG 基础：向量检索注入外部知识 | `rag.py` |
| [第 12 章](ch12-callbacks-and-human-approval.md) | 回调与人工审批 | `tools/_callbacks.py` |
| [第 13 章](ch13-session-persistence.md) | 会话持久化 | `memory/_session.py` |
| [第 14 章](ch14-long-term-memory.md) | 长期记忆：跨任务复用经验 | `memory/_long_term.py` |
| [第 15 章](ch15-context-optimization.md) | 上下文优化 | `memory/_context_optimizer.py` |

### 第四部分 · 高级专题（第 16~20 章）

| 章 | 主题 | 对应源码 |
|---|---|---|
| [第 16 章](ch16-planning-and-reflection.md) | 规划与反思 | `orchestration/_planning_reflection.py` |
| [第 17 章](ch17-e2b-sandbox.md) | E2B 沙箱 | `sandbox/_e2b_sandbox.py` |
| [第 18 章](ch18-skills-system.md) | Skills 技能系统 | `skills.py` |
| [第 19 章](ch19-multi-agent-orchestration.md) | 多智能体编排 | `orchestration/` |
| [第 20 章](ch20-transfer-and-multi-agent.md) | Transfer 与多智能体（里程碑） | `orchestration/_transfer.py` |

### 附录

| 附录 | 主题 |
|---|---|
| [附录 1](appendix1-ide-setup.md) | VS Code + Claude Code 开发环境 |
| [附录 2](appendix2-standards-audit.md) | AI 辅助编程与规范审计 |
| [附录 3](appendix3-visualization-and-testing.md) | 可视化跟踪与测试 |

## 配套资源

- **可运行示例**：[`examples/`](../examples/) 20 个示例，覆盖每章的动手实验
- **参考文档**：[`docs/`](../docs/README.md) 概念 / How-to / 参考 三层文档
- **测试**：[`tests/`](../tests/) 单元与集成测试，可对照验证每个机制的行为
