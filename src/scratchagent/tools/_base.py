"""这个文件定义了 `scratch_agents` 框架中最核心的**工具抽象层**：

把普通 Python 函数包装成AI Agent 可以识别、描述和调用的工具。
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Any,
    overload,
)

from ..context import ExecutionContext

if TYPE_CHECKING:
    from ..llm import LlmRequest

from ._helpers import (
    format_tool_definition,
    function_to_input_schema,
)


class BaseTool(ABC):
    """所有工具的抽象基类."""

    DEFAULT_CONFIRMATION_TEMPLATE = (
        "The Agent wants to execute '{name}' with arguments: {arguments}." "你同意吗?"
    )

    def __init__(
        self,
        name: str | None = None,
        description: str | None = None,
        tool_definition: dict[str, Any] | None = None,
        required_confirmation: bool = False,
        confirmation_message_template: str | None = None,
    ):
        self.name = name or self.__class__.__name__
        self.description = description or self.__doc__ or ""
        self._tool_definition = tool_definition
        self.required_confirmation = required_confirmation
        self.confirmation_message_template = (
            confirmation_message_template
            if confirmation_message_template
            else self.DEFAULT_CONFIRMATION_TEMPLATE
        )

    @property
    def tool_definition(self) -> dict[str, Any] | None:
        return self._tool_definition

    def get_confirmation_message(self, arguments: dict) -> str:
        return self.confirmation_message_template.format(
            name=self.name, arguments=arguments
        )

    async def process_llm_request(
        self,
        context: ExecutionContext,
        request: "LlmRequest",
    ) -> None:
        """供工具在发送大模型请求之前对其进行修改的钩子."""
        return None

    @abstractmethod
    async def execute(self, context: ExecutionContext, **kwargs) -> Any:
        pass

    async def __call__(self, context: ExecutionContext, **kwargs) -> Any:
        return await self.execute(context, **kwargs)


class FunctionTool(BaseTool):
    """将一个 Python 函数封装为基础工具"""

    def __init__(
        self,
        func: Callable[..., Any],
        name: str | None = None,
        description: str | None = None,
        tool_definition: dict[str, Any] | None = None,
        sandbox_executable: bool = False,
        required_confirmation: bool = False,
        confirmation_message_template: str = "",
    ):
        self.func = func
        self.needs_context = "context" in inspect.signature(func).parameters
        self.sandbox_executable = sandbox_executable

        if sandbox_executable and self.needs_context:
            raise ValueError(
                f"Tool '{func.__name__}' cannot be sandbox_executable "
                " because it requires 'context' parameters."
            )

        resolved_name = name or func.__name__
        resolved_desc = description or (func.__doc__ or "").strip()

        # Must set name/description before _generate_definition

        super().__init__(
            name=resolved_name,
            description=resolved_desc,
            tool_definition=tool_definition,
            required_confirmation=required_confirmation,
            confirmation_message_template=confirmation_message_template,
        )

        # Generate definition after super().__init__ so self.name is available
        if self._tool_definition is None:
            self._tool_definition = self._generate_definition()

    async def execute(self, context: ExecutionContext, **kwargs) -> Any:
        """执行被包装的函数"""
        if self.needs_context:
            result = self.func(context=context, **kwargs)
        else:
            result = self.func(**kwargs)

        # Handel both sync and async functions
        if inspect.iscoroutine(result):
            return await result
        return result

    def _generate_definition(self) -> dict[str, Any]:
        """根据函数签名生成工具定义."""
        parameters = function_to_input_schema(self.func)
        return format_tool_definition(
            self.name,
            self.description,
            parameters,
        )

    def get_source_code(self) -> str:
        """获取被封装函数的源代码"""
        if not self.sandbox_executable:
            raise ValueError(f"Tool '{self.name}' is not marked as sandbox_executable")

        source = inspect.getsource(self.func)
        lines = source.split("\n")
        filtered_lines = []
        skip_decorator = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("@tool"):
                skip_decorator = True
                if "(" not in stripped or ")" in stripped:
                    skip_decorator = False
                continue
            if skip_decorator:
                if ")" in stripped:
                    skip_decorator = False
                continue
            filtered_lines.append(line)
        return "\n".join(filtered_lines)


@overload
def tool(func: Callable[..., Any], /) -> FunctionTool: ...


@overload
def tool(
    *,
    name: str | None = None,
    description: str | None = None,
    sandbox_executable: bool = False,
    required_confirmation: bool = False,
    confirmation_message: str | None = None,
) -> Callable[[Callable[..., Any]], FunctionTool]: ...


def tool(
    func: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    sandbox_executable: bool = False,
    required_confirmation: bool = False,
    confirmation_message: str | None = None,
) -> FunctionTool | Callable[[Callable[..., Any]], FunctionTool]:
    """用于从函数创建函数工具的装饰器.

    两种使用方式:
        @tool
        def my_func(...): ...

        @tool(name="custom_name", description="Custom description")
        def my_func(...): ...
    """

    def decorator(f: Callable[..., Any]) -> FunctionTool:
        return FunctionTool(
            func=f,
            name=name,
            description=description,
            sandbox_executable=sandbox_executable,
            required_confirmation=required_confirmation,
            confirmation_message_template=confirmation_message or "",
        )

    if func is not None:
        # Called without arguments: @tool
        return decorator(func)
    # Called with arguments: @tool(name=...)
    return decorator
