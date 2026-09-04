# 05. 多智能体

ScratchAgent 提供顺序、并行、循环三种工作流，也可以让 Agent 在运行中 transfer 到同级 Agent。

## 1. 顺序工作流

```python
from scratchagent import Agent, SequentialWorkFlow

researcher = Agent(model=client, name="researcher", instruction="先收集事实。")
writer = Agent(model=client, name="writer", instruction="根据上下文写出结论。")
workflow = SequentialWorkFlow([researcher, writer])
result = await workflow.run("比较两种缓存策略。")
print(result.output)
```

顺序工作流共享一个 `ExecutionContext`，后续 Agent 只能看到前一个 Agent 已记录的事件。

## 2. 并行和循环

```python
from scratchagent import LoopWorkFlow, ParallelWorkFlow

parallel = ParallelWorkFlow([researcher, writer])
parallel_result = await parallel.run("分别分析性能和可维护性。")

loop = LoopWorkFlow(
    [researcher, writer],
    max_iterations=3,
    stop_condition=lambda result, iteration: "完成" in str(result.output),
)
loop_result = await loop.run("反复改进这份方案。")
```

并行工作流会对同一个上下文并发写入，只有在工具和 callback 没有共享可变状态时才适用。循环工作流每轮重置 `final_result` 和 `current_step`，由 stop condition 或 `max_iterations` 结束。

## 3. Agent transfer

```python
from scratchagent import create_transfer_tool

transfer = create_transfer_tool([researcher, writer])
router = Agent(
    model=client,
    name="router",
    tools=[transfer],
    sub_agents=[researcher, writer],
)
result = await router.run("需要先做研究，再写结论。")
```

transfer 工具只接受目标 Agent 名称；Agent 会在上下文中设置 `transfer_to`，父 Agent 随后把同一上下文交给目标。`disallow_transfer_to_peers=True` 可关闭同级 transfer。
