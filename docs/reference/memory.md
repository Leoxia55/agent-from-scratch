# Memory 参考

导入：`from scratchagent.memory import ...`

## Session

`Session(session_id, user_id=None, events=[], state={}, created_at=..., updated_at=...)` 是 Pydantic 模型。`BaseSessionManager` 定义：

```python
async create(session_id: str, user_id: str | None = None) -> Session
async get(session_id: str) -> Session | None
async save(session: Session) -> None
```

`get_or_create(session_id, user_id=None)` 已在基类提供。`InMemorySessionManager` 的 `create` 在重复 ID 时抛出 `ValueError`。

## 长期任务记忆

`TaskMemory(task_summary, approach, final_answer, is_correct, error_analysis=None)` 提供 `to_embedding_text()`。`TaskMemoryManager(llm_client, collection_name="task_memories")` 暴露：

```python
await manager.save(context) -> str | None
await manager.search(query, top_k=5) -> list[TaskMemory]
```

保存流程依赖 LLM 提炼、Chroma 查询和 duplicate check；失败或判重时可能返回 `None`。

## Context optimizer

导出 `count_tokens`、`apply_compaction`、`apply_sliding_window`、`apply_summarization`、`create_optimizer_callback` 和 `ContextOptimizer`。默认优化器阈值为 50,000 tokens，摘要保留最近 5 步。
