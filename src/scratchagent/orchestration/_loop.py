"""Loop 循环工作流，重复直到满足停止条件"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Callable

from ..context import ExecutionContext, AgentResult, ToolConfirmation


from ..agent import Agent

StopCondition = Callable[[AgentResult, int], bool]

class LoopWorkFlow(Agent):
    """Run agents in a loop until loop condition is met."""

    def __init__(
        self,
        agents: List[Agent],
        stop_condition: StopCondition | None = None,
        max_iterations: int = 10,
        name: str = "loop_workflow",
    ):
        super().__init__(model=None, name=name) # 补上初始化Agent 全部属性
        self.agents = agents
        self.stop_condition = stop_condition
        self.max_iterations = max_iterations
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

        if context is None:
            context = ExecutionContext()

        result: AgentResult | None = None
        is_first_agent = True

        for iteration in range(1, self.max_iterations + 1):
            for agent in self.agents:
                context.final_result = None
                context.current_step = 0
                if is_first_agent:
                    result = await agent.run(          # ← 会话参数只在首个代理处生效
                        user_input=user_input,
                        context=context,
                        session_id=session_id,
                        user_id=user_id,
                        tool_confirmations=tool_confirmations,
                        verbose=verbose,
                    )
                    is_first_agent = False
                else:
                    result = await agent.run(context=context, verbose=verbose)
                context = result.context

            if result and self.stop_condition and self.stop_condition(result, iteration):
                break

        if result is None:
            raise ValueError("Workflow received an empty agents list.")  # 见下文附带 bug
        return result