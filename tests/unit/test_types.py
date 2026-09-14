"""types.py 单元测试：内部消息与事件协议。"""

from __future__ import annotations

import typing

import pytest
from pydantic import ValidationError

from scratchagent import (
    ContentItem,
    Event,
    Message,
    SummaryMessage,
    ToolCall,
    ToolResult,
)


# ---------------------------------------------------------------- Message
class TestMessage:
    def test_default_type(self):
        m = Message(role="user", content="hi")
        assert m.type == "message"

    def test_role_literal_valid(self):
        for role in ("system", "user", "assistant"):
            m = Message(role=role, content="x")
            assert m.role == role

    def test_role_invalid_raises(self):
        with pytest.raises(ValidationError):
            Message(role="tool", content="x")

    def test_content_required(self):
        with pytest.raises(ValidationError):
            Message(role="user")

    def test_json_round_trip(self):
        m = Message(role="assistant", content="hi there")
        assert Message.model_validate(m.model_dump()) == m


# ---------------------------------------------------------------- ToolCall
class TestToolCall:
    def test_default_type(self):
        tc = ToolCall(tool_call_id="t1", name="calc", arguments={})
        assert tc.type == "tool_call"

    def test_required_fields(self):
        with pytest.raises(ValidationError):
            ToolCall(name="calc", arguments={})
        with pytest.raises(ValidationError):
            ToolCall(tool_call_id="t1", arguments={})

    def test_arguments_accepts_str(self):
        tc = ToolCall(tool_call_id="t1", name="calc", arguments='{"x": 1}')
        assert tc.arguments == '{"x": 1}'

    def test_arguments_accepts_dict(self):
        tc = ToolCall(tool_call_id="t1", name="calc", arguments={"x": 1})
        assert tc.arguments == {"x": 1}


# ---------------------------------------------------------------- ToolResult
class TestToolResult:
    def test_default_type(self):
        tr = ToolResult(tool_call_id="t1", name="calc", status="success", content=[])
        assert tr.type == "tool_result"

    def test_status_literal(self):
        with pytest.raises(ValidationError):
            ToolResult(tool_call_id="t1", name="calc", status="pending", content=[])

    def test_status_valid(self):
        for status in ("success", "error"):
            tr = ToolResult(tool_call_id="t1", name="calc", status=status, content=[])
            assert tr.status == status

    def test_content_required(self):
        with pytest.raises(ValidationError):
            ToolResult(tool_call_id="t1", name="calc", status="success")

    def test_content_nested_types(self):
        tr = ToolResult(
            tool_call_id="t1",
            name="calc",
            status="success",
            content=["a", ["b", "c"], [{"k": "v"}]],
        )
        assert len(tr.content) == 3


# ---------------------------------------------------------------- SummaryMessage
class TestSummaryMessage:
    def test_default_type(self):
        s = SummaryMessage(content="summary")
        assert s.type == "summary"

    def test_content_only(self):
        s = SummaryMessage(content="summary")
        # SummaryMessage 只有 type 与 content 字段
        assert s.model_dump() == {"type": "summary", "content": "summary"}


# ---------------------------------------------------------------- ContentItem
class TestContentItem:
    def test_is_type_alias(self):
        # PEP-695 `type` 语句产生 typing.TypeAliasType
        assert isinstance(ContentItem, typing.TypeAliasType)

    def test_not_instantiable(self):
        with pytest.raises(TypeError):
            ContentItem()  # type: ignore[call-arg, misc]


# ---------------------------------------------------------------- Event
class TestEvent:
    def test_default_id_is_uuid(self):
        e = Event(execution_id="e1", author="user", content=[])
        assert isinstance(e.id, str)
        assert len(e.id) > 0

    def test_timestamp_is_float(self):
        e = Event(execution_id="e1", author="user", content=[])
        assert isinstance(e.timestamp, float)

    def test_content_sequence_order(self):
        items = [
            Message(role="user", content="a"),
            Message(role="assistant", content="b"),
        ]
        e = Event(execution_id="e1", author="user", content=items)
        assert e.content == items

    def test_content_default_empty(self):
        e = Event(execution_id="e1", author="user")
        assert e.content == []

    def test_execution_id_required(self):
        with pytest.raises(ValidationError):
            Event(author="user")

    def test_author_required(self):
        with pytest.raises(ValidationError):
            Event(execution_id="e1")
