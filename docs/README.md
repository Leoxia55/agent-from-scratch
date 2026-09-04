# ScratchAgent 文档

ScratchAgent 是一个用于学习智能体原理和工程边界的 Python 框架。文档按“先跑起来，再理解设计”的顺序组织：

## 学习路径

1. **教程**：从一次最小 LLM 请求开始，逐步加入工具、会话、上下文优化、E2B/Skills 和多智能体。
2. **How-to**：围绕实际任务查找 provider、工具确认、callbacks、RAG、持久化和调试做法。
3. **概念**：理解 agent loop、工具 schema、执行上下文、记忆、上下文压缩、路由和沙箱信任边界。
4. **参考**：按类、函数和环境变量查参数、返回值及错误。

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

- [教程](tutorials/00-minimal-llm-request.md)
- [How-to](how-to/switch-provider.md)
- [概念](concepts/agent-loop.md)
- [参考](reference/agent.md)

## 重要边界

ScratchAgent 的核心 loop、工具调用、状态和工作流由项目源码实现；LiteLLM、Pydantic、ChromaDB、Tavily 与 E2B 只承担基础设施职责。文件工具、E2B 工具、第三方搜索结果和模型输出都应视为不可信输入，生产部署必须增加最小权限、审批、超时、审计和网络隔离。

