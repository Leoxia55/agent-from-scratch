# 多智能体路由

ScratchAgent 的路由有两层：显式工作流和 Agent transfer。

| 机制 | 上下文 | 结束方式 | 适用场景 |
| --- | --- | --- | --- |
| Sequential | 同一 context，串行 | 最后 Agent 的结果 | 分阶段流水线 |
| Parallel | 共享 context，并发 | 合并各 Agent 输出 | 独立视角分析 |
| Loop | 同一 context，重复迭代 | stop condition 或上限 | 评审、改写 |
| transfer | 父 Agent 把 context 交给目标 | 目标 Agent 继续 loop | 动态专家路由 |

`create_transfer_tool` 生成一个枚举目标名称的工具。调用成功后写入 `context.transfer_to`；Agent 查找目标并递归运行。设置 `disallow_transfer_to_peers=True` 可禁用同级转移。路由器的工具描述应列出目标能力，否则模型无法做出稳定选择。

并行共享可变 context 有竞态风险；需要隔离时为每个 Agent 建立独立 context，最后显式合并结果。

