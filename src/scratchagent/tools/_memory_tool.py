"""可自动注入相关过往经验的记忆工具"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from ..types import Message
from ..context import ExecutionContext
from ._base import BaseTool

if TYPE_CHECKING:
    from ..memory import TaskMemory
    from ..llm import LlmRequest


class MemoryTool(BaseTool):
    """可自动将相关历史记忆注入到大语言模型请求中的工具"""

    def __init__(self):
        super().__init__(
            name="recall_memory",
            description=(
                "Search for past problem-solving records."
                "Use this to check if similar problems were solved before."
            ),
            tool_definition=None,  # Automatic injection only
        )

    async def execute(
        self, context: ExecutionContext, query: str = "", **kwargs: Any
    ) -> str:
        """检索记忆并返回格式化后的结果."""
        if context.memory_manager is None:
            return ""
        memories = await context.memory_manager.search(query, top_k=3)
        if not memories:
            return ""
        return self._format_memories(memories)

    def _format_memories(self, memories: list[TaskMemory]) -> str:
        """格式化记忆以供展示."""
        results = []
        for i, mem in enumerate(memories, 1):
            status = "Correct" if mem.is_correct else "Incorrect"
            text = (
                f"[Record {i}]\n"
                f"- Problem: {mem.task_summary}\n"
                f"- Approach: {mem.approach}\n"
                f"- Answer: {mem.final_answer}\n"
                f"- Result: {status}"
            )
            if not mem.is_correct and mem.error_analysis:
                text += f"\n- Error analysis:{mem.error_analysis}"
            results.append(text)

        return "\n\n".join(results)

    async def process_llm_request(
        self,
        context: ExecutionContext,
        request: LlmRequest,
    ) -> None:
        """在调用大语言模型之前注入相关记忆。"""
        if context.memory_manager is None:
            return

        user_msgs = [
            c for c in request.contents if isinstance(c, Message) and c.role == "user"
        ]
        if not user_msgs:
            return
        result = await self.execute(context, user_msgs[-1].content)
        if not result:
            return

        request.append_instructions(
            "The following are records from similar problems solved in the past:\n"
            "<PAST_EXPERIENCES>\n"
            f"{result}\n"
            "</PAST_EXPERIENCES>\n"
            "Reference successful approaches and avoid approaches that led to failures."
        )
