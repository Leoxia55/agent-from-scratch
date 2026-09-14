"""e2b-agent 示例：演示在 E2B 沙箱中执行 Python 代码

原理
----
通过 Agent(code_execution="e2b") 启用代码执行沙箱。框架会在 run() 时：
  1. 自动创建 E2B 沙箱（需 E2B_API_KEY）；
  2. 注入 execute_python_in_e2b / base_e2b_tool / upload_file_to_e2b 三个工具；
  3. 运行结束后自动关闭沙箱。

LLM 在需要计算、数据处理时，可调用 execute_python_in_e2b 在隔离环境中
执行 Python 代码，避免在宿主进程直接运行任意代码。

关键 API
--------
  Agent(code_execution="e2b", ...)

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/e2b_agent.py
"""

import asyncio

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config


async def e2b_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT, model="gpt-5.5"
        )
    )

    agent = Agent(
        model=openai_client,
        instruction=(
            "You are a helpful assistant with a Python sandbox. "
            "涉及计算或数据处理时，请调用 execute_python_in_e2b 在沙箱中执行代码。"
        ),
        code_execution="e2b",
    )

    user_input = (
        "请用 Python 计算前 20 个斐波那契数的和，并列出这些数。"
    )

    result = await agent.run(user_input, verbose=True)
    print(f"\n最终结果是：{result.output}")


if __name__ == "__main__":
    asyncio.run(e2b_agent())
