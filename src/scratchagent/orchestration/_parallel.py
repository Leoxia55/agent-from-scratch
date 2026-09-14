"""并行工作流：同时执行多个智能体"""

from __future__ import annotations

import asyncio
import logging

from ..agent import Agent
from ..context import AgentResult, ExecutionContext, ToolConfirmation
from ..llm import LlmClient

logger = logging.getLogger(__name__)


class ParallelWorkFlow(Agent):
    """并行运行多个智能体，并合并结果."""

    def __init__(
        self,
        agents: list[Agent],
        synthesizer: LlmClient | None = None,
        name: str = "parallel_workflow",
    ):
        super().__init__(model=synthesizer, name=name)  # 补上初始化Agent 全部属性
        self.agents = agents
        self.synthesizer = synthesizer

    async def run(
        self,
        user_input: str | None = None,
        context: ExecutionContext | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        tool_confirmations: list[ToolConfirmation] | None = None,
        verbose: bool = False,
    ) -> AgentResult:
        """Execute all agents concurrently."""

        if not self.agents:
            raise ValueError("Workflow received an empty agents list.")

        if context is None:
            context = ExecutionContext()

        existing_event_count = len(context.events)

        results = await asyncio.gather(
            *[
                agent.run(user_input, context=context, verbose=verbose)
                for agent in self.agents
            ]
        )

        merged_context = ExecutionContext()
        for event in context.events:
            merged_context.add_event(event)

        seen_user_event = False
        for result in results:
            new_events = result.context.events[existing_event_count:]
            for event in new_events:
                if event.author == "user":
                    if not seen_user_event:
                        merged_context.add_event(event)
                        seen_user_event = True
                else:
                    merged_context.add_event(event)

        # combine outputs
        if self.synthesizer is not None:
            combined_output = await self._synthesize(results)
        else:
            combined_output = "\n\n".join(
                f"[{agent.name}]\n{result.output}"
                for agent, result in zip(self.agents, results)
            )

        return AgentResult(
            output=combined_output,
            context=merged_context,
            status="complete",
        )

    async def _synthesize(self, results: list[AgentResult]) -> str:
        """用聚合模型把多个智能体的独立输出综合成一份连贯结论。

        通过 LlmClient.ask 做一次无工具循环的汇总，消解冲突并提炼要点；
        失败时降级回纯字符串拼接，避免单点聚合故障拖垮整个工作流。
        """
        parts = "\n\n".join(
            f"【{agent.name}】\n{result.output}"
            for agent, result in zip(self.agents, results)
        )
        prompt = (
            "以下是多个智能体对同一问题的独立分析，请汇总去重、消解相互矛盾的观点，"
            "提炼成一份连贯、结构化的综合结论。若存在无法调和的分歧，请如实保留并列明。"
            "\n\n" + parts
        )
        try:
            synthesized = await self.synthesizer.ask(prompt)
            if synthesized:
                return synthesized
        except Exception as exc:
            logger.warning("Parallel synthesis failed: %s", exc)
        return "\n\n".join(
            f"[{agent.name}]\n{result.output}"
            for agent, result in zip(self.agents, results)
        )
