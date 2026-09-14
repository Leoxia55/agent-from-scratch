"""loop-wf-agent 示例：演示多智能体循环编排（迭代执行直到质量达标）

原理
----
LoopWorkFlow 在 max_iterations 次内反复运行同一组 Agent，每轮循环后
调用 stop_condition 判断是否收敛；一旦满足即提前退出，否则继续下一轮。

本示例演示「作者起草 → 审阅者反馈 → 重写」的经典循环：作者先起草，
审阅者指出不足并给出改进建议，作者再据此重写，如此往复，直到审阅者
判定「通过 / 满意」。这与「顺序编排」的区别在于：后一轮会重新审视前
一轮的产出并驱动改进，而非一次性接力。

只有第一次迭代的第一个 Agent 接收 user_input，之后的一切都继承上下文。
stop_condition 用「审阅者输出中是否含『通过/满意』等关键词」来判断收敛，
对应「衡量输出质量（关键词是否存在）」这一典型循环场景。

关键 API
--------
  LoopWorkFlow(agents=[agent_a, agent_b, ...], stop_condition=fn, max_iterations=N)
  其中 stop_condition 签名：(result: AgentResult, iteration: int) -> bool

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/loop_wf_agent.py
"""

import asyncio
import logging

from scratchagent import Agent, LoopWorkFlow
from scratchagent.context import AgentResult
from scratchagent.llm import LlmClient, Provider, resolve_model_config

# 让 verbose 的 logger.info 真正打印出来，便于观察每轮 LLM 输出
logging.basicConfig(level=logging.INFO, format="%(message)s")

# 审阅者输出中出现这些关键词，即视为「质量达标」，停止迭代
PASS_KEYWORDS = ("通过", "满意", "合格", "无需修改", "没有问题")


def stop_when_approved(result: AgentResult, iteration: int) -> bool:
    """当审阅者判定通过（输出含关键词）时停止循环。"""
    text = result.output or ""
    reached = any(kw in text for kw in PASS_KEYWORDS)
    verdict = "通过，停止迭代" if reached else "仍需改进，继续下一轮"
    preview = text[:150].replace("\n", " ") if text else "<空输出>"
    print(f"\n[Loop] 第 {iteration} 轮审阅结束：{verdict}")
    print(f"      本轮 reviewer 输出（前150字）：{preview}")
    return reached


async def loop_wf_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.LM_STUDIO, model="qwen/qwen3.8-27b"
        )
    )

    # 作者：根据主题起草内容
    writer = Agent(
        model=openai_client,
        name="writer",
        instruction=(
            "You are a writer. 根据主题撰写一段内容。"
            "如果后面有审阅者的反馈，请根据反馈修改和完善你的上一版内容。"
        ),
    )

    # 审阅者：指出不足并给出改进建议；只有确认满意时才输出「通过」
    reviewer = Agent(
        model=openai_client,
        name="reviewer",
        instruction=(
            "You are a reviewer. 审阅作者的内容，指出不足并给出具体改进建议。"
            "只有当内容质量足够好、无需进一步修改时，才在开头明确写出「通过」；"
            "否则不要写「通过」，而是继续给出修改意见。"
        ),
    )

    workflow = LoopWorkFlow(
        agents=[writer, reviewer],
        stop_condition=stop_when_approved,
        max_iterations=5,
    )

    user_input = "请撰写一段关于「循环工作流（Loop Workflow）」的介绍。"
    result = await workflow.run(user_input, verbose=True)
    print(f"\n最终结果是：\n{result.output}")


if __name__ == "__main__":
    asyncio.run(loop_wf_agent())
