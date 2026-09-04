# ExecutionContext

`ExecutionContext` 是一次执行的可变工作区：

| 字段 | 用途 |
| --- | --- |
| `execution_id` | 本次运行标识，默认 UUID |
| `events` | 按时间追加的 `Event` 列表 |
| `current_step` | 已完成的 step 数 |
| `state` | 应用或工具共享的字典状态 |
| `final_result` | 最终文本或 Pydantic 对象 |
| `session` / `session_manager` | 短期会话存取 |
| `memory_manager` | 长期任务记忆和自动 recall |
| `code_env` / `code_env_owned` | E2B 环境及清理责任 |
| `transfer_to` / `transfer_tools` | 多智能体路由信息 |

工具通过 `context` 参数获取它；Agent 会自动注入，不会把它暴露给模型 schema。`add_event()` 和 `increment_step()` 是最小状态操作。

不要在多个并行 Agent 间无锁地修改 `state` 或 `events`。需要跨请求保留的信息放进 session，需要跨任务检索的信息交给长期 memory；不要把 API key 放在 context。

