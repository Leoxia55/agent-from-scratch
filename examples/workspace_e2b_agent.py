"""workspace-e2b-agent 示例：演示沙箱工作区文件管理

原理
----
在 E2B 沙箱中，Agent 除了执行代码，还能管理「工作区文件」：
  - upload_file_to_e2b：把本地文件上传到沙箱；
  - base_e2b_tool：在沙箱中执行 shell 命令（如 ls、cat）；
  - execute_python_in_e2b：在沙箱中读写文件。

本示例演示：让 Agent 在沙箱中创建一个文件、写入内容、再读取回显，
展示沙箱工作区的文件操作闭环。

关键 API
--------
  Agent(code_execution="e2b", ...)
  # 自动注入 base_e2b_tool / execute_python_in_e2b / upload_file_to_e2b

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/workspace_e2b_agent.py
"""

import asyncio

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config


async def workspace_e2b_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT, model="gpt-5.5"
        )
    )

    agent = Agent(
        model=openai_client,
        instruction=(
            "You are a helpful assistant with an E2B sandbox. "
            "你可以在沙箱工作区中执行 shell 命令（base_e2b_tool）和 Python 代码"
            "（execute_python_in_e2b）来创建、写入、读取文件。"
        ),
        code_execution="e2b",
    )

    user_input = (
        "请在沙箱工作区中做以下操作：\n"
        "1. 用 Python 创建一个 /home/user/report.txt 文件，写入「你好，E2B！」；\n"
        "2. 再用 shell 命令查看该文件的内容；\n"
        "3. 最后告诉我文件内容是什么。"
    )

    result = await agent.run(user_input, verbose=True)
    print(f"\n最终结果是：{result.output}")


if __name__ == "__main__":
    asyncio.run(workspace_e2b_agent())
