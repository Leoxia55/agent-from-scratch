"""human-in-loop-agent 示例：演示危险工具的人工确认

原理
----
对于删除、发送、写入外部系统等高风险工具，通过 FunctionTool 的
required_confirmation=True 标记。当 LLM 请求执行该工具时：
  1. 第一次 run() 不会真正执行，而是返回 status="pending"，
     并携带 pending_tool_calls（含 confirmation_message）；
  2. 应用层向用户展示确认消息，收集用户的批准/拒绝；
  3. 用 ToolConfirmation 再次调用 run() 继续执行。

关键 API
--------
  FunctionTool(func, required_confirmation=True, confirmation_message_template=...)
  ToolConfirmation(tool_call_id=..., approved=True/False, modified_arguments=...)

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/human_in_loop_agent.py
"""

import asyncio

from scratchagent import Agent, ToolConfirmation
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.tools import FunctionTool


def send_email(recipient: str, subject: str, body: str) -> str:
    """向指定收件人发送一封邮件。"""
    return f"邮件已发送至 {recipient}，主题：{subject}"


async def human_in_loop_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT, model="gpt-5.5"
        )
    )

    # 标记为需要人工确认的工具
    # 注意：description 只描述工具「做什么」，不要写「需人工确认」这类话——
    # 否则会暗示模型「这个动作敏感，先反问用户」，反而导致模型不调用工具，
    # 绕过框架的 required_confirmation 机制。
    email_tool = FunctionTool(
        func=send_email,
        name="send_email",
        description="向指定收件人发送一封邮件。",
        required_confirmation=True,
        confirmation_message_template=(
            "Agent 希望执行「{name}」，参数：{arguments}。是否批准？"
        ),
    )

    agent = Agent(
        model=openai_client,
        tools=[email_tool],
        instruction=(
            "You are a helpful assistant. "
            "当用户要求发送邮件时，你必须直接调用 send_email 工具，"
            "不要用文字反问或请求确认，把确认的职责交给系统处理。"
        ),
    )

    user_input = "请帮我给 youliangxia0505@google.com 发一封邮件，主题是「项目进度同步」，正文是「明天下午三点开会」。"

    # 第一次 run：触发工具调用，但被挂起等待确认
    result = await agent.run(user_input)

    if result.status == "pending":
        print("\n⚠️  检测到需要人工确认的工具调用：")
        for pending in result.pending_tool_calls:
            print(f"   - {pending.confirmation_message}")
            print(f"   - tool_call_id: {pending.tool_call.tool_call_id}")

        # 交互式人工决策：等待用户真实输入批准/拒绝
        response = input(
            "\n是否批准执行该工具？输入 y 批准，输入其他任意键拒绝："
        ).strip().lower()
        approved = response == "y"
        pending_id = result.pending_tool_calls[0].tool_call.tool_call_id

        print(f"\n[人工决策] {'批准' if approved else '拒绝'}本次调用")

        result = await agent.run(
            context=result.context,
            tool_confirmations=[
                ToolConfirmation(tool_call_id=pending_id, approved=approved)
            ],
        )
    else:
        print("（本次未触发需要确认的工具）")

    print(f"\n最终结果是：{result.output}")


if __name__ == "__main__":
    asyncio.run(human_in_loop_agent())
