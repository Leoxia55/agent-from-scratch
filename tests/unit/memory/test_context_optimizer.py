"""memory/_context_optimizer.py 单元测试：上下文优化策略。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from scratchagent import ExecutionContext, Message, SummaryMessage, ToolCall, ToolResult
from scratchagent.llm import LlmRequest
from scratchagent.memory import (
    ContextOptimizer,
    apply_compaction,
    apply_sliding_window,
    count_tokens,
)


def _request(contents=None):
    return LlmRequest(contents=contents or [])


class TestCountTokens:
    def test_empty_request(self, monkeypatch):
        assert count_tokens(_request()) == 0

    def test_counts_content(self, monkeypatch):
        # count_tokens 内部调用 tiktoken，这里直接用真实 tiktoken（已安装）
        req = _request([Message(role="user", content="hello world")])
        n = count_tokens(req)
        assert n > 0


class TestApplySlidingWindow:
    def test_keeps_first_user(self):
        req = _request(
            [
                Message(role="user", content="first"),
                Message(role="assistant", content="a1"),
                Message(role="assistant", content="a2"),
            ]
        )
        apply_sliding_window(ExecutionContext(), req, window_size=1)
        # 首 user 保留，其后只保留最近 1 条
        contents = req.contents
        assert contents[0].role == "user"
        assert contents[0].content == "first"
        assert len(contents) == 2

    def test_no_user_message(self):
        req = _request([Message(role="assistant", content="a")])
        apply_sliding_window(ExecutionContext(), req, window_size=1)
        assert len(req.contents) == 1


class TestApplyCompaction:
    def test_create_file_compaction(self):
        req = _request(
            [
                ToolCall(
                    tool_call_id="t1",
                    name="create_file",
                    arguments={"content": "very long content"},
                )
            ]
        )
        apply_compaction(ExecutionContext(), req)
        args = req.contents[0].arguments
        assert args["content"] == "[Content saved to file]"

    def test_read_file_result_compaction(self):
        req = _request(
            [
                ToolCall(
                    tool_call_id="t1",
                    name="read_file",
                    arguments={"file_path": "/a.txt"},
                ),
                ToolResult(
                    tool_call_id="t1",
                    name="read_file",
                    status="success",
                    content=["long content"],
                ),
            ]
        )
        apply_compaction(ExecutionContext(), req)
        result = req.contents[1]
        assert isinstance(result, ToolResult)
        assert "/a.txt" in result.content[0]

    def test_untracked_tool_unchanged(self):
        req = _request(
            [
                ToolCall(
                    tool_call_id="t1", name="other", arguments={"x": "y"}
                )
            ]
        )
        apply_compaction(ExecutionContext(), req)
        assert req.contents[0].arguments == {"x": "y"}


class TestContextOptimizer:
    async def test_below_threshold_returns_none(self, monkeypatch):
        optimizer = ContextOptimizer(llm_client=MagicMock(), token_threshold=10**9)
        ctx = ExecutionContext()
        req = _request([Message(role="user", content="hi")])
        result = await optimizer(ctx, req)
        assert result is None
