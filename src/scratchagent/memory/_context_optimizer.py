"""上下文优化策略：滑动窗口、压缩、摘要。"""

from __future__ import annotations

import inspect
import json
from typing import TYPE_CHECKING, Any

from ..context import ExecutionContext
from ..llm import LlmRequest, build_messages
from ..types import ContentItem, Message, SummaryMessage, ToolCall, ToolResult

if TYPE_CHECKING:
    from ..llm import LlmClient, LlmResponse


def create_optimizer_callback(apply_optimization, threshold: int = 50000):
    """Factory function that creates a callback applying optimization strategy"""

    async def callback(
        context: ExecutionContext,
        request: LlmRequest,
    ) -> LlmResponse | None:
        token_count = count_tokens(request)

        if token_count < threshold:
            return None

        # Support both sync and async functions
        result = apply_optimization(context, request)
        if inspect.isawaitable(result):
            await result
        return None

    return callback


def count_tokens(request: LlmRequest) -> int:
    """Calculate total token count of LlmRequest."""
    import tiktoken

    try:
        # 模糊匹配 就 用 gpt-5 的token 字典
        encoding = tiktoken.encoding_for_model("gpt-5")
    except KeyError:
        encoding = tiktoken.get_encoding("o200k_base")
    # 调用 llm 中的工具build_messages 来得到llm 原始的消息内容
    messages = build_messages(request)
    total_tokens = 0

    for message in messages:
        total_tokens += 4  # per-message overhead

        if message.get("content"):
            total_tokens += len(encoding.encode(str(message["content"])))

        if message.get("tool_calls"):
            for tool_call in message["tool_calls"]:
                func = tool_call.get("function", {})
                if func.get("name"):
                    total_tokens += len(encoding.encode(func["name"]))
                if func.get("arguments"):
                    total_tokens += len(encoding.encode(func["arguments"]))
    # 计算工具的定义 token
    if request.tools:
        for tool in request.tools:
            tool_def = tool.tool_definition
            if tool_def:
                total_tokens += len(encoding.encode(json.dumps(tool_def)))

    return total_tokens


def apply_sliding_window(
    context: ExecutionContext,
    request: LlmRequest,
    window_size: int = 20,
) -> None:
    """Sliding window that keeps only the most recent N messages."""
    contents = request.contents

    # Find user message position
    user_message_idx: int | None = None
    for i, item in enumerate(contents):
        if isinstance(item, Message) and item.role == "user":
            user_message_idx = i
            break

    if user_message_idx is None:
        return

    # Preserve up to user message . 保留第⼀个⽤⼾消息之前的内容，以及⽤⼾消息本⾝
    preserved = contents[: user_message_idx + 1]

    # Keep only the most recent N from remaining items
    remaining = contents[user_message_idx + 1 :]
    if len(remaining) > window_size:
        remaining = remaining[-window_size:]

    request.contents = preserved + remaining


# 用于压缩工具调用参数的工具
TOOLCALL_COMPACTION_RULES: dict[str, str] = {
    "create_file": "[Content saved to file]",
}

# 用于压缩工具返回结果内容的工具
TOOLRESULT_COMPACTION_RULES: dict[str, str] = {
    "read_file": "File content from {file_path}. Re-read if needed.",
    "search_web": "Search results processed. Query: {query}. Re-search if needed.",
    "tavily_search": "Search results processed. Query: {query}. Re-search if needed.",
}


def apply_compaction(context: ExecutionContext, request: LlmRequest) -> None:
    """Compress tool calls and results into reference messages."""
    tool_call_args: dict[str, dict[str, Any]] = {}
    compacted: list[ContentItem] = []

    for item in request.contents:
        if isinstance(item, ToolCall):
            arguments = item.arguments
            if not isinstance(arguments, dict):
                compacted.append(item)
                continue

            tool_call_args[item.tool_call_id] = arguments

            if item.name in TOOLCALL_COMPACTION_RULES:

                # for key, value in item.arguments.items():
                #     if key == "content":
                #         compressed_args[key] = "[Content saved to file]"
                #     else:
                #         compressed_args[key] = value
                # 以下是简单写法
                compressed_args = {
                    k: TOOLCALL_COMPACTION_RULES[item.name] if k == "content" else v
                    for k, v in arguments.items()
                }
                compacted.append(
                    ToolCall(
                        tool_call_id=item.tool_call_id,
                        name=item.name,
                        arguments=compressed_args,
                    )
                )
            else:
                compacted.append(item)

        elif isinstance(item, ToolResult):
            if item.name in TOOLRESULT_COMPACTION_RULES:
                args = tool_call_args.get(item.tool_call_id, {})
                template = TOOLRESULT_COMPACTION_RULES[item.name]
                compressed_content = template.format(
                    # 优先取 file_path, 如果没有取 path ,再没有则 unknown
                    file_path=args.get("file_path", args.get("path", "unknown")),
                    query=args.get("query", "unknown"),
                )
                compacted.append(
                    ToolResult(
                        tool_call_id=item.tool_call_id,
                        name=item.name,
                        status=item.status,
                        content=[compressed_content],
                    )
                )
            else:
                compacted.append(item)
        else:
            compacted.append(item)
    # 替换原有的内容
    request.contents = compacted


