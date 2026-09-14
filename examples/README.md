# scratchagent 示例索引

本目录包含 scratchagent 框架的完整示例，每个文件都是可独立运行的脚本。

## 运行前提

1. 在项目根目录 `agent-from-scratch/` 下配置 `.env`（已配置则可跳过）。
2. 使用项目虚拟环境运行：

```bash
cd D:/00_persist/agent-from-scratch
.venv/Scripts/python.exe examples/<文件名>.py
```

> 所有示例默认使用 `Provider.OPENAI_COMPAT` + 模型 `gpt-5.5`，由 `.env` 中的
> `OPENAI_BASE_URL` / `OPENAI_API_KEY` 提供。

## 案例对照表

| 案例文件 | 演示能力 | 依赖外部服务 | 测试验证 |
|---|---|---|---|
| `basic_agent.py` | 最简智能体：工具调用循环 | OpenAI 兼容中转 | Yes |
| `callback_agent.py` | 工具调用前后回调拦截 | OpenAI 兼容中转 | Yes|
| `human_in_loop_agent.py` | 危险工具人工确认（Human-in-the-Loop） | OpenAI 兼容中转 | Yes |
| `approval_callback_agent`| 危险工具人工确认(approval_callback)   | OpenAI 兼容中转 | Yes |
| `planning_reflection_agent.py` | 规划（create_tasks）与反思（reflection） | OpenAI 兼容中转 + Tavily | Yes |
| `session_agent.py` | 多轮会话持久化 | OpenAI 兼容中转 | Yes |
| `memory_agent.py` | 长期记忆存储与检索（ChromaDB） | OpenAI 兼容中转 + OpenRouter(embedding) | Yes |
| `rag_agent.py` | 检索增强生成（RAG） | OpenAI 兼容中转  + Tavily + OpenRouter(embedding) | Yes |
| `discover_skills_agent.py` | 技能发现与注入（SKILL.md） | OpenAI 兼容中转 | Yes |
| `skill_agent.py`| 用PDF合并skill 合并几个pdf 为 一个PDF文件 | OpenAI 兼容中转 + E2B | Yes |
| `e2b_agent.py` | E2B 沙箱执行 Python 代码 | OpenAI 兼容中转 + E2B | Yes |
| `search_compressor_agent.py` | 搜索结果向量化压缩 | OpenAI 兼容中转 + Tavily + OpenRouter(embedding) | Yes |
| `sequential_wf_agent.py` | 多智能体顺序编排 | OpenAI 兼容中转 + Tavily | Yes |
| `parallel_wf_agent.py` | 多智能体并行编排 | OpenAI 兼容中转：测试采用本地LM_Studio 提供的Qwen3.8 27b  | Yes |
| `transfer_to_agent.py` | 多智能体路由转接 | OpenAI 兼容中转：测试采用本地LM_Studio 提供的Qwen3.8 27b  | Yes |
| `workspace_e2b_agent.py` | E2B 沙箱工作区文件管理 | OpenAI 兼容中转 + E2B | Yes |
| `coding_agent.py` | 代码审查，结构化输出（output_type） | OpenAI 兼容中转 | Yes |
| `fast_mcp_agent.py` | 启动本地MCP服务，为Agent 提供mcp_tools | OpenAI 兼容中转 | Yes |

## 环境变量依赖说明

| 环境变量 | 用途 | 相关案例 |
|---|---|---|
| `OPENAI_BASE_URL` / `OPENAI_API_KEY` | LLM 主模型（`niuwa88.vip` 中转） | 全部 |
| `OPENROUTER_BASE_URL` / `OPENROUTER_API_KEY` | embedding 模型（`text-embedding-3-small`）、多模态模型 | memory / rag / search-compressor |
| `TAVILY_API_KEY` | 网络搜索 | planning-reflection / sequential / search-compressor |
| `E2B_API_KEY` | E2B 沙箱 | e2b / workspace-e2b |

> 注意：`OPENAI_BASE_URL=https://niuwa88.vip/v1` 中转平台**不提供 embedding 模型**，
> 涉及向量化的案例（memory / rag / search-compressor）均使用 `OPENROUTER_BASE_URL`
> 的 embedding 能力，框架内部已对此做了处理。

## 辅助目录

- `skills/`：示范技能目录，供 `skill_agent.py` 使用。每个子目录含一个
  `SKILL.md`（YAML frontmatter 需含 `name` 与 `description`）。
