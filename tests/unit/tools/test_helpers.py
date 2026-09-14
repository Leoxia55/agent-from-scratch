"""tools/_helpers.py 单元测试：函数签名到 JSON Schema 的转换。"""

from __future__ import annotations

from pydantic import BaseModel

from scratchagent.tools import (
    format_tool_definition,
    function_to_input_schema,
    function_to_tool_definition,
)


def _fn_types(
    a: str, b: int, c: float, d: bool, e: list[str], opt: int = 0
) -> None:
    """Docstring."""


class _Model(BaseModel):
    name: str


def _fn_model(m: _Model) -> None:
    """Takes a model."""


def _fn_context(self, context, x: str) -> None:
    """Has self and context."""


class TestFunctionToInputSchema:
    def test_primitive_types(self):
        schema = function_to_input_schema(_fn_types)
        props = schema["properties"]
        assert props["a"]["type"] == "string"
        assert props["b"]["type"] == "integer"
        assert props["c"]["type"] == "number"
        assert props["d"]["type"] == "boolean"
        assert props["e"]["type"] == "array"
        assert props["e"]["items"]["type"] == "string"

    def test_required_fields(self):
        schema = function_to_input_schema(_fn_types)
        assert "a" in schema["required"]
        assert "b" in schema["required"]
        assert "opt" not in schema["required"]

    def test_pydantic_model(self):
        schema = function_to_input_schema(_fn_model)
        props = schema["properties"]
        # pydantic 模型参数会被展开为 model_json_schema，嵌套在参数名 key 下
        assert "name" in props["m"]["properties"]

    def test_skips_self_and_context(self):
        schema = function_to_input_schema(_fn_context)
        assert "self" not in schema["properties"]
        assert "context" not in schema["properties"]
        assert "x" in schema["properties"]


class TestFormatToolDefinition:
    def test_structure(self):
        d = format_tool_definition("add", "Add numbers", {"type": "object"})
        assert d["type"] == "function"
        assert d["function"]["name"] == "add"
        assert d["function"]["description"] == "Add numbers"
        assert d["function"]["parameters"] == {"type": "object"}


class TestFunctionToToolDefinition:
    def test_structure(self):
        d = function_to_tool_definition(_fn_types)
        assert d["function"]["name"] == "_fn_types"
        assert d["function"]["parameters"]["type"] == "object"
