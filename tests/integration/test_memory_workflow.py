"""集成测试：会话与长期记忆工作流。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from scratchagent import Agent, Message
from scratchagent.llm import LlmResponse
from scratchagent.memory import InMemorySessionManager


def _make_agent(output="ok", session_manager=None):
    client = MagicMock()
    client.generate = AsyncMock(
        return_value=LlmResponse(content=[Message(role="assistant", content=output)])
    )
    return Agent(model=client, session_manager=session_manager)


async def test_session_persistence_across_runs():
    mgr = InMemorySessionManager()
    agent = _make_agent(session_manager=mgr)

    await agent.run("remember this", session_id="s1", user_id="u1")
    session = await mgr.get("s1")
    assert session is not None
    assert session.user_id == "u1"
    # session 中应记录了 user event
    assert len(session.events) > 0


async def test_session_restore_history():
    mgr = InMemorySessionManager()
    agent = _make_agent(session_manager=mgr)

    await agent.run("first message", session_id="s1", user_id="u1")
    # 第二次 run 应恢复历史，session events 数量增加
    await agent.run("second message", session_id="s1", user_id="u1")
    session = await mgr.get("s1")
    assert session is not None
    # 两次 user 输入 + 两次 assistant 回复
    assert len(session.events) >= 4


async def test_memory_tool_injects_past_experiences():
    """MemoryTool 在 LLM 调用前注入 <PAST_EXPERIENCES>。"""
    from scratchagent.memory import TaskMemory
    from scratchagent.tools import MemoryTool

    memory = TaskMemory(
        task_summary="summary",
        approach="approach",
        final_answer="answer",
        is_correct=True,
    )

    mm = MagicMock()
    mm.search = AsyncMock(return_value=[memory])

    captured = {}

    async def fake_generate(request):
        captured["instructions"] = list(request.instructions)
        return LlmResponse(content=[Message(role="assistant", content="ok")])

    client = MagicMock()
    client.generate = AsyncMock(side_effect=fake_generate)

    agent = Agent(model=client, memory_manager=mm, tools=[MemoryTool()])
    await agent.run("a similar problem")

    # 应注入包含 <PAST_EXPERIENCES> 的 instruction
    assert any("<PAST_EXPERIENCES>" in i for i in captured["instructions"])
