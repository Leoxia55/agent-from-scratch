"""memory/_session.py 单元测试：会话抽象与内存实现。"""

from __future__ import annotations

import pytest

from scratchagent.memory import InMemorySessionManager, Session


class TestSession:
    def test_defaults(self):
        s = Session(session_id="s1")
        assert s.session_id == "s1"
        assert s.user_id is None
        assert s.events == []
        assert s.state == {}

    def test_with_user_id(self):
        s = Session(session_id="s1", user_id="u1")
        assert s.user_id == "u1"


class TestInMemorySessionManager:
    async def test_create(self):
        mgr = InMemorySessionManager()
        s = await mgr.create("s1", "u1")
        assert s.session_id == "s1"
        assert s.user_id == "u1"

    async def test_create_duplicate_raises(self):
        mgr = InMemorySessionManager()
        await mgr.create("s1")
        with pytest.raises(ValueError):
            await mgr.create("s1")

    async def test_get(self):
        mgr = InMemorySessionManager()
        await mgr.create("s1")
        s = await mgr.get("s1")
        assert s is not None
        assert s.session_id == "s1"

    async def test_get_missing(self):
        mgr = InMemorySessionManager()
        assert await mgr.get("missing") is None

    async def test_save(self):
        mgr = InMemorySessionManager()
        s = await mgr.create("s1")
        s.state["k"] = "v"
        await mgr.save(s)
        got = await mgr.get("s1")
        assert got is not None
        assert got.state["k"] == "v"

    async def test_save_updates_updated_at(self):
        mgr = InMemorySessionManager()
        s = await mgr.create("s1")
        old = s.updated_at
        await mgr.save(s)
        assert s.updated_at >= old

    async def test_get_or_create_new(self):
        mgr = InMemorySessionManager()
        s = await mgr.get_or_create("s1", "u1")
        assert s.session_id == "s1"
        assert s.user_id == "u1"

    async def test_get_or_create_existing(self):
        mgr = InMemorySessionManager()
        await mgr.create("s1", "u1")
        s = await mgr.get_or_create("s1", "u2")
        # 已存在则返回原 session，user_id 不变
        assert s.user_id == "u1"
