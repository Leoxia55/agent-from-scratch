"""核心的数据类型"""

import uuid
from typing import List, Literal, TypeAlias, Any
from datetime import datetime

from pydantic import BaseModel, Field


class Message(BaseModel):
    """在会话中的一个文本消息 Message"""
    type: Literal["message"] = "message"
    role: Literal["system", "user", "assistant"]
    content: str

class ToolCall(BaseModel):
    """LLM 请求执行一个 tool . API Role 是 assistant"""
    type: Literal["tool_call"] = "tool_call"
    tool_call_id: str
    name: str
    arguments: str | dict[str, Any]


class ToolResult(BaseModel):
    """Tool 工具执行的结果. API Role is tool"""
    type: Literal["tool_result"] = "tool_result"
    tool_call_id: str
    name: str
    status: Literal["success", "error"]
    content: list[str | dict]

class SummaryMessage(BaseModel):
    """包含执行历史摘要的持久标记."""
    type: Literal["summary"] = "summary"
    content: str

# 对四种类型信息的一个打包封装，构成一个 ContentItem，可以表示4个类型当中的任何一种
# ContentItem = Union[Message, ToolCall, ToolResult, SummaryMessage]
type ContentItem = Message | ToolCall | ToolResult | SummaryMessage

class Event(BaseModel):
    """一个Agent 智能体的执行记录."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    author: str  # "user" or agent name
    content: List[ContentItem] = Field(default_factory=list)