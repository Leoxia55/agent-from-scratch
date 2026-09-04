"""一个轻量级的 LLM 客户端，支持多种服务商类型的 LiteLLM SDK 封装辅助工具。"""

import json
from typing import Any, Dict, List, Optional, Type, Union, cast

from litellm import acompletion
from pydantic import BaseModel, Field

from ..tools import BaseTool
from ..types import ContentItem, Message as CoreMessage, SummaryMessage, ToolCall, ToolResult
from ._config import LLMConfigError, ModelConfig, Provider, resolve_model_config


class LlmRequest(BaseModel):
    """用于调用大语言模型的请求对象。Request object for LLM calls."""

    model_config = {"arbitrary_types_allowed": True}

    instructions: List[str] = Field(default_factory=list)
    contents: List[ContentItem] = Field(default_factory=list)
    tools: List[BaseTool] = Field(default_factory=list)
    tool_choice: Optional[str] = None
    model_id: Optional[str] = None

    def append_instructions(self, text: str) -> None:
        """Append a single instruction string to the instructions list."""
        self.instructions.append(text)


class LlmResponse(BaseModel):
    """用于处理大语言模型调用响应的对象。Response object from LLM calls."""

    content: List[ContentItem] = Field(default_factory=list)
    error_message: Optional[str] = None
    usage_metadata: Dict[str, Any] = Field(default_factory=dict)


class LlmClient:
    """LiteLLM 聊天补全接口与响应接口的统一调用器。

    默认配置适用于单模型脚本。当一个进程需要调用多个服务端点时，
    更推荐使用每次调用单独指定服务商与模型参数的方式。
    """

    def __init__(self, default_config: ModelConfig | None = None) -> None:
        self.default_config = default_config

    def _resolve_call_config(
        self,
        *,
        config: ModelConfig | None,
        provider: Provider | str | None,
        model: str | None,
    ) -> ModelConfig:
        if config is not None:
            return config
        if provider is not None and model is not None:
            return resolve_model_config(provider=provider, model=model)
        if self.default_config is not None:
            return self.default_config
        raise LLMConfigError("Pass config=... or both provider=... and model=....")

    async def generate(self, request: LlmRequest) -> LlmResponse:
        """使用客户端的默认提供商配置生成响应."""
        try:
            messages = build_messages(request)
            tools = [
                tool_definition
                for tool in request.tools
                if (tool_definition := tool.tool_definition) is not None
            ] or None
            resolved = self._resolve_call_config(config=None, provider=None, model=None)
            if request.model_id is not None:
                resolved = resolve_model_config(
                    provider=resolved.provider,
                    model=request.model_id,
                )

            response = await cast(Any, acompletion)(
                model=resolved.model,
                messages=messages,
                api_key=resolved.api_key,
                api_base=resolved.api_base,
                tools=tools,
                tool_choice=request.tool_choice,
            )

            return _parse_response(response)
        except Exception as exc:
            return LlmResponse(error_message=str(exc))

    async def ask(
        self,
        prompt: str,
        response_format: Optional[Type[BaseModel]] = None,
    ) -> Union[str, BaseModel]:
        """用于一次性提示词并支持可选结构化输出的便捷方法."""
        if response_format is not None:
            schema_text = json.dumps(response_format.model_json_schema())
            instruction = (
                f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n"
                f"{schema_text}"
            )
        else:
            instruction = prompt

        request = LlmRequest(
            instructions=[instruction],
            contents=[CoreMessage(role="user", content="Please respond.")],
        )
        response = await self.generate(request)
        if response.error_message is not None:
            raise RuntimeError(f"LLM request failed: {response.error_message}")

        text = ""
        for item in response.content:
            if isinstance(item, CoreMessage):
                text = item.content
                break

        if response_format is None:
            return text

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].lstrip()
        return response_format.model_validate_json(cleaned.strip())


def build_messages(request: LlmRequest) -> List[dict[str, Any]]:
    """将大模型请求（LlmRequest）转换为接口消息格式."""
    messages: List[dict[str, Any]] = []

    for instruction in request.instructions:
        messages.append({"role": "system", "content": instruction})

    for item in request.contents:
        if isinstance(item, CoreMessage):
            messages.append({"role": item.role, "content": item.content})
        elif isinstance(item, ToolCall):
            tool_call_dict = {
                "id": item.tool_call_id,
                "type": "function",
                "function": {
                    "name": item.name,
                    "arguments": item.arguments,
                },
            }
            if messages and messages[-1]["role"] == "assistant":
                messages[-1].setdefault("tool_calls", []).append(tool_call_dict)
            else:
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call_dict],
                })
        elif isinstance(item, ToolResult):
            messages.append({
                "role": "tool",
                "tool_call_id": item.tool_call_id,
                "content": str(item.content[0]) if item.content else "",
            })
        elif isinstance(item, SummaryMessage):
            messages.append({"role": "system", "content": item.content})

    return messages


def _parse_response(response: Any) -> LlmResponse:
    """将 API 响应转换为 LlmResponse."""
    choices = getattr(response, "choices", None) or []
    if not choices:
        return LlmResponse(error_message="LLM response did not contain any choices")

    message = getattr(choices[0], "message", None)
    if message is None:
        return LlmResponse(error_message="LLM response did not contain a message")

    content_items: List[ContentItem] = []
    message_content = getattr(message, "content", None)
    if isinstance(message_content, str) and message_content:
        content_items.append(CoreMessage(role="assistant", content=message_content))

    for tool_call in getattr(message, "tool_calls", None) or []:
        function = getattr(tool_call, "function", None)
        tool_name = getattr(function, "name", None)
        tool_arguments = getattr(function, "arguments", None)
        if not isinstance(tool_name, str) or tool_arguments is None:
            continue
        content_items.append(ToolCall(
            tool_call_id=str(getattr(tool_call, "id", "")),
            name=tool_name,
            arguments=tool_arguments,
        ))

    usage = getattr(response, "usage", None)
    return LlmResponse(
        content=content_items,
        usage_metadata={
            "input_tokens": getattr(usage, "prompt_tokens", 0),
            "output_tokens": getattr(usage, "completion_tokens", 0),
        },
    )
