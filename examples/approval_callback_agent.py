"""演示通过 approval_callback 来实现 Human-in-the-loop, 一个文件删除的确认操作

可以examples/human_in_loop_agent.py 比较理解

说明：在examples目录下要有一个 abc.txt 文件
"""

import asyncio
import sys
from pathlib import Path

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.tools import (
    calculator,
    search_web,
    delete_file,
    approval_callback,
)


PENDING_CLEANUP_FILE = Path(__file__).resolve().parents[0]/"abc.txt"

async def approval_callback_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT,
            model="gpt-5.5",
        )
    )

    user_input = f"Please delete the file at  {PENDING_CLEANUP_FILE} with delete_file tool."

    agent = Agent(
        model=openai_client,
        tools=[calculator, search_web, delete_file],
        before_tool_callbacks=[approval_callback],
        instruction="You are a helpful assistant."
    )

    result = await agent.run(user_input)
    print(f"The result is {result.output}")

if __name__ == "__main__":
    asyncio.run(approval_callback_agent())