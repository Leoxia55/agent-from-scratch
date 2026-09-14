"""tools/_base.py 单元测试：BaseTool / FunctionTool / @tool。"""

from __future__ import annotations

import pytest

from scratchagent import ExecutionContext
from scratchagent.tools import BaseTool, FunctionTool, tool


def _sync_add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


async def _async_add(a: int, b: int) -> int:
    return a + b


def _needs_context(context: ExecutionContext, key: str) -> str:
    return str(context.state.get(key, ""))


# ---------------------------------------------------------------- BaseTool
class TestBaseTool:
    def test_abstract_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseTool()

    def test_default_name_from_class(self):
        class MyTool(BaseTool):
            async def execute(self, context, **kwargs):
                return None

        t = MyTool()
        assert t.name == "MyTool"

    def test_confirmation_message(self):
        class MyTool(BaseTool):
            async def execute(self, context, **kwargs):
                return None

        t = MyTool()
        msg = t.get_confirmation_message({"x": 1})
        assert "MyTool" in msg


# ---------------------------------------------------------------- FunctionTool
class TestFunctionTool:
    def test_wraps_sync_callable(self):
        ft = FunctionTool(_sync_add)
        assert ft.name == "_sync_add"

    async def test_execute_sync(self):
        ft = FunctionTool(_sync_add)
        ctx = ExecutionContext()
        assert await ft(ctx, a=1, b=2) == 3

    async def test_execute_async(self):
        ft = FunctionTool(_async_add)
        ctx = ExecutionContext()
        assert await ft(ctx, a=1, b=2) == 3

    def test_needs_context_detected(self):
        ft = FunctionTool(_needs_context)
        assert ft.needs_context is True

    def test_needs_context_false_for_plain(self):
        ft = FunctionTool(_sync_add)
        assert ft.needs_context is False

    async def test_execute_injects_context(self):
        ft = FunctionTool(_needs_context)
        ctx = ExecutionContext()
        ctx.state["key"] = "val"
        assert await ft(ctx, key="key") == "val"

    def test_sandbox_executable_with_context_conflict(self):
        with pytest.raises(ValueError):
            FunctionTool(_needs_context, sandbox_executable=True)

    def test_custom_name(self):
        ft = FunctionTool(_sync_add, name="add")
        assert ft.name == "add"

    def test_tool_definition_generated(self):
        ft = FunctionTool(_sync_add)
        definition = ft.tool_definition
        assert definition is not None
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "_sync_add"

    def test_get_source_code_requires_flag(self):
        ft = FunctionTool(_sync_add)
        with pytest.raises(ValueError):
            ft.get_source_code()

    def test_get_source_code(self):
        ft = FunctionTool(_sync_add, sandbox_executable=True)
        source = ft.get_source_code()
        assert "def _sync_add" in source


# ---------------------------------------------------------------- @tool 装饰器
class TestToolDecorator:
    def test_without_args(self):
        @tool
        def my_func(x: int) -> int:
            return x

        assert isinstance(my_func, FunctionTool)
        assert my_func.name == "my_func"

    def test_with_args(self):
        @tool(name="custom", description="Custom desc")
        def my_func(x: int) -> int:
            return x

        assert isinstance(my_func, FunctionTool)
        assert my_func.name == "custom"
        assert my_func.description == "Custom desc"

    async def test_decorated_tool_executes(self):
        @tool
        def my_func(x: int) -> int:
            return x * 2

        ctx = ExecutionContext()
        assert await my_func(ctx, x=21) == 42
