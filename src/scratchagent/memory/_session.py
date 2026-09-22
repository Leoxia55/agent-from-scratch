"""多轮对话的会话管理。"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ..types import Event


class Session(BaseModel):
    """用于在多次 run () 调用之间保存会话持久状态的容器."""

    session_id: str
    user_id: str | None = None
    events: list[Event] = Field(default_factory=list)
    state: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class BaseSessionManager(ABC):
    """会话管理的抽象基类."""

    @abstractmethod
    async def create(
        self,
        session_id: str,
        user_id: str | None = None,
    ) -> Session:
        """Create a new session."""
        pass

    @abstractmethod
    async def get(self, session_id: str) -> Session | None:
        """根据 ID 获取会话。未找到则返回 None."""
        pass

    @abstractmethod
    async def save(self, session: Session) -> None:
        """将会话更改持久化保存到存储中."""
        pass

    async def get_or_create(
        self,
        session_id: str,
        user_id: str | None = None,
    ) -> Session:
        """获取现有会话或创建新会话."""
        session = await self.get(session_id)
        if session is None:
            session = await self.create(session_id, user_id)
        return session


class InMemorySessionManager(BaseSessionManager):
    """用于开发和测试的内存会话存储。"""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    async def create(
        self,
        session_id: str,
        user_id: str | None = None,
    ) -> Session:
        """创建一个新的Session."""
        if session_id in self._sessions:
            raise ValueError(f"Session {session_id} already exists")

        session = Session(session_id=session_id, user_id=user_id)
        self._sessions[session_id] = session
        return session

    async def get(self, session_id: str) -> Session | None:
        """通过ID检索一个Session."""
        return self._sessions.get(session_id)

    async def save(self, session: Session) -> None:
        """保持Session."""
        session.updated_at = datetime.now()  # 每次更新都需要修改时间
        self._sessions[session.session_id] = session
