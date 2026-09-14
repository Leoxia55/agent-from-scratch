"""
从零开始编写的智能体框架 Agent-from-Scratch

一个简单的智能体框架，旨在帮助开发者理解智能体的工作原理，并提供一个可扩展的基础来构建自己的智能体应用。
支持工具tool 调用， 记忆、和简单的多智能体编排。
"""

# Agent
from .agent import (
    Agent,
)

# config .env
from .config import (
    load_project_env,
)

# 执行上下文
from .context import (
    AgentResult,
    ExecutionContext,
    PendingToolCall,
    ToolConfirmation,
)

# llm
from .llm import LlmClient, Provider, resolve_model_config

# Agent Orchestrator 编排
from .orchestration import (
    LoopWorkFlow,
    ParallelWorkFlow,
    SequentialWorkFlow,
    create_tasks,
    create_transfer_tool,
    reflection,
)

# RAG 增强检索
from .rag import (
    fixed_length_chunking,
    get_embeddings,
    vector_search,
)

# skill
from .skills import (
    SkillInfo,
    discover_skills,
    generate_skills_prompt,
    load_skill,
    parse_frontmatter,
)

# 核心消息类型
from .types import (
    ContentItem,
    Event,
    Message,
    SummaryMessage,
    ToolCall,
    ToolResult,
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
    "Provider",
    "resolve_model_config",
    "load_project_env",
    "SkillInfo",
    "discover_skills",
    "load_skill",
    "generate_skills_prompt",
    "parse_frontmatter",
    "get_embeddings",
    "fixed_length_chunking",
    "vector_search",
]
