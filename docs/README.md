# ScratchAgent 文档

ScratchAgent 是一个用于学习智能体原理和工程边界的 Python 框架。文档按“先跑起来，再理解设计”的顺序组织：

## 学习路径

1. **快速上手**：从一次最小 LLM 请求开始，逐步加入工具、会话、上下文优化、E2B/Skills 和多智能体。
2. **系统课程**：[`course/`](../course/README.md) 21 章，每章讲透一个模块（原理 → 源码精读 → 动手实验），适合想完整理解智能体底层原理的学习者。
3. **How-to**：围绕实际任务查找 provider、工具确认、callbacks、RAG、持久化和调试做法。
4. **概念**：理解 agent loop、工具 schema、执行上下文、记忆、上下文压缩、路由和沙箱信任边界。
5. **参考**：按类、函数和环境变量查参数、返回值及错误。

## 准备环境

```powershell
uv sync
Copy-Item .env.example .env
```

至少配置一个模型 provider 的凭据。默认示例使用 OpenAI-compatible 接口：

```dotenv
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
```

项目要求 Python `>=3.13,<3.14`。示例均为异步 Python 程序，使用 `asyncio.run(main())` 启动。

## 目录

- [快速上手教程](tutorials/00-minimal-llm-request.md)
- [系统课程（21 章）](../course/README.md)
- [How-to](how-to/switch-provider.md)
- [概念](concepts/agent-loop.md)
- [参考](reference/agent.md)
- [深度解读：agent.py 逐行剖析](deep-dives/agent-py-deep-dive.md)
- [项目评估报告（独立审计快照）](assessment.md)

## 重要边界

ScratchAgent 的核心 loop、工具调用、状态和工作流由项目源码实现；LiteLLM、Pydantic、ChromaDB、Tavily 与 E2B 只承担基础设施职责。文件工具、E2B 工具、第三方搜索结果和模型输出都应视为不可信输入，生产部署必须增加最小权限、审批、超时、审计和网络隔离。

