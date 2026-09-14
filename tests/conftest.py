"""顶层测试 fixtures。

提供 mock LLM、脚本化 LLM、样本消息、执行上下文、临时技能目录等公共 fixture。
所有外部依赖（litellm / OpenAI / Tavily / ChromaDB / E2B / tiktoken）均在各自测试中
按需 mock，本文件只提供纯内存、无 IO 的基础 fixture。
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from scratchagent import Agent, ExecutionContext, Message, ToolCall
from scratchagent.llm import LlmClient, LlmResponse


@pytest.fixture
def mock_llm_client():
    """返回一个 generate() 返回 LlmResponse 的 LlmClient mock。

    默认返回一个 assistant Message。测试中可用 client.generate.return_value 覆盖。
    """
    client = MagicMock(spec=LlmClient)
    client.generate = AsyncMock(
        return_value=LlmResponse(content=[Message(role="assistant", content="ok")])
    )
    return client


@pytest.fixture
def scripted_llm():
    """返回 (add_response, build_client)。

    add_response 向脚本队列追加一个 LlmResponse；
    build_client 返回 generate 按次序返回这些响应的 mock client。
    """
    responses: list[LlmResponse] = []

    def _add(content=None, error=None):
        if content is None:
            content = [Message(role="assistant", content="")]
        responses.append(LlmResponse(content=content, error_message=error))

    def _build():
        client = MagicMock(spec=LlmClient)
        client.generate = AsyncMock(side_effect=list(responses))
        return client

    return _add, _build


@pytest.fixture
def sample_messages():
    """类型测试用的标准消息样本。"""
    return [
        Message(role="user", content="hi"),
        Message(role="assistant", content="hello"),
    ]


@pytest.fixture
def sample_tool_call():
    """工具调用测试样本。"""
    return ToolCall(tool_call_id="t1", name="calculator", arguments={"expr": "2+2"})


@pytest.fixture
def execution_context():
    """新建的执行上下文。"""
    return ExecutionContext()


@pytest.fixture
def empty_agent(mock_llm_client):
    """最小可用 Agent 实例（model 为 mock）。"""
    return Agent(model=mock_llm_client)
