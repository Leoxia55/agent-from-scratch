"""顺序工作流：依次执行多个智能体"""


from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..context import ExecutionContext, AgentResult, ToolConfirmation

from ..agent import Agent

class SequentialWorkFlow(Agent):
    """按顺序运行多个智能体，将上下文从一个传递到下一个."""

    def __init__(
        self,
        agents: List[Agent],
        name: str = "sequential_workflow",
    ):
        super().__init__(model=None, name=name) # 补上初始化Agent 全部属性
        self.agents = agents
        self.name = name

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
        if context is None:
            # 初始化一个 context
            context = ExecutionContext()

        result = None
        for i, agent in enumerate(self.agents):
            if context is not None:
                context.final_result = None
                context.current_step = 0

            if i == 0:
                result = await agent.run(
                    user_input=user_input,
                    context=context,
                    verbose=verbose,
                )
            else:
                result = await agent.run(
                    context=context,
                    verbose=verbose,
                )
            context = result.context

        if result is None:
            raise ValueError("Workflow received an empty agents list.")

        return result