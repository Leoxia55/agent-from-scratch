"""
从零开始编写的智能体框架 Agent-from-Scratch

一个简单的智能体框架，旨在帮助开发者理解智能体的工作原理，并提供一个可扩展的基础来构建自己的智能体应用。
支持工具tool 调用， 记忆、和简单的多智能体编排。
"""

# 核心消息类型
from .types import (
    Message,
    ToolCall,
    ToolResult,
    SummaryMessage,
    ContentItem,
    Event,
)

# 执行上下文
from .context import (
    ExecutionContext,
    AgentResult,
    PendingToolCall,
    ToolConfirmation,
)

# RAG 增强检索
# from ._rag import (
#     get_embeddings,
#     fixed_length_chunking,
#     vector_search,
# )

# skill
# from ._skills import (
#     SkillInfo,
#     discover_skills,
#     load_skill,
#     generate_skills_prompt,
#     parse_frontmatter,
# )
# llm
from .llm import (
    LlmClient,
)

# Agent Orchestrator 编排
from .orchestration import (
    create_tasks,
    reflection,
    create_transfer_tool,
    LoopWorkFlow,
    SequentialWorkFlow,
    ParallelWorkFlow,
)

# Agent
from .agent import (
    Agent,
)

__all__ = [
    "LlmClient",
    "Message",
    "ToolCall",
    "ToolResult",
    "SummaryMessage",
    "ContentItem",
    "Event",
    "Agent",
    "LoopWorkFlow",
    "SequentialWorkFlow",
    "ParallelWorkFlow",
    "ExecutionContext",
    "AgentResult",
    "PendingToolCall",
    "ToolConfirmation",
    "create_tasks",
    "reflection",
    "create_transfer_tool",
]
