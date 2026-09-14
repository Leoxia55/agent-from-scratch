"""顺序工作流：依次执行多个智能体"""

from __future__ import annotations

from ..agent import Agent
from ..context import AgentResult, ExecutionContext, ToolConfirmation


class SequentialWorkFlow(Agent):
    """按顺序运行多个智能体，将上下文从一个传递到下一个."""

    def __init__(
        self,
        agents: list[Agent],
        name: str = "sequential_workflow",
    ):
        super().__init__(model=None, name=name)  # 补上初始化Agent 全部属性
        self.agents = agents

    async def run(
        self,
        user_input: str | None = None,
        context: ExecutionContext | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        tool_confirmations: list[ToolConfirmation] | None = None,
        verbose: bool = False,
    ) -> AgentResult:
        """Execute all agents in sequence"""
        if not self.agents:
            raise ValueError("Workflow received an empty agents list.")

        if context is None:
            # 初始化一个 context
            context = ExecutionContext()

        result: AgentResult | None = None
        for i, agent in enumerate(self.agents):
            context.final_result = None
            context.current_step = 0

            if i == 0:
                result = await agent.run(
                    user_input=user_input,
                    context=context,
                    session_id=session_id,
                    user_id=user_id,
                    tool_confirmations=tool_confirmations,
                    verbose=verbose,
                )
            else:
                result = await agent.run(
                    context=context,
                    verbose=verbose,
                )
            context = result.context

        assert result is not None
        return result
