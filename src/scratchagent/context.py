"""智能体框架的执行上下文与结果类型"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel

from .types import Event, ToolCall


@dataclass
class ExecutionContext:
    """所有运行期间执行状态的存储中心"""

    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    events: list[Event] = field(default_factory=list)
    current_step: int = 0
    state: dict[str, Any] = field(default_factory=dict)
    final_result: str | BaseModel | None = None

    # 会话管理
    session: Any | None = None
    session_manager: Any | None = None
    # 记忆管理
    memory_manager: Any | None = None

    # 代码执行环境 "Sandbox" 沙箱
    code_env: Any | None = None
    # True only when this Agent created the sandbox and owns its cleanup.
    code_env_owned: bool = False
    # Multi-Agent 中 转移模式
    transfer_to: str | None = None
    transfer_tools: dict[str, Any] = field(default_factory=dict)

    def add_event(self, event: Event) -> None:
        """追加一个event 到执行历史中"""
        self.events.append(event)

    def increment_step(self) -> None:
        """移到下一步，计数器+1"""
        self.current_step += 1


class PendingToolCall(BaseModel):
    """等待用户确认的工具调用 (human-in-the-loop)."""

    tool_call: "ToolCall"
    confirmation_message: str


@dataclass
class AgentResult:
    """智能体执行结果。"""

    output: Any  # str | BaseModel
    context: ExecutionContext
    # status: str = "complete"  # "complete" | "pending" | "error"
    status: Literal["complete", "pending", "error"]
    pending_tool_calls: list[PendingToolCall] = field(default_factory=list)


class ToolConfirmation(BaseModel):
    """用户对待处理工具调用的响应 (human-in-the-loop)."""

    tool_call_id: str
    approved: bool
    modified_arguments: dict | None = None
