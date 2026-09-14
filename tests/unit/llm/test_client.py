"""llm/_client.py 单元测试：LlmClient 与消息转换。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from scratchagent import Message, SummaryMessage, ToolCall, ToolResult
from scratchagent.llm import (
    LLMConfigError,
    LlmClient,
    LlmRequest,
    LlmResponse,
    ModelConfig,
    Provider,
    build_messages,
)
from scratchagent.tools import FunctionTool


# ---------------------------------------------------------------- LlmRequest
class TestLlmRequest:
    def test_defaults(self):
        r = LlmRequest()
        assert r.instructions == []
        assert r.contents == []
        assert r.tools == []
        assert r.tool_choice is None
        assert r.model_id is None

    def test_append_instructions(self):
        r = LlmRequest()
        r.append_instructions("first")
        r.append_instructions("second")
        assert r.instructions == ["first", "second"]


# ---------------------------------------------------------------- LlmResponse
class TestLlmResponse:
    def test_defaults(self):
        r = LlmResponse()
        assert r.content == []
        assert r.error_message is None
        assert r.usage_metadata == {}

    def test_content_items(self):
        r = LlmResponse(content=[Message(role="assistant", content="hi")])
        assert len(r.content) == 1


# ---------------------------------------------------------------- LlmClient
class TestLlmClient:
    def test_init_default(self):
        c = LlmClient()
        assert c.default_config is None

    def test_init_with_config(self):
        cfg = ModelConfig(provider=Provider.LLAMA, model="m")
        c = LlmClient(default_config=cfg)
        assert c.default_config is cfg

    async def test_generate_returns_response(self, monkeypatch):
        cfg = ModelConfig(provider=Provider.LLAMA, model="m")
        client = LlmClient(default_config=cfg)

        fake_response = MagicMock()
        fake_response.choices = [MagicMock()]
        fake_response.choices[0].message.content = "hello"
        fake_response.choices[0].message.tool_calls = None
        fake_response.usage = None

        async def fake_acompletion(**kwargs):
            return fake_response

        monkeypatch.setattr("scratchagent.llm._client.acompletion", fake_acompletion)

        req = LlmRequest(contents=[Message(role="user", content="hi")])
        resp = await client.generate(req)
        assert resp.error_message is None
        assert isinstance(resp.content[0], Message)
        assert resp.content[0].content == "hello"

    async def test_generate_handles_error(self, monkeypatch):
        cfg = ModelConfig(provider=Provider.LLAMA, model="m")
        client = LlmClient(default_config=cfg)

        async def fake_acompletion(**kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr("scratchagent.llm._client.acompletion", fake_acompletion)
        resp = await client.generate(LlmRequest())
        assert resp.error_message is not None
        assert "boom" in resp.error_message

    async def test_generate_no_config_returns_error(self):
        client = LlmClient()
        resp = await client.generate(LlmRequest())
        assert resp.error_message is not None

    async def test_generate_parses_tool_call(self, monkeypatch):
        cfg = ModelConfig(provider=Provider.LLAMA, model="m")
        client = LlmClient(default_config=cfg)

        fake_message = MagicMock()
        fake_message.content = None
        fake_tc = MagicMock()
        fake_tc.id = "tc1"
        fake_tc.function.name = "calculator"
        fake_tc.function.arguments = '{"operator": "add"}'
        fake_message.tool_calls = [fake_tc]

        fake_response = MagicMock()
        fake_response.choices = [MagicMock()]
        fake_response.choices[0].message = fake_message
        fake_response.usage = None

        async def fake_acompletion(**kwargs):
            return fake_response

        monkeypatch.setattr("scratchagent.llm._client.acompletion", fake_acompletion)
        resp = await client.generate(LlmRequest())
        assert len(resp.content) == 1
        assert isinstance(resp.content[0], ToolCall)
        assert resp.content[0].tool_call_id == "tc1"
        assert resp.content[0].name == "calculator"

    async def test_ask_plain_text(self, monkeypatch):
        cfg = ModelConfig(provider=Provider.LLAMA, model="m")
        client = LlmClient(default_config=cfg)

        async def fake_generate(request):
            return LlmResponse(
                content=[Message(role="assistant", content="answer")]
            )

        monkeypatch.setattr(client, "generate", fake_generate)
        result = await client.ask("question")
        assert result == "answer"

    async def test_ask_structured(self, monkeypatch):
        class Answer(BaseModel):
            conclusion: str

        cfg = ModelConfig(provider=Provider.LLAMA, model="m")
        client = LlmClient(default_config=cfg)

        async def fake_generate(request):
            return LlmResponse(
                content=[Message(role="assistant", content='{"conclusion": "yes"}')]
            )

        monkeypatch.setattr(client, "generate", fake_generate)
        result = await client.ask("question", response_format=Answer)
        assert isinstance(result, Answer)
        assert result.conclusion == "yes"

    async def test_ask_error_raises(self, monkeypatch):
        cfg = ModelConfig(provider=Provider.LLAMA, model="m")
        client = LlmClient(default_config=cfg)

        async def fake_generate(request):
            return LlmResponse(error_message="failed")

        monkeypatch.setattr(client, "generate", fake_generate)
        with pytest.raises(RuntimeError):
            await client.ask("question")


# ---------------------------------------------------------------- build_messages
class TestBuildMessages:
    def test_instruction_to_system(self):
        req = LlmRequest(instructions=["be helpful"])
        msgs = build_messages(req)
        assert msgs == [{"role": "system", "content": "be helpful"}]

    def test_core_message(self):
        req = LlmRequest(contents=[Message(role="user", content="hi")])
        msgs = build_messages(req)
        assert msgs == [{"role": "user", "content": "hi"}]

    def test_tool_call_attached_to_assistant(self):
        req = LlmRequest(
            contents=[
                Message(role="assistant", content=""),
                ToolCall(tool_call_id="t1", name="calc", arguments='{"x":1}'),
            ]
        )
        msgs = build_messages(req)
        assert len(msgs) == 1
        assert msgs[0]["role"] == "assistant"
        assert len(msgs[0]["tool_calls"]) == 1
        assert msgs[0]["tool_calls"][0]["id"] == "t1"

    def test_tool_call_new_assistant(self):
        req = LlmRequest(
            contents=[ToolCall(tool_call_id="t1", name="calc", arguments='{"x":1}')]
        )
        msgs = build_messages(req)
        assert msgs[0]["role"] == "assistant"
        assert msgs[0]["content"] is None
        assert msgs[0]["tool_calls"][0]["function"]["name"] == "calc"

    def test_tool_result(self):
        req = LlmRequest(
            contents=[
                ToolResult(
                    tool_call_id="t1", name="calc", status="success", content=["4"]
                )
            ]
        )
        msgs = build_messages(req)
        assert msgs[0]["role"] == "tool"
        assert msgs[0]["tool_call_id"] == "t1"
        assert msgs[0]["content"] == "4"

    def test_summary_message(self):
        req = LlmRequest(contents=[SummaryMessage(content="so far...")])
        msgs = build_messages(req)
        assert msgs == [{"role": "system", "content": "so far..."}]


# ---------------------------------------------------------------- tool 过滤
class TestToolDefinitionFilter:
    async def test_none_tool_definition_excluded(self, monkeypatch):
        """tool_definition=None 的工具不应传给 litellm。"""
        cfg = ModelConfig(provider=Provider.LLAMA, model="m")
        client = LlmClient(default_config=cfg)

        captured = {}

        async def fake_acompletion(**kwargs):
            captured["tools"] = kwargs.get("tools")
            r = MagicMock()
            r.choices = [MagicMock()]
            r.choices[0].message.content = "ok"
            r.choices[0].message.tool_calls = None
            r.usage = None
            return r

        monkeypatch.setattr("scratchagent.llm._client.acompletion", fake_acompletion)

        # 构造一个 tool_definition 为 None 的 MemoryTool 实例
        from scratchagent.tools import MemoryTool

        req = LlmRequest(tools=[MemoryTool()])
        await client.generate(req)
        assert captured["tools"] is None
