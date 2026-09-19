"""借助 ChromaDB 实现长期记忆，用于任务记忆的存储与检索"""

import os
import uuid
from typing import Any, cast

import chromadb
import openai
from chromadb.api.types import QueryResult
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from pydantic import BaseModel, Field

from ..context import ExecutionContext
from ..llm import LlmClient
from ..types import (
    Event,
    Message,
    ToolCall,
    ToolResult,
)
from ..config import load_project_env


class TaskMemory(BaseModel):
    """Structured memory for GAIA problem-solving records."""

    task_summary: str = Field(description="What the problem asked")
    approach: str = Field(description="Methods and tools used to solve it")
    final_answer: str = Field(description="The agent's submitted answer")
    is_correct: bool = Field(description="Whether the answer was correct")
    error_analysis: str | None = Field(
        default=None,
        description="Why the attempt failed, if it did",
    )

    def to_embedding_text(self) -> str:
        """Generate text for vector search."""
        return f"Task: {self.task_summary}"


class DuplicateCheckResult(BaseModel):
    """Result of duplicate check."""

    decision: str = Field(description="ADD (new information) or SKIP (duplicate)")
    reason: str = Field(description="Explanation for the decision")


TASK_MEMORY_EXTRACTION_PROMPT = """Analyze the following execution history and extract a structured task memory.

Execution History:
{execution_history}

Extract:
- task_summary: What the problem asked
- approach: Methods and tools used to solve it
- final_answer: The agent's submitted answer
- is_correct: Whether the answer was correct (true or false)
- error_analysis: If incorrect, explain why; otherwise leave null
"""


DUPLICATE_CHECK_PROMPT = """Compare the new memory against existing memories to determine if it's a duplicate.

Existing memories:
{existing_memories}

New memory:
{new_memory}

Respond with one of:
- ADD: This is new information that should be stored
- SKIP: Similar information already exists, no need to store

Judgment criteria:
- Same problem with different approach or different result counts as new information
- Same problem with same approach and same result is a duplicate
"""


class TaskMemoryManager:
    """Memory manager for GAIA problem-solving learning."""

    def __init__(
        self,
        llm_client: LlmClient,
        collection_name: str = "task_memories",
    ):
        self.llm_client = llm_client

        # ChromaDB setup
        # chromadb.PersistentClient(path="./.memory_db")

        # 加载一下环境变量
        load_project_env()

        self.client = chromadb.Client()
        embedding_fn = OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            api_base=os.getenv("OPENROUTER_BASE_URL"),
            model_name=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        )
        # OpenAIEmbeddingFunction 内部创建的 openai.OpenAI 客户端 connect 超时仅 5s，
        # 访问 OpenRouter 时 TLS 握手偶发超过 5s 导致 ConnectTimeout。
        # 这里替换为带更长 timeout 的客户端，避免 embedding 请求偶发超时。
        embedding_fn.client = openai.OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENROUTER_BASE_URL"),
            timeout=60.0,
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=cast(Any, embedding_fn),
        )



    async def _extract_memory(self, execution_history: str) -> TaskMemory | None:
        """Extract structured memory from execution history."""
        prompt = TASK_MEMORY_EXTRACTION_PROMPT.format(
            execution_history=execution_history
        )
        try:
            result = await self.llm_client.ask(
                prompt=prompt,
                response_format=TaskMemory,
            )
            if not isinstance(result, TaskMemory):
                raise TypeError("Expected TaskMemory from memory extraction")
            return result
        except Exception as e:
            print(f"Memory extraction failed: {e}")
            return None

    def _format_execution_history(self, events: list[Event]) -> str:
        """Convert event list to text."""
        lines = []
        for event in events:
            for item in event.content:
                if isinstance(item, Message):
                    lines.append(f"[{item.role}]: {item.content}")
                elif isinstance(item, ToolCall):
                    lines.append(f"[Tool Call]: {item.name}({item.arguments})")
                elif isinstance(item, ToolResult):
                    content_preview = str(item.content[0])[:500] if item.content else ""
                    lines.append(f"[Tool Result]: {item.name} -> {content_preview}")
        return "\n".join(lines)

    async def _is_duplicate(
        self,
        new_memory: TaskMemory,
        existing_results: QueryResult,
    ) -> bool:
        """Determine if a new memory duplicates an existing one."""
        metadatas = existing_results["metadatas"]
        if not metadatas or not metadatas[0]:
            return False

        existing_texts = []
        for meta in metadatas[0]:
            existing_texts.append(
                f"task_summary: {meta.get('task_summary')}, "
                f"- approach: {meta.get('approach')}, "
                f"is_correct: {meta.get('is_correct')}"
            )

        prompt = DUPLICATE_CHECK_PROMPT.format(
            existing_memories="\n".join(existing_texts),
            new_memory=(
                f"task_summary: {new_memory.task_summary}, "
                f"approach: {new_memory.approach}, "
                f"is_correct: {new_memory.is_correct}"
            ),
        )

        try:
            result = await self.llm_client.ask(
                prompt=prompt,
                response_format=DuplicateCheckResult,
            )
            if not isinstance(result, DuplicateCheckResult):
                raise TypeError("Expected DuplicateCheckResult from duplicate check")
            return result.decision == "SKIP"
        except Exception:
            return False

    async def save(self, context: ExecutionContext) -> str | None:
        """Extract and save memory from execution context.

        Returns:
            memory_id if saved, None if ignored as duplicate
        """
        # 1. Convert execution history to text
        execution_history = self._format_execution_history(context.events)

        # 2. Extract structured memory using LLM
        memory = await self._extract_memory(execution_history)
        if memory is None:
            return None

        # 3. Duplicate check using the same text used for storage
        try:
            existing = self.collection.query(
                query_texts=[memory.to_embedding_text()],
                n_results=3,
            )
        except Exception as e:
            # embedding 调用偶发网络超时，优雅降级：跳过重复检查，直接尝试入库
            print(f"Memory duplicate check failed (skipping): {e}")
            existing = cast(QueryResult, {"metadatas": [[], []]}) #降级处理
        if await self._is_duplicate(memory, existing):
            return None

        # 4. Store in ChromaDB
        memory_id = str(uuid.uuid4())
        metadata = memory.model_dump()
        # ChromaDB metadata cannot store None values
        metadata = {k: ("" if v is None else v) for k, v in metadata.items()}
        try:
            self.collection.add(
                ids=[memory_id],
                documents=[memory.to_embedding_text()],
                metadatas=[metadata],
            )
        except Exception as e:
            # 入库时 embedding 调用失败，优雅降级：放弃本次保存
            print(f"Failed to store memory: {e}")
            return None
        return memory_id

    async def search(self, query: str, top_k: int = 5) -> list[TaskMemory]:
        """Search for memories related to the query."""
        # 空库直接返回，避免无意义的 embedding 调用（embedding 需联网，网络不稳时易超时）
        try:
            if self.collection.count() == 0:
                return []
        except Exception:
            pass

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
            )
        except Exception as e:
            # embedding 调用偶发网络超时，优雅降级：视为无匹配记忆，不中断主流程
            print(f"Memory search failed (falling back to no memory): {e}")
            return []

        metadatas = results["metadatas"]
        if not metadatas or not metadatas[0]:
            return []

        return [TaskMemory.model_validate(meta) for meta in metadatas[0]]
