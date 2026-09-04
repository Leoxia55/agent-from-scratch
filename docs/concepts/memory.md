# 短期与长期记忆

短期记忆是 session 的 `events` 和 `state`：它回答“这段对话刚刚发生了什么”。`Session` 包含 `session_id`、可选 `user_id`、时间戳、事件和状态；`InMemorySessionManager` 用字典保存它们。

长期记忆是 `TaskMemory`：

```text
当前上下文 -> LLM 提炼 task_summary/approach/final_answer
           -> Chroma 相似度检索 + duplicate check
           -> 保存或跳过
新请求     -> MemoryTool.process_llm_request 注入相关记忆
```

长期管理器默认使用 ChromaDB 和 `text-embedding-3-small`。它不是事实数据库：提炼结果可能错误或泄露数据，检索内容应标注来源并经过权限过滤。跨用户使用时必须按租户隔离 collection 或 metadata。

