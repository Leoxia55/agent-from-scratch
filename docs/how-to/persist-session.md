# 持久化 Session

`Agent` 只依赖 `BaseSessionManager` 的三个异步方法：`create`、`get`、`save`。实现该接口即可接入数据库、Redis 或对象存储。

```python
from scratchagent.memory import BaseSessionManager, Session


class PostgresSessionManager(BaseSessionManager):
    async def create(
        self, session_id: str, user_id: str | None = None
    ) -> Session:
        # INSERT，已存在的 session_id 应抛出 ValueError
        ...

    async def get(self, session_id: str) -> Session | None:
        # SELECT 并还原 events/state
        ...

    async def save(self, session: Session) -> None:
        # UPDATE events/state/updated_at
        ...
```

使用时传入 `session_id`：

```python
agent = Agent(model=client, session_manager=PostgresSessionManager())
result = await agent.run("继续上次任务", session_id="user-42")
```

保存完整事件会持续增长；应配合[上下文压缩](../concepts/context-compression.md)，并在数据库层设置租户隔离、大小限制和加密。`InMemorySessionManager` 可作为协议参考，但不提供持久化。
