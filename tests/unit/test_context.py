"""context.py 单元测试：执行上下文与结果类型。"""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from scratchagent import Event, Message, ToolCall
from scratchagent.context import (
    AgentResult,
    ExecutionContext,
    PendingToolCall,
    ToolConfirmation,
)


# ---------------------------------------------------------------- ExecutionContext
class TestExecutionContext:
    def test_default_init(self):
        ctx = ExecutionContext()
        assert isinstance(ctx.execution_id, str)
        assert ctx.current_step == 0
        assert ctx.events == []
        assert ctx.state == {}
        assert ctx.final_result is None

    def test_execution_id_is_uuid(self):
        ctx = ExecutionContext()
        uuid.UUID(ctx.execution_id)  # 不抛错即合法 uuid

    def test_add_event(self):
        ctx = ExecutionContext()
        e1 = Event(execution_id=ctx.execution_id, author="user", content=[])
        e2 = Event(execution_id=ctx.execution_id, author="assistant", content=[])
        ctx.add_event(e1)
        ctx.add_event(e2)
        assert ctx.events == [e1, e2]

    def test_increment_step(self):
        ctx = ExecutionContext()
        ctx.increment_step()
        ctx.increment_step()
        assert ctx.current_step == 2

    def test_field_defaults_none(self):
        ctx = ExecutionContext()
        assert ctx.session is None
        assert ctx.session_manager is None
        assert ctx.memory_manager is None
        assert ctx.code_env is None
        assert ctx.code_env_owned is False
        assert ctx.transfer_to is None
        assert ctx.transfer_tools == {}

    def test_state_is_mutable_dict(self):
        ctx = ExecutionContext()
        ctx.state["key"] = "value"
        assert ctx.state["key"] == "value"


# ---------------------------------------------------------------- AgentResult
class TestAgentResult:
    def test_status_literal_valid(self):
        for status in ("complete", "pending", "error"):
            ctx = ExecutionContext()
            r = AgentResult(output=None, context=ctx, status=status)
            assert r.status == status

    def test_status_type_annotation_is_literal(self):
        """status 类型标注应为 Literal["complete","pending","error"]（运行时 dataclass 不校验）。"""
        from typing import get_type_hints

        hints = get_type_hints(AgentResult)
        assert "complete" in hints["status"].__args__  # type: ignore[union-attr]
        assert "pending" in hints["status"].__args__  # type: ignore[union-attr]
        assert "error" in hints["status"].__args__  # type: ignore[union-attr]

    def test_output_any(self):
        ctx = ExecutionContext()
        r = AgentResult(output="result", context=ctx, status="complete")
        assert r.output == "result"

    def test_pending_tool_calls_default_empty(self):
        ctx = ExecutionContext()
        r = AgentResult(output=None, context=ctx, status="complete")
        assert r.pending_tool_calls == []

    def test_pending_tool_calls(self):
        ctx = ExecutionContext()
        tc = ToolCall(tool_call_id="t1", name="calc", arguments={})
        p = PendingToolCall(tool_call=tc, confirmation_message="confirm?")
        r = AgentResult(
            output=None, context=ctx, status="pending", pending_tool_calls=[p]
        )
        assert len(r.pending_tool_calls) == 1


# ---------------------------------------------------------------- PendingToolCall
class TestPendingToolCall:
    def test_fields(self):
        tc = ToolCall(tool_call_id="t1", name="calc", arguments={})
        p = PendingToolCall(tool_call=tc, confirmation_message="confirm?")
        assert p.tool_call == tc
        assert p.confirmation_message == "confirm?"


# ---------------------------------------------------------------- ToolConfirmation
class TestToolConfirmation:
    def test_fields(self):
        c = ToolConfirmation(tool_call_id="t1", approved=True)
        assert c.tool_call_id == "t1"
        assert c.approved is True
        assert c.modified_arguments is None

    def test_modified_arguments(self):
        c = ToolConfirmation(
            tool_call_id="t1", approved=True, modified_arguments={"x": 1}
        )
        assert c.modified_arguments == {"x": 1}
