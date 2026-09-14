"""planning-reflection-agent 示例：演示规划与反思

原理
----
为 Agent 注入两个特殊工具，引导它先规划、执行中反思：
  - create_tasks：创建/更新任务清单（pending / in_progress / completed）；
  - reflection：暂停并分析进展，可标记 need_replan=True 请求重新规划。

这两个工具本身不产生业务结果，而是通过打印任务清单、记录反思，
让 Agent 在多步复杂任务中保持结构化和可追踪。

本示例额外做两件事，让演示更直观：
  1. 关掉 verbose，改用 after_tool_callbacks 自定义打印——
     search_web 结果只显示前 150 字，reflection 完整显示；
  2. 强化 instruction，要求完成调研后必须直接输出结论文本，
     并明确禁止在任务清单全部完成后继续调用 create_tasks / reflection，
     避免模型「反思上瘾」或「任务清单上瘾」导致永远不产出纯文本、
     最终返回 None。

关键 API
--------
  from scratchagent.orchestration import create_tasks, reflection
  Agent(after_tool_callbacks=[...])

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/planning_reflection_agent.py
"""

import asyncio

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.orchestration import create_tasks, reflection
from scratchagent.tools import FunctionTool, search_web
from scratchagent.types import ToolResult


def _log_tool_result(context, tool_result: ToolResult) -> None:
    """自定义工具结果打印：search_web 截断，reflection 完整显示。

    create_tasks 内部已自行 print 任务清单，这里不重复打印，避免刷屏。
    """
    name = tool_result.name
    if name == "create_tasks":
        return  # 任务清单已由 create_tasks 内部打印

    if name == "reflection":
        # 反思内容完整展示，直观看到 Agent 在反思
        text = str(tool_result.content[0]) if tool_result.content else ""
        print(f"\n[反思] {text}\n", flush=True)
        return

    # 其他工具（如 search_web）：截取前 150 字，其余省略
    raw = tool_result.content[0] if tool_result.content else ""
    text = str(raw)
    if len(text) > 150:
        text = text[:150] + " ……（已截断）"
    print(f"\n[工具结果 {name}] {text}\n", flush=True)


async def planning_reflection_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT, model="gpt-5.5"
        )
    )

    agent = Agent(
        model=openai_client,
        tools=[FunctionTool(search_web), create_tasks, reflection],
        instruction=(
            "You are a research assistant. "
            "对于复杂问题，先用 create_tasks 制定计划，再逐步执行，"
            "并在关键节点用 reflection 反思进度。"
            "重要：当所有调研步骤完成后，你必须立即直接输出最终的纯文本结论，"
            "以「结论：」开头。此时绝对禁止再调用任何工具——包括 create_tasks"
            "和 reflection。不要用 create_tasks 去刷新已全部完成的任务清单，"
            "任务清单一旦全部标记完成，就立刻停止调用工具并输出结论。"
        ),
        after_tool_callbacks=[_log_tool_result],
        max_steps=12,
    )

    user_input = (
        "帮我调研并对比「新能源汽车」和「传统燃油车」在当前国内市场环境下的"
        "优劣势，最终给出一个简洁的结论。"
    )

    result = await agent.run(user_input, verbose=False)
    print(f"\n最终结果是：{result.output}")


if __name__ == "__main__":
    asyncio.run(planning_reflection_agent())