SUMMARIZATION_PROMPT = """You are summarizing an AI agent's work progress.

Given the following execution history, extract:
1. Key findings: Important information discovered
2. Tools used: List of tools that were called
3. Current status: What has been accomplished and what remains

Be concise. Focus on information that will help the agent continue its work.

Execution History:
{history}

Provide a structured summary."""


async def apply_summarization(
    context: ExecutionContext,
    request: "LlmRequest",
    llm_client: LlmClient,
    keep_recent: int = 5,
) -> None:
    """Replace old messages with one durable summary marker."""
    contents = request.contents

    # Find the first user message and the latest summary marker.
    # 这是一种生成器表达式写法，等价于
    # user_idx = None

    # for i, item in enumerate(contents):
    #     if isinstance(item, Message) and item.role == "user":
    #         user_idx = i
    #         break

    user_idx: int | None = next(
        (
            i
            for i, item in enumerate(contents)
            if isinstance(item, Message) and item.role == "user"
        ),
        None,
    )
    if user_idx is None:
        return

    summary_idx: int | None = next(
        (
            i
            for i in range(len(contents) - 1, -1, -1)
            if isinstance(contents[i], SummaryMessage)
        ),
        None,
    )
    summary_start = (summary_idx + 1) if summary_idx is not None else user_idx + 1
    summary_end = len(contents) - keep_recent

    if summary_end <= summary_start:
        return

    to_summarize = contents[summary_start:summary_end]
    if not to_summarize:
        return

    # Include the previous summary so each replacement remains complete.
    history_parts: list[str] = []
    if summary_idx is not None:
        previous_summary = contents[summary_idx]
        if isinstance(previous_summary, SummaryMessage):
            history_parts.append(f"[Previous summary]\n{previous_summary.content}")
    history_parts.append(format_history_for_summary(to_summarize))

    summary = await generate_summary(llm_client, "\n\n".join(history_parts))
    if not summary:
        return

    summary_item = SummaryMessage(content=summary)
    summary_prefix_end = summary_idx if summary_idx is not None else summary_start
    preserved_prefix = contents[:summary_prefix_end]
    preserved_end = contents[summary_end:]
    request.contents = preserved_prefix + [summary_item] + preserved_end


def format_history_for_summary(items: list[ContentItem]) -> str:
    """Convert ContentItem list to text for summarization."""
    lines: list[str] = []
    for item in items:
        if isinstance(item, Message):
            lines.append(f"[{item.role}]: {item.content[:500]}...")
        elif isinstance(item, ToolCall):
            lines.append(f"[Tool Call]: {item.name}({item.arguments})")
        elif isinstance(item, ToolResult):
            content_preview = str(item.content[0])[:200] if item.content else ""
            lines.append(f"[Tool Result]: {item.name} -> {content_preview}...")
    return "\n".join(lines)


async def generate_summary(llm_client: LlmClient, history: str) -> str:
    """Generate history summary using LLM."""

    request = LlmRequest(
        instructions=[SUMMARIZATION_PROMPT.format(history=history)],
        contents=[Message(role="user", content="Please summarize.")],
    )

    response = await llm_client.generate(request)

    for item in response.content:
        if isinstance(item, Message):
            return item.content

    return ""


class ContextOptimizer:
    """Hierarchical context optimization strategies for managing execution context in AI agents."""

    def __init__(
        self,
        llm_client: LlmClient,
        token_threshold: int = 50000,
        enable_compaction: bool = True,
        enable_summarization: bool = True,
        keep_recent_steps: int = 5,
    ):
        self.llm_client = llm_client
        self.token_threshold = token_threshold
        self.enable_compaction = enable_compaction
        self.enable_summarization = enable_summarization
        self.keep_recent_steps = keep_recent_steps

    async def __call__(
        self,
        context: ExecutionContext,
        request: LlmRequest,
    ) -> LlmResponse | None:
        """Register as before_llm_callback."""
        if count_tokens(request) < self.token_threshold:
            return None  # No optimization needed

        if self.enable_compaction:
            apply_compaction(context, request)
            if count_tokens(request) < self.token_threshold:
                return None  # Compaction was sufficient

        if self.enable_summarization:
            await apply_summarization(
                context, request, self.llm_client, self.keep_recent_steps
            )

        return None
