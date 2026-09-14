"""orchestration/_planning_reflection.py 单元测试：规划与反思工具。"""

from __future__ import annotations

from scratchagent import ExecutionContext
from scratchagent.orchestration import create_tasks, reflection
from scratchagent.orchestration._planning_reflection import Task


class TestTask:
    def test_str_pending(self):
        assert str(Task(content="a", status="pending")) == "[ ] a"

    def test_str_in_progress(self):
        assert str(Task(content="a", status="in_progress")) == "[>] **a**"

    def test_str_completed(self):
        assert str(Task(content="a", status="completed")) == "[X] ~~a~~"


class TestCreateTasks:
    async def test_with_task_objects(self):
        tasks = [
            Task(content="a", status="pending"),
            Task(content="b", status="completed"),
        ]
        plan = await create_tasks(ExecutionContext(), tasks=tasks)
        assert "[ ] a" in plan
        assert "[X] ~~b~~" in plan

    async def test_with_dicts(self):
        tasks = [{"content": "a", "status": "pending"}]
        plan = await create_tasks(ExecutionContext(), tasks=tasks)
        assert "[ ] a" in plan


class TestReflection:
    async def test_no_replan(self):
        r = await reflection(ExecutionContext(), analysis="all good")
        assert r == "Reflection recorded: all good"

    async def test_replan(self):
        r = await reflection(ExecutionContext(), analysis="need change", need_replan=True)
        assert "REPLAN NEEDED" in r
