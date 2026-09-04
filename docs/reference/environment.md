# 环境变量参考

项目通过 `python-dotenv` 从最近的 `.env` 加载变量，且不会覆盖已经存在的进程环境变量。

| 变量 | 用途 | 必填条件 |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI-compatible key | `Provider.OPENAI_COMPAT` |
| `OPENAI_BASE_URL` | OpenAI-compatible endpoint | `Provider.OPENAI_COMPAT` |
| `ANTHROPIC_API_KEY` | Anthropic key | `Provider.ANTHROPIC` |
| `ANTHROPIC_BASE_URL` / `ANTHROPIC_API_BASE` | Anthropic endpoint | `Provider.ANTHROPIC` |
| `LLAMA_API_KEY` | llama.cpp key | 可选，默认 dummy-key |
| `LLAMA_BASE_URL` | llama.cpp endpoint | 可选，默认 `http://127.0.0.1:8080/v1` |
| `LM_STUDIO_API_KEY` | LM Studio key | 可选 |
| `LM_STUDIO_API_BASE` / `LM_STUDIO_BASE_URL` | LM Studio endpoint | `Provider.LM_STUDIO` |
| `OPENROUTER_API_KEY` / `OPENROUTER_BASE_URL` | 内置 embedding RAG | 调用 `get_embeddings` |
| `TAVILY_API_KEY` | `search_web` | 调用 Tavily 搜索 |
| `E2B_API_KEY` | E2B 沙箱 | 创建 E2B 环境 |
| `E2B_TEMPLATE_ID` / `E2B_TEMPLATE` | E2B 模板 | 可选 |

凭据只放在环境变量或密钥管理系统中；不要写入工具参数、session 事件、长期 memory 或 Skills。

