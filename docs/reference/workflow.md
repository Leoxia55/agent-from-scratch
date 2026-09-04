# Workflow 参考

导入：`from scratchagent import SequentialWorkFlow, ParallelWorkFlow, LoopWorkFlow, create_transfer_tool`

## `SequentialWorkFlow`

`SequentialWorkFlow(agents, name="sequential_workflow")` 按列表顺序运行 Agent，共享 context；只有第一个 Agent 接收 `user_input`，后续 Agent 读取已有事件。

## `ParallelWorkFlow`

`ParallelWorkFlow(agents, name="parallel_workflow")` 使用 `asyncio.gather` 并发执行，最后合并输出为带 Agent 名称的字符串。共享 context 的写入顺序不可依赖。

## `LoopWorkFlow`

`LoopWorkFlow(agents, stop_condition=None, max_iterations=10, name="loop_workflow")` 重复运行 Agent 列表。`stop_condition(result, iteration)` 返回真值时停止；否则达到 `max_iterations` 停止。

## transfer

`create_transfer_tool(target_agents)` 返回名为 `transfer_to_agent` 的 `FunctionTool`，参数是目标 Agent 名称枚举。目标必须存在且允许转移；运行时通过 `ExecutionContext.transfer_to` 继续执行。

