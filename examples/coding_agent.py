"""coding-agent 示例：演示结构化输出

原理
----
通过 Agent 的 output_type 参数（一个 Pydantic BaseModel 子类），框架会：
  1. 自动生成一个 final_answer 工具，其入参 schema 即该模型；
  2. 强制 LLM 以该结构返回结果（tool_choice="required"）；
  3. 解析为对应的 Pydantic 实例，作为 result.output 返回。

本示例让 Agent 对一段代码做审查，并返回结构化的审查报告。

关键 API
--------
  Agent(output_type=SomeBaseModel, ...)
  # result.output 为 SomeBaseModel 实例

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/coding_agent.py
"""

import asyncio

from pydantic import BaseModel, Field

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config


class CodeReview(BaseModel):
    """代码审查结果的结构化输出。"""

    summary: str = Field(description="一段话概述代码整体情况")
    score: int = Field(description="代码质量评分，0-100 分")
    issues: list[str] = Field(description="发现的问题列表")
    suggestions: list[str] = Field(description="改进建议列表")


async def coding_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT, model="gpt-5.5"
        )
    )

    agent = Agent(
        model=openai_client,
        instruction="You are a senior code reviewer. 审查代码并输出结构化报告。",
        output_type=CodeReview,
    )

    code_snippet = '''
def calc_total(items):
    total = 0
    for i in items:
        total = total + i
    return total
'''

    user_input = f"请审查下面这段 Python 代码：\n```python\n{code_snippet}\n```"

    result = await agent.run(user_input)

    # result.output 是 CodeReview 实例
    print(f"\n最终结果是（结构化）：")
    print(f"  - 总结：{result.output.summary}")
    print(f"  - 评分：{result.output.score}")
    print(f"  - 问题：{result.output.issues}")
    print(f"  - 建议：{result.output.suggestions}")


if __name__ == "__main__":
    asyncio.run(coding_agent())
